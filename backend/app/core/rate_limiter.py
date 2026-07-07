"""
Task 2.09 — Rate Limiting per-Tenant con Redis Sliding Window

Sliding window algorithm su Redis. Ogni tenant ha il suo limite.
Superato → TENANT_103 con header Retry-After.
"""

from __future__ import annotations

import os
import time
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.context import get_tenant_id
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

# Default: 1000 requests per minute per tenant
_DEFAULT_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_TENANT", "1000"))
_WINDOW_SIZE_SECONDS = 60


class RateLimiter:
    """Rate limiter per-tenant con Redis sliding window.

    In dev senza Redis: rate limiting disabilitato con warning.
    """

    def __init__(self) -> None:
        self._redis: Any = None
        self._enabled = False

    async def initialize(self) -> None:
        """Inizializza connessione Redis."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning(
                "rate_limiter_disabled",
                message="REDIS_URL non configurato, rate limiting disabilitato",
            )
            return

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._redis.ping()
            self._enabled = True
            logger.info("rate_limiter_initialized", redis_url=redis_url.split("@")[-1])
        except Exception as exc:
            logger.warning(
                "rate_limiter_redis_failed",
                error=str(exc),
                message="Rate limiting disabilitato",
                exc_info=True
            )

    async def check_rate_limit(
        self,
        tenant_id: str,
        limit: int = _DEFAULT_RATE_LIMIT,
    ) -> tuple[bool, int, int]:
        """Verifica rate limit per un tenant.

        Returns:
            (allowed, remaining, retry_after_seconds)
        """
        if not self._enabled or not self._redis:
            return True, limit, 0

        now = time.time()
        key = f"ratelimit:{tenant_id}"

        pipe = self._redis.pipeline()

        # Remove requests outside the window
        pipe.zremrangebyscore(key, 0, now - _WINDOW_SIZE_SECONDS)
        # Count requests in the window
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # TTL on the key
        pipe.expire(key, _WINDOW_SIZE_SECONDS + 10)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= limit:
            # Calculate Retry-After
            oldest = await self._redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(_WINDOW_SIZE_SECONDS - (now - oldest[0][1])) + 1
            else:
                retry_after = _WINDOW_SIZE_SECONDS
            return False, 0, max(retry_after, 1)

        remaining = max(0, limit - request_count - 1)
        return True, remaining, 0

    async def close(self) -> None:
        """Chiudi connessione Redis."""
        if self._redis:
            await self._redis.close()


# ── Singleton ──────────────────────── ────────────────────────
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Restituisce il singleton RateLimiter."""
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware che applica rate limiting per-tenant.

    Aggiunge headers: X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip for /health and /docs
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        tenant_id = get_tenant_id()
        if not tenant_id:
            # No tenant in context = pre-auth, skip rate limit
            return await call_next(request)

        limiter = get_rate_limiter()
        allowed, remaining, retry_after = await limiter.check_rate_limit(tenant_id)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                tenant_id=tenant_id,
                retry_after=retry_after,
            )
            raise AppException(ErrorCode.TENANT_103)

        response = await call_next(request)

        # Add headers rate limit
        response.headers["X-RateLimit-Limit"] = str(_DEFAULT_RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if retry_after > 0:
            response.headers["Retry-After"] = str(retry_after)

        return response
