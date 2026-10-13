import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.api.dependencies import get_client_ip
from src.core import settings
from src.core.errors import error_response, setup_error_handlers
from src.core.languages import setup_language_system
from src.core.limiter import limiter
from src.core.logger import setup_logging
from src.database import engine

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    extra = {"ip": get_client_ip(request)}

    try:
        response = await call_next(request)
    except Exception:
        extra["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
        logger.exception("%s %s 500", request.method, request.url.path, extra=extra)
        return error_response(request, "INTERNAL_SERVER_ERROR", 500)

    extra["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
    message = "%s %s %d"
    args = (request.method, request.url.path, response.status_code)

    if response.status_code >= 500:
        logger.error(message, *args, extra=extra)
    elif response.status_code >= 400:
        logger.warning(message, *args, extra=extra)
    else:
        logger.info(message, *args, extra=extra)

    return response