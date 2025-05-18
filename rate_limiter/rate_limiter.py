from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Callable, Optional

# Initialize the limiter with default settings
limiter = Limiter(key_func=get_remote_address)

def setup_limiter(app):
    """Set up the rate limiter for the FastAPI application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def rate_limit(
    limit: str,
    key_func: Optional[Callable] = None,
    error_message: Optional[str] = None
):
    """
    Rate limit decorator that can be applied to any endpoint
    
    Args:
        limit (str): Rate limit string (e.g., "5/minute", "100/hour", "1000/day")
        key_func (Callable, optional): Function to generate the rate limit key. Defaults to IP address
        error_message (str, optional): Custom error message when limit is exceeded
    """
    if key_func is None:
        key_func = get_remote_address
        
    return limiter.limit(
        limit,
        key_func=key_func,
        error_message=error_message or "Rate limit exceeded"
    )

async def custom_key_func(request: Request) -> str:
    """Custom key function that combines IP and API key for rate limiting"""
    api_key = request.headers.get("X-API-Key", "")
    ip = get_remote_address(request)
    return f"{ip}:{api_key}"

# Predefined rate limit decorators for common use cases
def standard_rate_limit():
    """Standard rate limit: 60 requests per minute"""
    return rate_limit("1000/minute")

def strict_rate_limit():
    """Strict rate limit: 30 requests per minute"""
    return rate_limit("100/minute")

def api_rate_limit():
    """API rate limit: 100 requests per minute, using API key in the limit key"""
    return rate_limit("500/minute", key_func=custom_key_func)
