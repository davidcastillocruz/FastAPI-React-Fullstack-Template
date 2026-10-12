from fastapi import FastAPI

from src.core.logger import setup_logging
from src.core import settings
from src.core.limiter import limiter

# Logging init
setup_logging()

# API docs only outside production
show_docs = settings.APP_MODE != "production"

# App definition
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None,
    openapi_url="/openapi" if show_docs else None
)

# Rate limiting setup
app.state.limiter = limiter
