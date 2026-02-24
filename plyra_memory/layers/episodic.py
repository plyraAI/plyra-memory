"""Episodic memory layer — append-only immutable event log."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from plyra_memory.config import MemoryConfig
from plyra_memory.embedders.base import Embedder
from plyra_memory.schema import (
    Episode,
    EpisodicQuery,
)
from plyra_memory.storage.base import StorageBackend
from plyra_memory.vectors.base import VectorBackend

if TYPE_CHECKING:
    from plyra_memory.layers.semantic import SemanticLayer

log = logging.getLogger(__name__)


class EpisodicLayer:
    """Append-only episodic event log with vector embedding."""

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

    async def record(self, episode: Episode) -> Episode:
        """Record an episode event. Embeds and indexes the content."""
        saved = await self._store.save_episode(episode)

        try:
            embedding = await self._embedder.embed(episode.content)
            await self._vectors.upsert(
                id=saved.id,
                embedding=embedding,
                metadata={
                    "layer": "episodic",
                    "session_id": episode.session_id,
                    "agent_id": episode.agent_id,
                    "importance": episode.importance,
                },
            )
        except Exception:
            log.warning(
                "Failed to embed/index episode %s — stored in SQL only",
                saved.id,
                exc_info=True,
            )

        return saved

    async def search(
        self,
        text_query: str,
        agent_id: str | None = None,
        session_id: str | None = None,
        top_k: int = 10,
        *,
        query_embedding: list[float] | None = None,
        promoter=None,
    ) -> list[tuple[Episode, float]]:
        """Semantic search over episodes. Returns (episode, score) tuples."""
        embedding = (
            query_embedding
            if query_embedding is not None
            else await self._embedder.embed(text_query)
        )

        vector_results = await self._vectors.query(
            embedding, top_k * 3, {"layer": "episodic"}
        )

        results: list[tuple[Episode, float]] = []
        for vr in vector_results:
            ep = await self._store.get_episode(vr["id"])
            if ep is None:
                continue
            if agent_id and ep.agent_id != agent_id:
                continue
            if session_id and ep.session_id != session_id:
                continue
            await self._store.increment_episode_access(ep.id)
            results.append((ep, vr["score"]))

        # Trigger auto-promotion check after search hits (background task)
        if promoter and agent_id and results:
            import asyncio

            asyncio.create_task(promoter.check_and_promote(agent_id))

        return results[:top_k]

    async def query(self, query: EpisodicQuery) -> list[Episode]:
        """Query episodes using structured filters."""
        return await self._store.get_episodes(query)

    async def get(self, episode_id: str) -> Episode | None:
        """Get a single episode by ID."""
        return await self._store.get_episode(episode_id)

    async def _check_and_promote(
        self, episode: Episode, semantic_layer: SemanticLayer
    ) -> None:
        """Promote frequently-accessed episodes to semantic memory."""
        from plyra_memory.schema import Fact, FactRelation

        if (
            episode.access_count >= self._config.semantic_promotion_threshold
            and not episode.promoted
        ):
            fact = Fact(
                agent_id=episode.agent_id,
                subject="agent",
                predicate=FactRelation.KNOWS,
                object=episode.content,
                source_episode_id=episode.id,
            )
            result = await semantic_layer.learn(fact)
            await self._store.mark_episode_promoted(episode.id, result.id)
