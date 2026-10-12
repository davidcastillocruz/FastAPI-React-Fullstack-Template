from fastapi import Request

from src.core import settings


# Client IP for logging and rate limiting
def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# It extracts the user language from the fastapi request obj
# Priority: ?lang= > "language" cookie > Accept-Language header > MAIN_LANGUAGE
def get_language(request: Request, lang: str | None = None) -> str:
    supported = settings.AVAILABLE_LANGUAGES
    tags = []

    # 1. Query param: ?lang=es
    if lang:
        tags.append(lang.lower())

    # 2. Cookie saved when the user picked a language
    cookie_lang = request.cookies.get("language")
    if cookie_lang:
        tags.append(cookie_lang.lower())

    # 3. Accept-Language: "es-ES,es;q=0.9,en;q=0.8" -> ["es-es", "es", "en"]
    candidates = []
    for part in request.headers.get("accept-language", "").split(","):
        tag, _, q = part.strip().lower().partition(";q=")
        try:
            quality = float(q) if q else 1.0
        except ValueError:
            continue
        if tag and tag != "*" and quality > 0:
            candidates.append((quality, tag))

    # Highest quality first, ties keep the browser's order (sorted is stable)
    tags.extend(tag for _, tag in sorted(candidates, key=lambda c: -c[0]))

    # First supported tag wins, trying the base language too ("es-es" -> "es")
    for tag in tags:
        for option in (tag, tag.split("-")[0]):
            if option in supported:
                return option

    # 4. Fallback
    return settings.MAIN_LANGUAGE
