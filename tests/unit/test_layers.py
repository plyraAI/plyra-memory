"""Unit tests for memory layers (working, episodic, semantic)."""

from __future__ import annotations

import pytest
import pytest_asyncio

from plyra_memory.config import MemoryConfig
from plyra_memory.layers.episodic import EpisodicLayer
from plyra_memory.layers.semantic import SemanticLayer
from plyra_memory.layers.working import WorkingMemoryLayer
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    EpisodicQuery,
    Fact,
    FactRelation,
    SemanticQuery,
    WorkingEntry,
)

# ── Working Memory ───────────────────────────────────────────


@pytest.mark.asyncio
class TestWorkingMemoryLayer:
    @pytest_asyncio.fixture
    async def working(self, store, config):
        return WorkingMemoryLayer(store, config)

    async def test_add_and_get(self, working, agent_id, session_id):
        entry = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="debugging LangGraph",
        )
        result = await working.add(entry)
        assert result.content == "debugging LangGraph"

        state = await working.get(session_id)
        assert len(state.entries) == 1

    async def test_eviction_on_max(self, store, agent_id, session_id):
        cfg = MemoryConfig(
            store_url="unused",
            vectors_url="unused",
            working_max_entries=3,
            cache_enabled=False,
        )
        working = WorkingMemoryLayer(store, cfg)

        for i in range(4):
            entry = WorkingEntry(
                session_id=session_id,
                agent_id=agent_id,
                content=f"entry {i}",
                importance=0.5,
            )
            await working.add(entry)

        state = await working.get(session_id)
        assert len(state.entries) <= 3

    async def test_clear(self, working, agent_id, session_id):
        entry = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="temp",
        )
        await working.add(entry)
        await working.clear(session_id)
        state = await working.get(session_id)
        assert len(state.entries) == 0

    async def test_flush_to_episodic(
        self, working, store, mock_embedder, mock_vectors, config, agent_id, session_id
    ):
        episodic = EpisodicLayer(store, mock_vectors, mock_embedder, config)

        entry = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="user asked about memory",
            source="user",
        )
        await working.add(entry)

        episodes = await working.flush_to_episodic(session_id, agent_id, episodic)
        assert len(episodes) >= 1
        assert episodes[0].content == "user asked about memory"

        # Working should be cleared after flush
        state = await working.get(session_id)
        assert len(state.entries) == 0


# ── Episodic Memory ──────────────────────────────────────────


@pytest.mark.asyncio
class TestEpisodicLayer:
    @pytest_asyncio.fixture
    async def episodic(self, store, mock_vectors, mock_embedder, config):
        return EpisodicLayer(store, mock_vectors, mock_embedder, config)

    async def test_record_and_get(self, episodic, agent_id, session_id):
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="hello from test",
        )
        result = await episodic.record(ep)
        assert result.id == ep.id

        loaded = await episodic.get(ep.id)
        assert loaded is not None
        assert loaded.content == "hello from test"

    async def test_search_returns_tuples(self, episodic, agent_id, session_id):
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="test content for search",
        )
        await episodic.record(ep)

        results = await episodic.search("test", agent_id=agent_id, top_k=5)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], tuple)
            assert len(results[0]) == 2
            episode, score = results[0]
            assert isinstance(episode, Episode)
            assert isinstance(score, float)

    async def test_query(self, episodic, agent_id, session_id):
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.AGENT_RESPONSE,
            content="response content",
        )
        await episodic.record(ep)

        query = EpisodicQuery(agent_id=agent_id, limit=10)
        results = await episodic.query(query)
        assert len(results) >= 1


# ── Semantic Memory ──────────────────────────────────────────


@pytest.mark.asyncio
class TestSemanticLayer:
    @pytest_asyncio.fixture
    async def semantic(self, store, mock_vectors, mock_embedder, config):
        return SemanticLayer(store, mock_vectors, mock_embedder, config)

    async def test_learn_and_search(self, semantic, agent_id):
        fact = Fact(
            agent_id=agent_id,
            subject="Python",
            predicate=FactRelation.IS_A,
            object="programming language",
        )
        result = await semantic.learn(fact)
        assert result.subject == "Python"

        results = await semantic.search("Python", agent_id=agent_id, top_k=5)
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], tuple)
            fact_result, score = results[0]
            assert isinstance(fact_result, Fact)
            assert isinstance(score, float)

    async def test_learn_dedup(self, semantic, agent_id):
        """Learning the same fact twice should not create duplicates."""
        for _ in range(2):
            fact = Fact(
                agent_id=agent_id,
                subject="Python",
                predicate=FactRelation.IS_A,
                object="language",
            )
            await semantic.learn(fact)

        query = SemanticQuery(agent_id=agent_id, limit=100)
        results = await semantic.query(query)
        # Should be 1 fact (deduped on fingerprint)
        assert len(results) == 1

    async def test_forget(self, semantic, agent_id):
        fact = Fact(
            agent_id=agent_id,
            subject="old",
            predicate=FactRelation.HAS_PROPERTY,
            object="deprecated",
        )
        result = await semantic.learn(fact)
        success = await semantic.forget(result.id)
        assert success is True

        query = SemanticQuery(agent_id=agent_id)
        results = await semantic.query(query)
        assert len(results) == 0
