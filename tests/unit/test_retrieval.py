"""Unit tests for retrieval engine and semantic cache."""

from __future__ import annotations

from datetime import UTC

import pytest
import pytest_asyncio

from plyra_memory.config import MemoryConfig
from plyra_memory.layers.episodic import EpisodicLayer
from plyra_memory.layers.semantic import SemanticLayer
from plyra_memory.layers.working import WorkingMemoryLayer
from plyra_memory.retrieval.cache import SemanticCache
from plyra_memory.retrieval.engine import HybridRetrieval
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    Fact,
    FactRelation,
    RecallRequest,
    RecallResult,
    WorkingEntry,
)


@pytest.mark.asyncio
class TestHybridRetrieval:
    @pytest_asyncio.fixture
    async def retrieval(self, store, mock_vectors, mock_embedder, config):
        working = WorkingMemoryLayer(store, config)
        episodic = EpisodicLayer(store, mock_vectors, mock_embedder, config)
        semantic = SemanticLayer(store, mock_vectors, mock_embedder, config)
        return HybridRetrieval(working, episodic, semantic, mock_embedder, config)

    async def test_recall_empty(self, retrieval, agent_id, session_id):
        req = RecallRequest(
            query="anything",
            session_id=session_id,
            agent_id=agent_id,
            top_k=10,
        )
        result = await retrieval.recall(req)
        assert isinstance(result, RecallResult)
        assert len(result.results) == 0

    async def test_recall_with_data(
        self, store, mock_vectors, mock_embedder, config, agent_id, session_id
    ):
        working = WorkingMemoryLayer(store, config)
        episodic = EpisodicLayer(store, mock_vectors, mock_embedder, config)
        semantic = SemanticLayer(store, mock_vectors, mock_embedder, config)
        retrieval = HybridRetrieval(working, episodic, semantic, mock_embedder, config)

        # Add working entry
        we = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="user is debugging",
        )
        await working.add(we)

        # Add episode
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="help me debug",
        )
        await episodic.record(ep)

        # Add fact
        fact = Fact(
            agent_id=agent_id,
            subject="debugging",
            predicate=FactRelation.HAS_PROPERTY,
            object="important skill",
        )
        await semantic.learn(fact)

        req = RecallRequest(
            query="debugging",
            session_id=session_id,
            agent_id=agent_id,
            top_k=10,
        )
        result = await retrieval.recall(req)
        assert len(result.results) > 0

    async def test_cosine_similarity_identical(self):
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert HybridRetrieval.cosine_similarity(a, b) == pytest.approx(1.0)

    async def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert HybridRetrieval.cosine_similarity(a, b) == pytest.approx(0.0)

    async def test_cosine_similarity_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert HybridRetrieval.cosine_similarity(a, b) == 0.0

    async def test_recency_score(self):
        from datetime import datetime

        now = datetime.now(UTC)
        score = HybridRetrieval.recency_score(now)
        assert 0.9 < score <= 1.0

        from datetime import timedelta

        old = now - timedelta(days=30)
        old_score = HybridRetrieval.recency_score(old)
        assert old_score < score


@pytest.mark.asyncio
class TestSemanticCache:
    async def test_cache_miss(self, mock_embedder, config):
        cache = SemanticCache(mock_embedder, config)
        result, query_embedding = await cache.get("query")
        assert result is None
        assert isinstance(query_embedding, list)

    async def test_cache_set_and_get(self, mock_embedder, config):
        cfg = MemoryConfig(
            store_url=config.store_url,
            vectors_url=config.vectors_url,
            cache_enabled=True,
            cache_max_size=100,
            cache_ttl_seconds=300,
        )
        cache = SemanticCache(mock_embedder, cfg)

        recall_result = RecallResult(
            query="test", results=[], latency_ms=1.0, cache_hit=False
        )
        await cache.set("test", recall_result)
        cached, query_embedding = await cache.get("test")
        # MockEmbedder always returns same vector, so this should hit
        assert cached is not None
        assert isinstance(query_embedding, list)

    async def test_cache_clear(self, mock_embedder, config):
        cache = SemanticCache(mock_embedder, config)
        recall_result = RecallResult(
            query="test", results=[], latency_ms=1.0, cache_hit=False
        )
        await cache.set("test", recall_result)
        cache.clear()
        assert cache.size == 0
