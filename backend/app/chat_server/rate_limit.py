"""Sliding-window rate limiter backed by Redis.

Key shape: "rl:{site_key}:{ip}:{minute_bucket}".
"""

from __future__ import annotations

import time
from functools import lru_cache

import redis

from app.core.config import settings


@lru_cache(maxsize=1)
def _client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def check_and_increment(site_key: str, ip: str, *, limit: int | None = None) -> bool:
    """Return True if the request is allowed, False if it exceeds the limit."""
    cap = limit if limit is not None else settings.chat_rate_limit_per_min
    bucket = int(time.time() // 60)
    key = f"rl:{site_key}:{ip}:{bucket}"
    try:
        pipe = _client().pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, 65)
        count, _ = pipe.execute()
    except Exception:
        # Fail open: don't deny chat if Redis is down.
        return True
    return int(count) <= cap
