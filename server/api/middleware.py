"""Rate limiting and middleware configuration for CivicPulse."""

from slowapi import Limiter
from starlette.requests import Request

from server.config import settings


def safe_get_ip(request: Request) -> str:
    """Safely obtain client IP address without DNS lookups."""
    if request.client and request.client.host:
        return request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return "127.0.0.1"


# Global rate limiter keyed by client IP
limiter = Limiter(
    key_func=safe_get_ip,
    default_limits=[settings.RATE_LIMIT]
)
