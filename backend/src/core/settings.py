from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self
from urllib.parse import quote

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/ folder: backend/src/core/settings.py -> parents[2]
BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"


# Every field is read from the environment variable with its name, converted to its type and validated:
# a wrong value stops the app on startup with a clear error
class Settings(BaseSettings):
    # In Docker the variables come from env_file; outside it, from these files.
    # A variable of the environment wins over the files, and variables without a field are ignored
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env.api", BASE_DIR / ".env.db"),
        extra="ignore",
    )

    # App info
    APP_TITLE: str = "FastAPI-React-Template"
    APP_DESCRIPTION: str = "A fullstack development template"
    # ClassVar: not read from the environment, the version goes with the code
    APP_VERSION: ClassVar[str] = "1.0.0"

    # Deploy: any other value stops the app, a typo must not start it as development
    # (public docs, debug logs, mail without TLS)
    APP_MODE: Literal["development", "production"] = "development"

    # Database: POSTGRES_* come from .env.db, the same file the db container uses
    # to create the user and the database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "1234"
    POSTGRES_DB: str = "app"
    DATABASE_HOST: str = "db"
    DATABASE_PORT: int = 5432
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Languages, AVAILABLE_LANGUAGES is written "en,es"
    # (NoDecode: read as plain text, not as a JSON list)
    MAIN_LANGUAGE: str = "en"
    AVAILABLE_LANGUAGES: Annotated[list[str], NoDecode] = ["en", "es"]

    # Where the rate limiter keeps its counters: redis:// shares them between all the workers,
    # memory:// keeps one counter per worker
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    # Mail, the booleans accept true/false, 1/0, yes/no...
    MAIL_USERNAME: str = "fastapi@react.dev"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM: str = "fastapi@react.dev"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 465
    MAIL_START_TLS: bool = False
    MAIL_SSL_TLS: bool = True

    # "Production " or "ES" are accepted as "production" and "es"
    @field_validator("APP_MODE", "MAIN_LANGUAGE", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip().lower()

    # "en, ES," -> ["en", "es"]
    @field_validator("AVAILABLE_LANGUAGES", mode="before")
    @classmethod
    def split_languages(cls, value: str | list[str]) -> list[str]:
        codes = value.split(",") if isinstance(value, str) else value
        return [code.strip().lower() for code in codes if code.strip()]

    # Checks that need several fields, after each one is valid
    @model_validator(mode="after")
    def check_combinations(self) -> Self:
        if self.MAIN_LANGUAGE not in self.AVAILABLE_LANGUAGES:
            raise ValueError(f"MAIN_LANGUAGE '{self.MAIN_LANGUAGE}' must be in AVAILABLE_LANGUAGES")
        # STARTTLS (port 587) and SSL/TLS (port 465) can't be used at the same time
        if self.MAIL_START_TLS and self.MAIL_SSL_TLS:
            raise ValueError("MAIL_START_TLS and MAIL_SSL_TLS can't both be true")
        # Both false means no encryption: only allowed outside production (e.g. Mailpit)
        if self.APP_MODE == "production" and not (self.MAIL_START_TLS or self.MAIL_SSL_TLS):
            raise ValueError("In production, MAIL_START_TLS or MAIL_SSL_TLS must be true")
        return self

    # quote: a password with characters like "/" or "@" doesn't break the URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{quote(self.POSTGRES_USER, safe='')}:{quote(self.POSTGRES_PASSWORD, safe='')}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def LOG_LEVEL(self) -> str:
        return "INFO" if self.APP_MODE == "production" else "DEBUG"


# The settings of the app: from src.core.settings import settings
settings = Settings()
