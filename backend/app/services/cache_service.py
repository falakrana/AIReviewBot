"""
Redis-backed caching service.

Strategy:
    key  = "analysis:" + SHA-256(code_string)
    value= JSON-serialised AnalysisIssue dict

If Redis is unavailable the service degrades gracefully (cache disabled),
so the system continues to function without caching.
"""
import hashlib
import json
import logging
from typing import Optional

import redis

from backend.app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self) -> None:
        try:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._client.ping()
            self.enabled = True
            logger.info("[Cache] Redis connected — caching enabled.")
        except Exception as exc:
            logger.warning(f"[Cache] Redis unavailable — caching disabled. ({exc})")
            self._client = None
            self.enabled = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, code: str) -> str:
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
        return f"analysis:{digest}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, code: str) -> Optional[dict]:
        """Return cached analysis dict for *code*, or None on miss/error."""
        if not self.enabled:
            return None
        try:
            raw = self._client.get(self._key(code))
            if raw:
                logger.debug("[Cache] HIT")
                return json.loads(raw)
            logger.debug("[Cache] MISS")
            return None
        except Exception as exc:
            logger.warning(f"[Cache] get error: {exc}")
            return None

    def set(self, code: str, result: dict) -> bool:
        """Store *result* keyed by hash of *code*. Returns True on success."""
        if not self.enabled:
            return False
        try:
            self._client.setex(
                self._key(code),
                settings.CACHE_TTL,
                json.dumps(result),
            )
            logger.debug("[Cache] stored result")
            return True
        except Exception as exc:
            logger.warning(f"[Cache] set error: {exc}")
            return False

    def is_healthy(self) -> bool:
        """Ping Redis — used by the /health endpoint."""
        if not self.enabled or self._client is None:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False


# Module-level singleton — shared across imports in the same process
cache_service = CacheService()
