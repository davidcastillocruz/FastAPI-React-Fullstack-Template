import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.api.dependencies import get_client_ip
from src.api.routers.email_requests_router import router as email_requests_router
from src.core import request_context
from src.core.settings import settings
from src.core.errors import error_response, setup_error_handlers, setup_openapi
from src.core.languages import setup_language_system
from src.core.limiter import limiter
from src.core.logger import setup_logging
from src.database import engine

# Registers every model before the first query, so relationships between models always resolve
import src.models  # noqa: F401

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    setup_language_system()
    yield
    # --- Shutdown ---
    # Closes the connections of the database pool
    await engine.dispose()


show_docs = settings.APP_MODE != "production"

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None,
    openapi_url="/openapi" if show_docs else None
)

app.state.limiter = limiter
setup_error_handlers(app)
setup_openapi(app)

app.include_router(email_requests_router)


# Gives every request an id and logs it: method, path, status and duration
# The id and the client IP go in every log line written while the request is handled
# (see core/request_context.py), and the client gets the id in the X-Request-ID header
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    request_id = uuid.uuid4().hex[:8]
    request_context.request_id.set(request_id)
    request_context.client_ip.set(get_client_ip(request))
    extra = {}

    try:
        response = await call_next(request)
    except Exception:
        extra["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
        logger.exception("%s %s 500", request.method, request.url.path, extra=extra)
        response = error_response(request, "INTERNAL_SERVER_ERROR", 500)
        response.headers["X-Request-ID"] = request_id
        return response

    extra["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
    message = "%s %s %d"
    args = (request.method, request.url.path, response.status_code)

    if response.status_code >= 500:
        logger.error(message, *args, extra=extra)
    elif response.status_code >= 400:
        logger.warning(message, *args, extra=extra)
    else:
        logger.info(message, *args, extra=extra)

    response.headers["X-Request-ID"] = request_id
    return response