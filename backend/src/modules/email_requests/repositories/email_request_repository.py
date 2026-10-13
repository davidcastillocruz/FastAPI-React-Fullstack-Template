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


# Newest first, id breaks ties so the pages never repeat or skip a row
async def get_email_requests(db: AsyncSession, offset: int, limit: int) -> list[EmailRequestModel]:
    result = await db.scalars(
        select(EmailRequestModel)
        .order_by(EmailRequestModel.created_at.desc(), EmailRequestModel.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result)
