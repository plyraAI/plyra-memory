"""Semantic cache — avoids re-embedding and re-searching for similar queries."""

from __future__ import annotations

import logging
from datetime import datetime

from plyra_memory.config import MemoryConfig
from plyra_memory.embedders.base import Embedder
from plyra_memory.retrieval.engine import HybridRetrieval
from plyra_memory.schema import RecallResult, _new_id, _utcnow

log = logging.getLogger(__name__)


class SemanticCache:
    """Cache that matches queries by embedding similarity, not exact string."""

    def __init__(self, embedder: Embedder, config: MemoryConfig) -> None:
        self._embedder = embedder
        self._config = config
        # {key: (RecallResult, cached_at, query_embedding)}
        self._cache: dict[str, tuple[RecallResult, datetime, list[float]]] = {}

    async def get(
        self,
        query: str,
        *,
        query_embedding: list[float] | None = None,
    ) -> tuple[RecallResult | None, list[float]]:
        """Return (cached_result_or_None, query_embedding).

        Always returns *query_embedding* so the caller can reuse it
        without embedding the same query again.
        """
        qemb = (
            query_embedding
            if query_embedding is not None
            else await self._embedder.embed(query)
        )
        if not self._config.cache_enabled:
            return None, qemb
        now = _utcnow()
        for _key, (result, cached_at, cemb) in list(self._cache.items()):
            age = (now - cached_at).total_seconds()
            if age > self._config.cache_ttl_seconds:
                continue
            sim = HybridRetrieval.cosine_similarity(qemb, cemb)
            if sim >= self._config.cache_similarity_threshold:
                log.debug("cache hit  sim=%.3f", sim)
                return result.model_copy(update={"cache_hit": True}), qemb
        return None, qemb

    async def set(
        self,
        query: str,
        result: RecallResult,
        *,
        query_embedding: list[float] | None = None,
    ) -> None:
        """Cache a query result.  Reuses *query_embedding* when provided."""
        if not self._config.cache_enabled:
            return
        qemb = (
            query_embedding
            if query_embedding is not None
            else await self._embedder.embed(query)
        )
        self._cache[_new_id()] = (result, _utcnow(), qemb)
        # Evict oldest if over max
        if len(self._cache) > self._config.cache_max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest]

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)
