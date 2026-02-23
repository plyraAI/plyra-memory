"""Abstract base class for storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from plyra_memory.schema import (
    Episode,
    EpisodicQuery,
    Fact,
    SemanticQuery,
    Session,
    WorkingEntry,
)


class StorageBackend(ABC):
    """Abstract async storage backend for plyra-memory."""

    @abstractmethod
    async def initialize(self) -> None:
        """Create tables / schema."""

    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""

    # -- Sessions --

    @abstractmethod
    async def save_session(self, session: Session) -> Session: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def update_session(self, session: Session) -> Session: ...

    # -- Working entries --

    @abstractmethod
    async def save_working_entry(self, entry: WorkingEntry) -> WorkingEntry: ...

    @abstractmethod
    async def get_working_entries(self, session_id: str) -> list[WorkingEntry]: ...

    @abstractmethod
    async def delete_working_entries(self, session_id: str) -> int:
        """Delete all working entries for a session. Return count deleted."""

    # -- Episodes --

    @abstractmethod
    async def save_episode(self, episode: Episode) -> Episode: ...

    @abstractmethod
    async def get_episodes(self, query: EpisodicQuery) -> list[Episode]: ...

    @abstractmethod
    async def get_episode(self, episode_id: str) -> Episode | None: ...

    @abstractmethod
    async def increment_episode_access(self, episode_id: str) -> int:
        """Increment access_count, return new value."""

    @abstractmethod
    async def mark_episode_promoted(self, episode_id: str, fact_id: str) -> None: ...

    # -- Facts --

    @abstractmethod
    async def save_fact(self, fact: Fact) -> Fact:
        """Upsert on fingerprint collision."""

    @abstractmethod
    async def get_facts(self, query: SemanticQuery) -> list[Fact]: ...

    @abstractmethod
    async def get_fact(self, fact_id: str) -> Fact | None: ...

    @abstractmethod
    async def get_fact_by_fingerprint(self, fingerprint: str) -> Fact | None: ...

    @abstractmethod
    async def update_fact_access(self, fact_id: str) -> None:
        """Update last_accessed timestamp."""

    @abstractmethod
    async def delete_fact(self, fact_id: str) -> bool: ...

    @abstractmethod
    async def count_memories(self) -> dict[str, int]:
        """Return {working: N, episodic: N, semantic: N}."""

    # -- Working entry deletion by id (for eviction) --

    @abstractmethod
    async def delete_working_entry_by_id(self, entry_id: str) -> bool: ...
