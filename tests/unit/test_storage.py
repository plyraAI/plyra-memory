"""Unit tests for storage layer (SQLite)."""

from __future__ import annotations

import pytest

from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    EpisodicQuery,
    Fact,
    FactRelation,
    SemanticQuery,
    Session,
    WorkingEntry,
)


@pytest.mark.asyncio
class TestSQLiteStore:
    async def test_session_roundtrip(self, store, agent_id, session_id):
        session = Session(id=session_id, agent_id=agent_id)
        await store.save_session(session)
        loaded = await store.get_session(session_id)
        assert loaded is not None
        assert loaded.id == session_id
        assert loaded.agent_id == agent_id

    async def test_session_not_found(self, store):
        loaded = await store.get_session("nonexistent")
        assert loaded is None

    async def test_working_entry_roundtrip(self, store, agent_id, session_id):
        entry = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="debugging issue",
        )
        await store.save_working_entry(entry)
        entries = await store.get_working_entries(session_id)
        assert len(entries) == 1
        assert entries[0].content == "debugging issue"

    async def test_delete_working_entry_by_id(self, store, agent_id, session_id):
        entry = WorkingEntry(
            session_id=session_id,
            agent_id=agent_id,
            content="to be deleted",
        )
        await store.save_working_entry(entry)
        result = await store.delete_working_entry_by_id(entry.id)
        assert result is True
        entries = await store.get_working_entries(session_id)
        assert len(entries) == 0

    async def test_clear_working_entries(self, store, agent_id, session_id):
        for i in range(3):
            entry = WorkingEntry(
                session_id=session_id,
                agent_id=agent_id,
                content=f"entry {i}",
            )
            await store.save_working_entry(entry)

        await store.delete_working_entries(session_id)
        entries = await store.get_working_entries(session_id)
        assert len(entries) == 0

    async def test_clear_working_entries_method(self, store, agent_id, session_id):
        """Test the delete_working_entries method."""
        for i in range(3):
            entry = WorkingEntry(
                session_id=session_id,
                agent_id=agent_id,
                content=f"entry {i}",
            )
            await store.save_working_entry(entry)

        count = await store.delete_working_entries(session_id)
        assert count == 3
        entries = await store.get_working_entries(session_id)
        assert len(entries) == 0

    async def test_episode_roundtrip(self, store, agent_id, session_id):
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="hello world",
        )
        await store.save_episode(ep)
        query = EpisodicQuery(session_id=session_id)
        episodes = await store.get_episodes(query)
        assert len(episodes) == 1
        assert episodes[0].content == "hello world"

    async def test_get_episode_by_id(self, store, agent_id, session_id):
        ep = Episode(
            session_id=session_id,
            agent_id=agent_id,
            event=EpisodeEvent.AGENT_RESPONSE,
            content="response text",
        )
        await store.save_episode(ep)
        loaded = await store.get_episode(ep.id)
        assert loaded is not None
        assert loaded.id == ep.id

    async def test_fact_roundtrip(self, store, agent_id):
        fact = Fact(
            agent_id=agent_id,
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
        )
        await store.save_fact(fact)
        query = SemanticQuery(agent_id=agent_id)
        facts = await store.get_facts(query)
        assert len(facts) == 1
        assert facts[0].subject == "Python"

    async def test_fact_merge_on_fingerprint(self, store, agent_id):
        """Save same fact twice → should merge (average confidence)."""
        f1 = Fact(
            agent_id=agent_id,
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
            confidence=0.8,
        )
        await store.save_fact(f1)

        f2 = Fact(
            agent_id=agent_id,
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
            confidence=1.0,
        )
        await store.save_fact(f2)

        query = SemanticQuery(agent_id=agent_id, top_k=100)
        facts = await store.get_facts(query)
        assert len(facts) == 1
        assert facts[0].confidence == pytest.approx(0.9, abs=0.05)

    async def test_delete_fact(self, store, agent_id):
        fact = Fact(
            agent_id=agent_id,
            subject="old",
            predicate=FactRelation.HAS_PROPERTY,
            object="deprecated",
        )
        await store.save_fact(fact)
        result = await store.delete_fact(fact.id)
        assert result is True
        query = SemanticQuery(agent_id=agent_id)
        facts = await store.get_facts(query)
        assert len(facts) == 0

    async def test_update_session(self, store, agent_id, session_id):
        session = Session(id=session_id, agent_id=agent_id)
        await store.save_session(session)
        ended = session.end()
        await store.update_session(ended)
        loaded = await store.get_session(session_id)
        assert loaded is not None
        assert loaded.ended_at is not None
