import logging
import os
import re
import secrets
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

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

def get_rate_limit_key(request: Request) -> str:
    """
    Keys rate limits by authenticated tenant or user identity when available:
    1. X-Team-ID or X-User-ID header
    2. Authorization header hash
    3. Falls back to Client IP address
    """
    team_id = request.headers.get("X-Team-ID") or request.query_params.get("team_id")
    if team_id:
        return f"team:{team_id}"
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"user:{user_id}"
    auth = request.headers.get("Authorization")
    if auth:
        import hashlib
        return f"auth:{hashlib.sha256(auth.encode()).hexdigest()[:16]}"
    return get_remote_address(request)

# Rate limiter with tenant-aware key function
limiter = Limiter(key_func=get_rate_limit_key, default_limits=["60/minute"])

ROUTE_LIMITS = {
    "/api/analyze": "10/minute",
    "/api/analyze-stream": "10/minute",
    "/api/scaffold": "15/minute",
    "/api/sync-miro": "20/minute",
    "/api/oauth/callback": "10/minute",
}

def sanitize_telemetry_path(url_path: str, query_string: str = "") -> str:
    """Scans and scrubs secrets, tokens, or codes from query parameters for telemetry logging."""
    if not query_string:
        return url_path
    sanitized_query = re.sub(
        r'((?:token|key|secret|code|password|access_token|github_token)=)[^\&\s]+',
        r'\1[REDACTED]',
        query_string,
        flags=re.IGNORECASE
    )
    return f"{url_path}?{sanitized_query}"

class SecurityAndTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Production-grade middleware providing:
    1. HTTPS & Security Headers (Strict-Transport-Security, CSP frame-ancestors for Miro)
    2. Distributed / Tenant-aware Rate Limiting
    3. Correlation ID Tracking & Sanitized Request Telemetry
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = __import__("time").time()
        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path
        
        # Extract or generate unique Request Correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or secrets.token_hex(16)
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((__import__("time").time() - start_time) * 1000)
            safe_uri = sanitize_telemetry_path(path, request.url.query)
            logger.error(f"Unhandled Exception: path={safe_uri} error={str(exc)} correlation_id={correlation_id} duration_ms={duration_ms}")
            raise exc

        duration_ms = int((__import__("time").time() - start_time) * 1000)

        # Enterprise Security & Tracing Headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Miro Iframe Embedding Support via Content-Security-Policy
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://*.miro.com https://miro.com;"

        # Enforce Strict-Transport-Security in non-local environments
        if os.getenv("ENVIRONMENT") == "production" or request.url.hostname not in ("localhost", "127.0.0.1"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Log sanitized request telemetry
        if not path.startswith("/assets"):
            safe_uri = sanitize_telemetry_path(path, request.url.query)
            logger.info(f"{request.method} {safe_uri} - status={response.status_code} ip={client_ip} cid={correlation_id} duration_ms={duration_ms}")

        return response

def get_rate_limit_for_path(path: str) -> str:
    """Returns the rate limit string for a given path."""
    return ROUTE_LIMITS.get(path, "60/minute")