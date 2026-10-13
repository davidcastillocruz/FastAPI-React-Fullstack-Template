import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors

from src.core.settings import settings

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=settings.MAIL_START_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS
)


# Runs as a background task, after the response: errors are logged, not raised (nobody would catch them)
async def send_email(subject: str, recipients: list[str], body: str) -> None:
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.html
        )
        await FastMail(conf).send_message(message)

    except ConnectionErrors as exc:
        # SMTP server unreachable, wrong credentials, TLS/port mismatch...
        logger.error(
            "Could not connect to the mail server: %s",
            exc,
            extra={"server": settings.MAIL_SERVER, "port": settings.MAIL_PORT, "subject": subject}
        )
        return

    except Exception:
        logger.exception("Failed to send email", extra={"recipients": recipients, "subject": subject})
        return

    logger.info("Email sent", extra={"recipients": recipients, "subject": subject})
