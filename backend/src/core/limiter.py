from slowapi import Limiter

from src.core.settings import settings
from src.api.dependencies import get_client_ip

# Rate limiter, its counters are stored in RATE_LIMIT_STORAGE_URI (Redis in Docker)
# If Redis is down it keeps working with counters in memory until Redis is back
limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    in_memory_fallback_enabled=True
)
