from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.languages import get_error_detail
from src.api.dependencies import get_language

# Every error answers {"detail": "..."} translated to the user's language,
# the same shape FastAPI uses for its own errors

# Errors that Starlette raises by itself, with its default English text
ROUTING_ERRORS = {
    404: "NOT_FOUND",  # the route doesn't exist
    405: "METHOD_NOT_ALLOWED",  # the route exists but not with that method
}


# Translated {"detail": ...} error response
def error_response(
    request: Request, name: str, status_code: int, args: dict[str, tuple] | None = None
) -> JSONResponse:
    language = get_language(request, request.query_params.get("lang"))
    return JSONResponse(
        {"detail": get_error_detail(name=name, language=language, args=args)},
        status_code=status_code
    )


# Replaces slowapi's default handler, which answers {"error": ...} in English
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return error_response(request, "TOO_MANY_REQUESTS", 429)


# Replaces pydantic's English list of errors with one translated string
# loc is like ("body", "email") or ("query", "page"), the field is the last name in it
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for error in exc.errors():
        names = [part for part in error["loc"] if isinstance(part, str)]
        field = names[-1] if names else "body"
        if field not in fields:
            fields.append(field)
    return error_response(request, "VALIDATION_ERROR", 422, args={"detail": (", ".join(fields),)})


# Translates the routing errors above,
# any other HTTPException (like the ones raised by the services) keeps FastAPI's default handling
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    name = ROUTING_ERRORS.get(exc.status_code)
    # Only Starlette's own text ("Not Found"...), a custom 404 of ours keeps its message
    if name and exc.detail == HTTPStatus(exc.status_code).phrase:
        response = error_response(request, name, exc.status_code)
        # The 405 must keep the "Allow" header with the valid methods
        response.headers.update(exc.headers or {})
        return response
    return await http_exception_handler(request, exc)


# It registers the error handlers in the app
# Unhandled errors (500) are handled in the log_requests middleware of main.py
def setup_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
