"""plyra-memory schema — complete Pydantic v2 models for the memory system."""

from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id() -> str:
    return uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MemoryLayer(StrEnum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class ImportanceLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOISE = "noise"

    @classmethod
    def from_score(cls, score: float) -> ImportanceLevel:
        if score >= 0.9:
            return cls.CRITICAL
        if score >= 0.7:
            return cls.HIGH
        if score >= 0.4:
            return cls.MEDIUM
        if score >= 0.1:
            return cls.LOW
        return cls.NOISE


class EpisodeEvent(StrEnum):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    PLAN_CREATED = "plan_created"
    PLAN_STEP = "plan_step"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MEMORY_PROMOTED = "memory_promoted"
    POLICY_BLOCK = "policy_block"
    SUMMARY = "summary"
    CUSTOM = "custom"


class FactRelation(StrEnum):
    PREFERS = "prefers"
    DISLIKES = "dislikes"
    IS = "is"
    IS_A = "is_a"
    HAS = "has"
    HAS_PROPERTY = "has_property"
    KNOWS = "knows"
    USES = "uses"
    WORKS_ON = "works_on"
    LOCATED_IN = "located_in"
    BELONGS_TO = "belongs_to"
    RELATED_TO = "related_to"
    REQUIRES = "requires"
    LEARNED_FROM = "learned_from"
    CUSTOM = "custom"


class PlyraEnv(StrEnum):
    LOCAL = "local"
    DI = "di"
    STAGING = "staging"
    PREPROD = "preprod"
    PRODUCTION = "production"


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = {"extra": "forbid", "frozen": False}


class _ImmutableBase(_Base):
    model_config = {"extra": "forbid", "frozen": True}


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class Session(_Base):
    id: str = Field(default_factory=_new_id)
    agent_id: str
    user_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    ended_at: datetime | None = None
    framework: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    def end(self) -> Session:
        return self.model_copy(update={"ended_at": _utcnow()})


# ---------------------------------------------------------------------------
# Working Memory
# ---------------------------------------------------------------------------


class WorkingEntry(_Base):
    id: str = Field(default_factory=_new_id)
    session_id: str
    agent_id: str = ""
    content: str = Field(..., min_length=1, max_length=8_000)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    source: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content", mode="before")
    @classmethod
    def _strip_content(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def importance_level(self) -> ImportanceLevel:
        return ImportanceLevel.from_score(self.importance)


class WorkingMemoryState(_Base):
    session_id: str
    entries: list[WorkingEntry] = Field(default_factory=list)
    total_tokens: int = 0
    max_entries: int = 50
    captured_at: datetime = Field(default_factory=_utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_full(self) -> bool:
        return len(self.entries) >= self.max_entries

    @computed_field  # type: ignore[prop-decorator]
    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def sorted_by_importance(self) -> list[WorkingEntry]:
        return sorted(self.entries, key=lambda e: e.importance, reverse=True)


# ---------------------------------------------------------------------------
# Episode (immutable)
# ---------------------------------------------------------------------------


class Episode(_ImmutableBase):
    id: str = Field(default_factory=_new_id)
    session_id: str
    agent_id: str
    event: EpisodeEvent
    content: str = Field(..., min_length=1, max_length=32_000)
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    tool_error: str | None = None
    importance: float = Field(0.5, ge=0.0, le=1.0)
    access_count: int = Field(0, ge=0)
    sequence_num: int = 0
    promoted: bool = False
    promoted_to: str | None = None
    summarized: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def importance_level(self) -> ImportanceLevel:
        return ImportanceLevel.from_score(self.importance)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_tool_event(self) -> bool:
        return self.event in (
            EpisodeEvent.TOOL_CALL,
            EpisodeEvent.TOOL_RESULT,
            EpisodeEvent.TOOL_ERROR,
        )

    @model_validator(mode="after")
    def _validate_tool_name(self) -> Episode:
        if self.is_tool_event and self.tool_name is None:
            raise ValueError(f"tool_name is required when event is {self.event.value}")
        return self


# ---------------------------------------------------------------------------
# Episodic Query
# ---------------------------------------------------------------------------


class EpisodicQuery(_Base):
    session_id: str | None = None
    agent_id: str | None = None
    event_types: list[EpisodeEvent] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)
    since: datetime | None = None
    until: datetime | None = None
    min_importance: float = Field(0.0, ge=0.0, le=1.0)
    text_query: str | None = None
    top_k: int = Field(20, ge=1, le=200)
    limit: int | None = None  # alias for top_k
    include_promoted: bool = True

    @model_validator(mode="after")
    def _sync_limit_and_top_k(self) -> EpisodicQuery:
        if self.limit is not None:
            object.__setattr__(self, "top_k", self.limit)
        return self


# ---------------------------------------------------------------------------
# Fact (semantic memory)
# ---------------------------------------------------------------------------


class Fact(_Base):
    id: str = Field(default_factory=_new_id)
    agent_id: str
    user_id: str | None = None
    subject: str = Field(..., min_length=1, max_length=500)
    predicate: FactRelation
    object: str = Field(..., min_length=1, max_length=2_000)
    content: str = ""
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    access_count: int = Field(0, ge=0)
    created_at: datetime = Field(default_factory=_utcnow)
    last_accessed: datetime = Field(default_factory=_utcnow)
    last_confirmed: datetime = Field(default_factory=_utcnow)
    ttl_days: int | None = None
    source_episode_id: str | None = None
    promoted_from: str | None = None
    fingerprint: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _build_derived_fields(self) -> Fact:
        if not self.content:
            object.__setattr__(
                self,
                "content",
                f"{self.subject} {self.predicate.value} {self.object}",
            )
        raw = f"{self.agent_id}:{self.subject.lower()}:{self.predicate.value}"
        object.__setattr__(
            self,
            "fingerprint",
            hashlib.sha256(raw.encode()).hexdigest()[:16],
        )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def importance_level(self) -> ImportanceLevel:
        return ImportanceLevel.from_score(self.importance)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_expired(self) -> bool:
        if self.ttl_days is None:
            return False
        return (_utcnow() - self.created_at).days > self.ttl_days

    @computed_field  # type: ignore[prop-decorator]
    @property
    def decay_score(self) -> float:
        days = (_utcnow() - self.last_accessed).total_seconds() / 86_400
        return max(0.01, min(1.0, self.confidence * math.exp(-0.05 * days)))


# ---------------------------------------------------------------------------
# Semantic Query
# ---------------------------------------------------------------------------


class SemanticQuery(_Base):
    agent_id: str | None = None
    user_id: str | None = None
    subjects: list[str] = Field(default_factory=list)
    predicates: list[FactRelation] = Field(default_factory=list)
    text_query: str | None = None
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    min_decay_score: float = Field(0.0, ge=0.0, le=1.0)
    include_expired: bool = False
    top_k: int = Field(10, ge=1, le=100)
    limit: int | None = None  # alias for top_k

    @model_validator(mode="after")
    def _sync_limit_and_top_k(self) -> SemanticQuery:
        if self.limit is not None:
            object.__setattr__(self, "top_k", self.limit)
        return self


# ---------------------------------------------------------------------------
# Recall / Retrieval
# ---------------------------------------------------------------------------


class RecallRequest(_Base):
    query: str = Field(..., min_length=1)
    session_id: str | None = None
    agent_id: str | None = None
    layers: list[MemoryLayer] = Field(default_factory=lambda: list(MemoryLayer))
    top_k: int = Field(10, ge=1, le=100)
    similarity_weight: float = Field(0.5, ge=0.0, le=1.0)
    recency_weight: float = Field(0.3, ge=0.0, le=1.0)
    importance_weight: float = Field(0.2, ge=0.0, le=1.0)
    min_score: float = Field(0.0, ge=0.0, le=1.0)
    event_types: list[EpisodeEvent] = Field(default_factory=list)
    predicates: list[FactRelation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> RecallRequest:
        total = self.similarity_weight + self.recency_weight + self.importance_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Fusion weights must sum to 1.0. Got {total:.3f}. "
                "Adjust similarity_weight + recency_weight + importance_weight."
            )
        return self


class RankedMemory(_ImmutableBase):
    id: str
    layer: MemoryLayer
    content: str
    score: float = Field(..., ge=0.0, le=1.0)
    similarity: float = Field(0.0, ge=0.0, le=1.0)
    recency: float = Field(0.0, ge=0.0, le=1.0)
    importance: float = Field(0.0, ge=0.0, le=1.0)
    created_at: datetime
    source_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecallResult(_ImmutableBase):
    query: str
    results: list[RankedMemory] = Field(default_factory=list)
    total_found: int = 0
    layers_searched: list[MemoryLayer] = Field(default_factory=list)
    cache_hit: bool = False
    latency_ms: float = 0.0
    retrieved_at: datetime = Field(default_factory=_utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def working_results(self) -> list[RankedMemory]:
        return [r for r in self.results if r.layer == MemoryLayer.WORKING]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def episodic_results(self) -> list[RankedMemory]:
        return [r for r in self.results if r.layer == MemoryLayer.EPISODIC]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def semantic_results(self) -> list[RankedMemory]:
        return [r for r in self.results if r.layer == MemoryLayer.SEMANTIC]


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


class ContextResult(_ImmutableBase):
    query: str
    content: str
    token_count: int
    token_budget: int
    memories_used: int
    cache_hit: bool = False
    latency_ms: float = 0.0
    retrieved_at: datetime = Field(default_factory=_utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def budget_used_pct(self) -> float:
        if self.token_budget == 0:
            return 0.0
        return round(self.token_count / self.token_budget * 100, 1)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthStatus(_ImmutableBase):
    status: Literal["ok", "degraded", "down"] = "ok"
    version: str = "0.1.0"
    env: PlyraEnv = PlyraEnv.LOCAL
    store_path: str = ""
    vectors_path: str = ""
    embed_model: str = ""
    uptime_seconds: float = 0.0
    session_count: int = 0
    memory_count: int = 0
    checked_at: datetime = Field(default_factory=_utcnow)
