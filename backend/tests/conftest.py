import os

# Before importing the app: the tests use their own database and keep the rate limit counters in memory
os.environ["POSTGRES_DB"] = "app_test"
os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.languages import setup_language_system
from src.core.limiter import limiter
from src.core.settings import settings
from src.database import Base, engine
from src.main import app
from src.modules.email_requests.services import email_request_service


# Creates the test database once, with the tables of the models (alembic is not needed here)
@pytest.fixture(scope="session", autouse=True)
async def database():
    admin_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": settings.POSTGRES_DB}
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{settings.POSTGRES_DB}"'))
    await admin.dispose()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    # The lifespan doesn't run with the test client, the languages are loaded here
    setup_language_system()
    yield
    await engine.dispose()


# Every test starts with empty tables and fresh rate limit counters
@pytest.fixture(autouse=True)
async def clean_state():
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    limiter.reset()


# Emails are recorded instead of sent: (subject, recipients, body)
@pytest.fixture(autouse=True)
def sent_emails(monkeypatch) -> list[tuple]:
    sent = []

    async def fake_send_email(subject: str, recipients: list[str], body: str) -> None:
        sent.append((subject, recipients, body))

    monkeypatch.setattr(email_request_service, "send_email", fake_send_email)
    return sent


# Calls the app directly, without a server
@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
