"""Tests for Memory.remember() and Memory._extract_and_learn()."""

from __future__ import annotations

import pytest

from plyra_memory import Memory, MemoryConfig
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    Fact,
    FactRelation,
    WorkingEntry,
)

# Re-export fixtures from conftest (mock_embedder, mock_vectors, store, config)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def mem_config(tmp_path) -> MemoryConfig:
    """Dedicated config for remember() tests (avoids collision with other
    test suites that share the ``config`` fixture)."""
    return MemoryConfig(
        store_url=str(tmp_path / "mem_api_test.db"),
        vectors_url=str(tmp_path / "mem_api_test.index"),
        embed_model="mock",
        embed_dim=384,
        working_max_entries=50,
        cache_enabled=False,
    )


# ---------------------------------------------------------------------------
# remember() basics
# ---------------------------------------------------------------------------


class TestRemember:
    """Core behaviour of ``Memory.remember()``."""

    async def test_returns_all_three_keys(
        self, mem_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("hello world")
            assert "working" in result
            assert "episodic" in result
            assert "facts" in result

    async def test_working_entry_stored(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("working entry test")
            we = result["working"]
            assert isinstance(we, WorkingEntry)
            assert we.content == "working entry test"

    async def test_episode_stored(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("episode test")
            ep = result["episodic"]
            assert isinstance(ep, Episode)
            assert ep.content == "episode test"
            assert ep.event == EpisodeEvent.AGENT_RESPONSE  # default

    async def test_custom_event(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember(
                "user said hi",
                event=EpisodeEvent.USER_MESSAGE,
            )
            assert result["episodic"].event == EpisodeEvent.USER_MESSAGE

    async def test_importance_propagated(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("important", importance=0.9)
            assert result["working"].importance == 0.9
            assert result["episodic"].importance == 0.9

    async def test_source_propagated(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("src test", source="tool")
            assert result["working"].source == "tool"

    async def test_metadata_propagated(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("meta test", metadata={"k": "v"})
            assert result["working"].metadata == {"k": "v"}

    async def test_session_and_agent_ids(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="ag-1",
            session_id="sess-1",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("ids test")
            assert result["working"].session_id == "sess-1"
            assert result["working"].agent_id == "ag-1"
            assert result["episodic"].session_id == "sess-1"
            assert result["episodic"].agent_id == "ag-1"

    async def test_no_facts_for_plain_text(
        self, mem_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("just a random thought")
            assert result["facts"] == []


# ---------------------------------------------------------------------------
# _extract_and_learn() — heuristic fact extraction
# ---------------------------------------------------------------------------


class TestExtractAndLearn:
    """Pattern-based fact extraction never raises."""

    async def test_extracts_name(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            facts = await mem._extract_and_learn("my name is Alice")
            assert len(facts) >= 1
            assert any(f.predicate == FactRelation.IS for f in facts)
            assert any("Alice" in f.object for f in facts)

    async def test_extracts_preference(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            facts = await mem._extract_and_learn("I prefer dark mode")
            assert len(facts) >= 1
            assert any(f.predicate == FactRelation.PREFERS for f in facts)

    async def test_extracts_works_on(self, mem_config, mock_embedder, mock_vectors):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            facts = await mem._extract_and_learn("I'm working on plyra")
            assert len(facts) >= 1
            assert any(f.predicate == FactRelation.WORKS_ON for f in facts)

    async def test_no_match_returns_empty(
        self, mem_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            facts = await mem._extract_and_learn("the weather is nice today")
            assert facts == []

    async def test_never_raises(self, mem_config, mock_embedder, mock_vectors):
        """Even with bizarre input, _extract_and_learn must not raise."""
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            facts = await mem._extract_and_learn("")
            assert facts == []
            facts = await mem._extract_and_learn("x" * 10_000)
            assert isinstance(facts, list)

    async def test_remember_routes_facts(self, mem_config, mock_embedder, mock_vectors):
        """remember() returns extracted facts from _extract_and_learn."""
        async with Memory(
            config=mem_config,
            agent_id="test",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await mem.remember("my name is Bob")
            assert len(result["facts"]) >= 1
            assert isinstance(result["facts"][0], Fact)
