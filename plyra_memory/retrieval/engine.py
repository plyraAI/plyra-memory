"""Hybrid retrieval engine — fuses results from all three layers."""

from __future__ import annotations

import logging
import math
import time

from plyra_memory.config import MemoryConfig
from plyra_memory.embedders.base import Embedder
from plyra_memory.layers.episodic import EpisodicLayer
from plyra_memory.layers.semantic import SemanticLayer
from plyra_memory.layers.working import WorkingMemoryLayer
from plyra_memory.schema import (
    MemoryLayer,
    RankedMemory,
    RecallRequest,
    RecallResult,
    _new_id,
    _utcnow,
)

log = logging.getLogger(__name__)

# Try to use numpy for fast cosine similarity; fall back to pure-Python.
try:
    import numpy as _np

    def _cosine_np(a: list[float], b: list[float]) -> float:
        va, vb = _np.asarray(a), _np.asarray(b)
        na, nb = _np.linalg.norm(va), _np.linalg.norm(vb)
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(_np.dot(va, vb) / (na * nb))

    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False


class HybridRetrieval:
    """Multi-layer retrieval with weighted score fusion."""

    def __init__(
        self,
        working: WorkingMemoryLayer,
        episodic: EpisodicLayer,
        semantic: SemanticLayer,
        embedder: Embedder,
        config: MemoryConfig,
    ) -> None:
        self._working = working
        self._episodic = episodic
        self._semantic = semantic
        self._embedder = embedder
        self._config = config

    async def recall(
        self,
        request: RecallRequest,
        *,
        query_embedding: list[float] | None = None,
    ) -> RecallResult:
        """Recall relevant memories.

        If *query_embedding* is supplied it is reused everywhere, saving
        redundant ``embed()`` calls.
        """
        t0 = time.monotonic()
        all_results: list[RankedMemory] = []

        # Compute query embedding exactly once
        if query_embedding is None:
            query_embedding = await self._embedder.embed(request.query)

        # ----- WORKING layer -----
        if MemoryLayer.WORKING in request.layers and request.session_id:
            state = await self._working.get(request.session_id)
            if state.entries:
                # Batch-embed all working entries in one model call
                texts = [e.content for e in state.entries]
                embeddings = await self._embedder.embed_batch(texts)
                decay = self._config.semantic_decay_lambda
                for entry, emb in zip(state.entries, embeddings):
                    sim = self.cosine_similarity(query_embedding, emb)
                    rec = self.recency_score(entry.created_at, decay)
                    score = (
                        sim * request.similarity_weight
                        + rec * request.recency_weight
                        + entry.importance * request.importance_weight
                    )
                    if score >= request.min_score:
                        all_results.append(
                            RankedMemory(
                                id=_new_id(),
                                layer=MemoryLayer.WORKING,
                                content=entry.content,
                                score=round(min(score, 1.0), 4),
                                similarity=round(max(0.0, min(sim, 1.0)), 4),
                                recency=round(max(0.0, min(rec, 1.0)), 4),
                                importance=entry.importance,
                                created_at=entry.created_at,
                                source_id=entry.id,
                            )
                        )

        # ----- EPISODIC layer -----
        if MemoryLayer.EPISODIC in request.layers:
            ep_results = await self._episodic.search(
                request.query,
                agent_id=request.agent_id,
                session_id=request.session_id,
                top_k=request.top_k * 2,
                query_embedding=query_embedding,
            )
            decay = self._config.semantic_decay_lambda
            for ep, sim in ep_results:
                rec = self.recency_score(ep.created_at, decay)
                score = (
                    sim * request.similarity_weight
                    + rec * request.recency_weight
                    + ep.importance * request.importance_weight
                )
                if score >= request.min_score:
                    all_results.append(
                        RankedMemory(
                            id=_new_id(),
                            layer=MemoryLayer.EPISODIC,
                            content=ep.content,
                            score=round(min(score, 1.0), 4),
                            similarity=round(max(0.0, min(sim, 1.0)), 4),
                            recency=round(max(0.0, min(rec, 1.0)), 4),
                            importance=ep.importance,
                            created_at=ep.created_at,
                            source_id=ep.id,
                        )
                    )

        # ----- SEMANTIC layer -----
        if MemoryLayer.SEMANTIC in request.layers:
            sem_results = await self._semantic.search(
                request.query,
                agent_id=request.agent_id,
                top_k=request.top_k * 2,
                query_embedding=query_embedding,
            )
            decay = self._config.semantic_decay_lambda
            for fact, sim in sem_results:
                rec = self.recency_score(fact.last_accessed, decay)
                score = (
                    sim * request.similarity_weight
                    + rec * request.recency_weight
                    + fact.importance * request.importance_weight
                )
                if score >= request.min_score:
                    all_results.append(
                        RankedMemory(
                            id=_new_id(),
                            layer=MemoryLayer.SEMANTIC,
                            content=fact.content,
                            score=round(min(score, 1.0), 4),
                            similarity=round(max(0.0, min(sim, 1.0)), 4),
                            recency=round(max(0.0, min(rec, 1.0)), 4),
                            importance=fact.importance,
                            created_at=fact.created_at,
                            source_id=fact.id,
                        )
                    )

        total = len(all_results)
        all_results.sort(key=lambda r: r.score, reverse=True)
        latency_ms = (time.monotonic() - t0) * 1000

        log.debug(
            "recall query=%r  results=%d  latency=%.1f ms",
            request.query[:60],
            total,
            latency_ms,
        )

        return RecallResult(
            query=request.query,
            results=all_results[: request.top_k],
            total_found=total,
            layers_searched=request.layers,
            latency_ms=round(latency_ms, 2),
        )

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Cosine similarity — uses numpy when available."""
        if not a or not b:
            return 0.0
        if _HAS_NUMPY:
            return _cosine_np(a, b)
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def recency_score(dt: object, decay_lambda: float = 0.01) -> float:
        """Exponential decay: score = exp(-λ * hours_ago)."""
        now = _utcnow()
        hours_ago = (now - dt).total_seconds() / 3600.0  # type: ignore[operator]
        return math.exp(-decay_lambda * hours_ago)
