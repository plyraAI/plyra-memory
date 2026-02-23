"""Unit tests for plyra_memory.schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    Fact,
    FactRelation,
    ImportanceLevel,
    MemoryLayer,
    RecallRequest,
    Session,
    WorkingEntry,
    WorkingMemoryState,
    _new_id,
)


class TestNewId:
    def test_returns_string(self):
        assert isinstance(_new_id(), str)

    def test_unique(self):
        ids = {_new_id() for _ in range(100)}
        assert len(ids) == 100


class TestSession:
    def test_create_session(self):
        s = Session(id="s1", agent_id="a1")
        assert s.id == "s1"
        assert s.created_at is not None
        assert s.ended_at is None

    def test_end_session(self):
        s = Session(id="s1", agent_id="a1")
        ended = s.end()
        assert ended.ended_at is not None
        assert ended.id == s.id


class TestWorkingEntry:
    def test_defaults(self):
        we = WorkingEntry(session_id="s1", agent_id="a1", content="hello")
        assert we.id is not None
        assert we.importance_level == ImportanceLevel.MEDIUM
        assert we.source is None

    def test_custom_importance(self):
        we = WorkingEntry(
            session_id="s1",
            agent_id="a1",
            content="critical",
            importance=0.95,
        )
        assert we.importance_level == ImportanceLevel.CRITICAL


class TestWorkingMemoryState:
    def test_empty(self):
        state = WorkingMemoryState(session_id="s1", entries=[])
        assert state.entry_count == 0
        assert state.total_tokens == 0

    def test_with_entries(self):
        entries = [
            WorkingEntry(session_id="s1", agent_id="a1", content="hi"),
            WorkingEntry(session_id="s1", agent_id="a1", content="there"),
        ]
        state = WorkingMemoryState(session_id="s1", entries=entries)
        assert state.entry_count == 2


class TestEpisode:
    def test_frozen(self):
        ep = Episode(
            session_id="s1",
            agent_id="a1",
            event=EpisodeEvent.USER_MESSAGE,
            content="test",
        )
        with pytest.raises(ValidationError):
            ep.content = "changed"

    def test_tool_event_requires_tool_name(self):
        """TOOL_CALL and TOOL_RESULT require tool_name."""
        with pytest.raises(ValidationError):
            Episode(
                session_id="s1",
                agent_id="a1",
                event=EpisodeEvent.TOOL_CALL,
                content="test",
            )

    def test_tool_event_with_tool_name(self):
        ep = Episode(
            session_id="s1",
            agent_id="a1",
            event=EpisodeEvent.TOOL_CALL,
            content="test",
            tool_name="my_tool",
        )
        assert ep.tool_name == "my_tool"


class TestFact:
    def test_fingerprint_computed(self):
        f = Fact(
            agent_id="a1",
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
        )
        assert f.fingerprint is not None
        assert len(f.fingerprint) == 16

    def test_fingerprint_always_recomputed(self):
        """Even if fingerprint is passed, it gets overridden."""
        f = Fact(
            agent_id="a1",
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
            fingerprint="should_be_overridden",
        )
        assert f.fingerprint != "should_be_overridden"

    def test_content_auto_generated(self):
        f = Fact(
            agent_id="a1",
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
        )
        assert "Python" in f.content
        assert "language" in f.content

    def test_same_inputs_same_fingerprint(self):
        f1 = Fact(
            agent_id="a1",
            subject="Python",
            predicate=FactRelation.IS_A,
            object="language",
        )
        f2 = Fact(
            agent_id="a1",
            subject="Python",
            predicate=FactRelation.IS_A,
            object="different",
        )
        # fingerprint uses agent:subject:predicate
        assert f1.fingerprint == f2.fingerprint


class TestRecallRequest:
    def test_default_weights(self):
        req = RecallRequest(
            query="test",
            session_id="s1",
            agent_id="a1",
        )
        total = req.similarity_weight + req.recency_weight + req.importance_weight
        assert abs(total - 1.0) < 0.02

    def test_bad_weights_rejected(self):
        with pytest.raises(ValidationError):
            RecallRequest(
                query="test",
                session_id="s1",
                agent_id="a1",
                similarity_weight=0.5,
                recency_weight=0.5,
                importance_weight=0.5,  # sum = 1.5
            )


class TestMemoryLayer:
    def test_values(self):
        assert MemoryLayer.WORKING.value == "working"
        assert MemoryLayer.EPISODIC.value == "episodic"
        assert MemoryLayer.SEMANTIC.value == "semantic"
