from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.email_requests.models.email_request_model import EmailRequestModel

# No rollback here: on any error the request ends and closing the session (get_db) rolls it back


async def get_email_request_by_email(db: AsyncSession, email: str) -> EmailRequestModel | None:
    return await db.scalar(select(EmailRequestModel).where(EmailRequestModel.email == email))


async def create_email_request(db: AsyncSession, email: str) -> EmailRequestModel:
    email_request = EmailRequestModel(email=email)
    db.add(email_request)
    await db.commit()
    return email_request
