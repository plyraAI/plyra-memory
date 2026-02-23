"""Integration tests – full Memory class lifecycle."""

from __future__ import annotations

import pytest
import pytest_asyncio

from plyra_memory.memory import Memory
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    Fact,
    FactRelation,
    WorkingEntry,
)


@pytest.mark.asyncio
class TestMemoryIntegration:
    @pytest_asyncio.fixture
    async def memory(self, config, mock_embedder, mock_vectors):
        """Create a Memory instance with tmp_path config and mock backends."""
        mem = Memory(
            config=config,
            agent_id="test-agent",
            embedder=mock_embedder,
            vectors=mock_vectors,
        )
        await mem._ensure_initialized()
        yield mem
        await mem.close()

    async def test_context_manager(self, config, mock_embedder, mock_vectors):
        async with Memory(
            config=config,
            agent_id="test-agent",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            assert mem._initialized is True
        assert mem._initialized is False

    async def test_working_memory_add_and_get(self, memory):
        entry = WorkingEntry(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            content="user is debugging LangGraph",
        )
        await memory.working.add(entry)
        state = await memory.working.get(memory.session_id)
        assert state.entry_count == 1
        assert state.entries[0].content == "user is debugging LangGraph"

    async def test_episodic_record_and_get(self, memory):
        ep = Episode(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="tell me about memory systems",
        )
        await memory.episodic.record(ep)
        loaded = await memory.episodic.get(ep.id)
        assert loaded is not None
        assert loaded.content == "tell me about memory systems"

    async def test_semantic_learn_and_query(self, memory):
        fact = Fact(
            agent_id=memory.agent_id,
            subject="plyra",
            predicate=FactRelation.IS_A,
            object="memory system",
        )
        await memory.semantic.learn(fact)

        from plyra_memory.schema import SemanticQuery

        query = SemanticQuery(agent_id=memory.agent_id)
        facts = await memory.semantic.query(query)
        assert len(facts) == 1
        assert facts[0].subject == "plyra"

    async def test_recall(self, memory):
        entry = WorkingEntry(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            content="debugging memory recall",
        )
        await memory.working.add(entry)

        result = await memory.recall("debugging")
        assert result is not None
        assert result.query == "debugging"

    async def test_context_for(self, memory):
        entry = WorkingEntry(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            content="context building test",
        )
        await memory.working.add(entry)

        ctx = await memory.context_for("context", token_budget=1000)
        assert ctx is not None
        assert ctx.token_budget == 1000

    async def test_flush(self, memory):
        entry = WorkingEntry(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            content="will be flushed",
            source="user",
        )
        await memory.working.add(entry)

        episodes = await memory.flush()
        assert len(episodes) >= 1

        # Working should be empty
        state = await memory.working.get(memory.session_id)
        assert state.entry_count == 0

    async def test_full_lifecycle(self, config, mock_embedder, mock_vectors):
        """Full lifecycle: init → add → recall → flush → close."""
        async with Memory(
            config=config,
            agent_id="lifecycle-agent",
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            # Working memory
            we = WorkingEntry(
                session_id=mem.session_id,
                agent_id=mem.agent_id,
                content="user wants to build a chatbot",
            )
            await mem.working.add(we)

            # Episodic memory
            ep = Episode(
                session_id=mem.session_id,
                agent_id=mem.agent_id,
                event=EpisodeEvent.USER_MESSAGE,
                content="how do I build a chatbot?",
            )
            await mem.episodic.record(ep)

            # Semantic memory
            fact = Fact(
                agent_id=mem.agent_id,
                subject="chatbot",
                predicate=FactRelation.REQUIRES,
                object="NLP capabilities",
            )
            await mem.semantic.learn(fact)

            # Recall
            result = await mem.recall("chatbot")
            assert result.query == "chatbot"

            # Context
            ctx = await mem.context_for("chatbot")
            assert ctx.query == "chatbot"

            # Flush
            episodes = await mem.flush()
            assert len(episodes) >= 1
