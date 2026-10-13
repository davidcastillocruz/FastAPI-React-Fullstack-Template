from fastapi import APIRouter, BackgroundTasks, Request, status

from src.api.dependencies import Language
from src.core.limiter import limiter
from src.database import DbSession
from src.modules.email_requests.schemas.email_request_schemas import EmailRequestCreate
from src.modules.email_requests.services import email_request_service as service
from src.shared.schemas import MessageResponse

router = APIRouter(prefix="/email-requests", tags=["Email requests"])


# The limiter needs the request parameter: it reads the client IP from it
@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_email_request(
    request: Request,
    body: EmailRequestCreate,
    db: DbSession,
    language: Language,
    background_tasks: BackgroundTasks
) -> MessageResponse:
    return await service.create_email_request(db, body.email, language, background_tasks)
