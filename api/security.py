import time
import logging
import json
import os
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
logger = logging.getLogger("omniarch.security")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        json.dumps({
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "logger": "%(name)s",
            "message": "%(message)s"
        })
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter supporting per-IP and per-route limits."""
    
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        # key -> list of timestamps
        self.requests: Dict[str, list] = {}
        # Specialized route limits (endpoint -> (max_requests, window_seconds))
        self.route_limits: Dict[str, Tuple[int, int]] = {
            "/api/analyze": (10, 60),        # 10 analyses per minute
            "/api/analyze-stream": (10, 60), # 10 stream analyses per minute
            "/api/scaffold": (15, 60),       # 15 code scaffoldings per minute
            "/api/sync-miro": (20, 60),      # 20 miro syncs per minute
            "/api/oauth/callback": (10, 60), # 10 oauth callbacks per minute
        }

    def check_rate_limit(self, key: str, path: str) -> Tuple[bool, int, int, int]:
        """
        Returns (is_allowed, limit, remaining, reset_seconds).
        """
        now = time.time()
        limit, window = self.route_limits.get(path, (self.default_limit, self.window_seconds))
        
        lookup_key = f"{key}:{path}"
        timestamps = self.requests.get(lookup_key, [])
        
        # Prune timestamps older than window
        cutoff = now - window
        timestamps = [ts for ts in timestamps if ts > cutoff]
        
        if len(timestamps) >= limit:
            oldest = timestamps[0]
            reset_seconds = max(1, int(oldest + window - now))
            self.requests[lookup_key] = timestamps
            return False, limit, 0, reset_seconds

        timestamps.append(now)
        self.requests[lookup_key] = timestamps
        remaining = max(0, limit - len(timestamps))
        reset_seconds = window
        return True, limit, remaining, reset_seconds


rate_limiter = SlidingWindowRateLimiter()

class SecurityAndTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Production-grade middleware providing:
    1. HTTPS & Security Headers (Strict-Transport-Security, CSP frame-ancestors for Miro)
    2. Sliding window Rate Limiting with standard RFC headers
    3. Structured Request/Response Telemetry & Latency Logging
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path
        
        # Check rate limit on API endpoints (bypass for health and static assets)
        if path.startswith("/api/") and not path.endswith(("/health", "/healthz")):
            allowed, limit, remaining, reset_sec = rate_limiter.check_rate_limit(client_ip, path)
            if not allowed:
                logger.warning(f"Rate limit exceeded: IP={client_ip} path={path} limit={limit}")
                response = Response(
                    content=json.dumps({
                        "detail": "Rate limit exceeded. Please wait before making more requests.",
                        "limit": limit,
                        "retry_after_seconds": reset_sec
                    }),
                    status_code=429,
                    media_type="application/json"
                )
                response.headers["Retry-After"] = str(reset_sec)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(reset_sec)
                return response
        else:
            limit, remaining, reset_sec = 60, 60, 60

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Unhandled Exception: path={path} error={str(exc)} duration_ms={duration_ms}")
            raise exc

        duration_ms = int((time.time() - start_time) * 1000)

        # Append Rate Limit Headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_sec)

        # Enterprise Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Miro Iframe Embedding Support via Content-Security-Policy (Allow Miro Canvas embedding while preventing external clickjacking)
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://*.miro.com https://miro.com;"
        
        # Enforce Strict-Transport-Security in non-local environments
        if os.getenv("ENVIRONMENT") == "production" or not request.url.hostname in ("localhost", "127.0.0.1"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Log request telemetry for monitoring
        if not path.startswith("/assets"):
            logger.info(f"{request.method} {path} - status={response.status_code} ip={client_ip} duration_ms={duration_ms}")

        return response
