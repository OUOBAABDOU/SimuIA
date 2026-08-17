from __future__ import annotations

import logging
import time

from fastapi import HTTPException, Request
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger("iarh.audit")

_RATE_LIMITED_PATHS = {
    "/api/v1/auth/register": (5, 300),
    "/api/v1/auth/login": (10, 60),
    "/api/v1/auth/refresh": (20, 60),
}


async def enforce_rate_limit(request: Request) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled or request.url.path not in _RATE_LIMITED_PATHS:
        return

    limit, window = _RATE_LIMITED_PATHS[request.url.path]
    client_ip = request.client.host if request.client else "unknown"
    bucket = int(time.time() // window)
    key = f"iarh:ratelimit:{request.url.path}:{client_ip}:{bucket}"
    redis: Redis | None = None
    try:
        redis = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
            decode_responses=True,
        )
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window + 1)
        if count > limit:
            raise HTTPException(status_code=429, detail="RATE_LIMITED", headers={"Retry-After": str(window)})
    except HTTPException:
        raise
    except Exception:
        # Availability takes precedence over rate limiting when Redis is down.
        logger.warning("rate_limit_unavailable", extra={"path": request.url.path})
    finally:
        if redis is not None:
            await redis.aclose()


def audit_event(event: str, request: Request, *, user_id: str | None = None, outcome: str = "success") -> None:
    logger.info(
        "audit_event",
        extra={
            "event": event,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_id": user_id,
            "outcome": outcome,
        },
    )
