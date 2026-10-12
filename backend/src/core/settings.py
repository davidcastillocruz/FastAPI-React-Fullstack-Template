import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

# backend/ folder: backend/src/core/settings.py -> parents[2]
BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"

load_dotenv(BASE_DIR / ".env.api")
load_dotenv(BASE_DIR / ".env.db")

# App info
APP_TITLE: str = os.getenv("APP_TITLE", "FastAPI-React-Template")
APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "A fullstack development template")
# The version goes with the code, not with each server's env file
APP_VERSION = "1.0.0"

# Deploy
APP_MODE: str = os.getenv("APP_MODE", "development").strip().lower()
# A typo must not start the app as development (public docs, debug logs, mail without TLS)
if APP_MODE not in ("development", "production"):
    raise ValueError(f"APP_MODE must be 'development' or 'production' (got '{APP_MODE}')")

# Backend
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1234")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app")
DATABASE_HOST: str = os.getenv("DATABASE_HOST", "db")
DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
# quote: a password with characters like "/" or "@" doesn't break the URL
DATABASE_URL: str = (
    f"postgresql+asyncpg://{quote(POSTGRES_USER, safe='')}:{quote(POSTGRES_PASSWORD, safe='')}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{POSTGRES_DB}"
)
DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
LOG_LEVEL: str = "INFO" if APP_MODE == "production" else "DEBUG"
MAIN_LANGUAGE: str = os.getenv("MAIN_LANGUAGE", "en").strip().lower()
AVAILABLE_LANGUAGES: list[str] = [
    code.strip().lower() for code in os.getenv("AVAILABLE_LANGUAGES", "en,es").split(",") if code.strip()
]
if MAIN_LANGUAGE not in AVAILABLE_LANGUAGES:
    raise ValueError(f"MAIN_LANGUAGE '{MAIN_LANGUAGE}' must be in AVAILABLE_LANGUAGES")
# Where the rate limiter keeps its counters: redis:// shares them between all the workers,
# memory:// keeps one counter per worker
RATE_LIMIT_STORAGE_URI: str = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

# Mail
MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "fastapi@react.dev")
MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "password")
MAIL_FROM: str = os.getenv("MAIL_FROM", "fastapi@react.dev")
MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465"))
MAIL_START_TLS: bool = os.getenv("MAIL_START_TLS", "false").strip().lower() == "true"
MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "true").strip().lower() == "true"
# STARTTLS (port 587) and SSL/TLS (port 465) can't be used at the same time
if MAIL_START_TLS and MAIL_SSL_TLS:
    raise ValueError("MAIL_START_TLS and MAIL_SSL_TLS can't both be true")
# Both false means no encryption: only allowed outside production (e.g. Mailpit)
if APP_MODE == "production" and not (MAIL_START_TLS or MAIL_SSL_TLS):
    raise ValueError("In production, MAIL_START_TLS or MAIL_SSL_TLS must be true")
