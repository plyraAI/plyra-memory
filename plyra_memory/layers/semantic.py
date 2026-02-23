"""Semantic memory layer — durable fact store with decay model."""

from __future__ import annotations

import logging

from plyra_memory.config import MemoryConfig
from plyra_memory.embedders.base import Embedder
from plyra_memory.schema import (
    Fact,
    SemanticQuery,
    _utcnow,
)
from plyra_memory.storage.base import StorageBackend
from plyra_memory.vectors.base import VectorBackend

log = logging.getLogger(__name__)


class SemanticLayer:
    """Durable fact store with subject/predicate/object triples and decay model."""

    def __init__(
        self,
        store: StorageBackend,
        vectors: VectorBackend,
        embedder: Embedder,
        config: MemoryConfig,
    ) -> None:
        self._store = store
        self._vectors = vectors
        self._embedder = embedder
        self._config = config

    async def learn(self, fact: Fact) -> Fact:
        """Learn a new fact or update an existing one (dedup on fingerprint)."""
        # Check for existing fact with same fingerprint
        existing = await self._store.get_fact_by_fingerprint(fact.fingerprint)
        if existing:
            updated = existing.model_copy(
                update={
                    "confidence": (existing.confidence + fact.confidence) / 2.0,
                    "last_confirmed": _utcnow(),
                    "object": fact.object,
                    "content": fact.content,
                }
            )
            result = await self._store.save_fact(updated)
        else:
            result = await self._store.save_fact(fact)

        try:
            embedding = await self._embedder.embed(result.content)
            await self._vectors.upsert(
                id=result.id,
                embedding=embedding,
                metadata={
                    "layer": "semantic",
                    "agent_id": result.agent_id,
                    "predicate": result.predicate.value,
                    "confidence": result.confidence,
                },
            )
        except Exception:
            log.warning(
                "Failed to embed/index fact %s — stored in SQL only",
                result.id,
                exc_info=True,
            )

        return result

    async def search(
        self,
        text_query: str,
        agent_id: str | None = None,
        top_k: int = 10,
        min_decay_score: float = 0.0,
        *,
        query_embedding: list[float] | None = None,
    ) -> list[tuple[Fact, float]]:
        """Semantic search over facts. Returns (fact, score) tuples."""
        embedding = (
            query_embedding
            if query_embedding is not None
            else await self._embedder.embed(text_query)
        )

        vector_results = await self._vectors.query(
            embedding, top_k * 2, {"layer": "semantic"}
        )

        results: list[tuple[Fact, float]] = []
        for vr in vector_results:
            fact = await self._store.get_fact(vr["id"])
            if fact is None:
                continue
            if agent_id and fact.agent_id != agent_id:
                continue
            if fact.is_expired:
                continue
            if fact.decay_score < min_decay_score:
                continue
            await self._store.update_fact_access(fact.id)
            results.append((fact, vr["score"]))
        return results[:top_k]

    async def query(self, query: SemanticQuery) -> list[Fact]:
        """Query facts using structured filters."""
        facts = await self._store.get_facts(query)
        if not query.include_expired:
            facts = [f for f in facts if not f.is_expired]
        return facts

    async def forget(self, fact_id: str) -> bool:
        """Delete a fact from storage and vectors."""
        await self._vectors.delete(fact_id)
        return await self._store.delete_fact(fact_id)
