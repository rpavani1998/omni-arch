import logging
import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure structured JSON logging
logger = logging.getLogger("omniarch.security")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    from pythonjsonlogger import jsonlogger
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        timestamp=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Rate limiter with per-route limits
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

ROUTE_LIMITS = {
    "/api/analyze": "10/minute",
    "/api/analyze-stream": "10/minute",
    "/api/scaffold": "15/minute",
    "/api/sync-miro": "20/minute",
    "/api/oauth/callback": "10/minute",
}


class SecurityAndTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Production-grade middleware providing:
    1. HTTPS & Security Headers (Strict-Transport-Security, CSP frame-ancestors for Miro)
    2. Rate Limiting via slowapi (handled at route level)
    3. Structured Request/Response Telemetry & Latency Logging
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = __import__("time").time()
        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((__import__("time").time() - start_time) * 1000)
            logger.error(f"Unhandled Exception: path={path} error={str(exc)} duration_ms={duration_ms}")
            raise exc

        duration_ms = int((__import__("time").time() - start_time) * 1000)

        # Enterprise Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Miro Iframe Embedding Support via Content-Security-Policy
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://*.miro.com https://miro.com;"

        # Enforce Strict-Transport-Security in non-local environments
        if os.getenv("ENVIRONMENT") == "production" or request.url.hostname not in ("localhost", "127.0.0.1"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Log request telemetry for monitoring
        if not path.startswith("/assets"):
            logger.info(f"{request.method} {path} - status={response.status_code} ip={client_ip} duration_ms={duration_ms}")

        return response


def get_rate_limit_for_path(path: str) -> str:
    """Returns the rate limit string for a given path."""
    return ROUTE_LIMITS.get(path, "60/minute")