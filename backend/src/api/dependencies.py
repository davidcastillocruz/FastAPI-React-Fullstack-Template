from fastapi import Request

# Client IP for logging and rate limiting
def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
