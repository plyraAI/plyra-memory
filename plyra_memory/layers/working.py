"""Working memory layer — session-scoped, size-bounded, auto-flush."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from plyra_memory.config import MemoryConfig
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    WorkingEntry,
    WorkingMemoryState,
)
from plyra_memory.storage.base import StorageBackend

if TYPE_CHECKING:
    from plyra_memory.layers.episodic import EpisodicLayer

log = logging.getLogger(__name__)


class WorkingMemoryLayer:
    """Session-scoped working memory with bounded capacity."""

    def __init__(self, store: StorageBackend, config: MemoryConfig) -> None:
        self._store = store
        self._config = config

    async def add(self, entry: WorkingEntry) -> WorkingEntry:
        """Add an entry to working memory. Evicts lowest importance if at capacity."""
        state = await self.get(entry.session_id)
        if state.is_full:
            lowest = min(state.entries, key=lambda e: e.importance)
            await self._store.delete_working_entry_by_id(lowest.id)
            log.debug(
                "evicted entry %s (importance=%.2f)",
                lowest.id,
                lowest.importance,
            )

        return await self._store.save_working_entry(entry)

    async def get(self, session_id: str) -> WorkingMemoryState:
        """Get all working memory entries for a session."""
        entries = await self._store.get_working_entries(session_id)
        total_tokens = sum(self._estimate_tokens(e.content) for e in entries)
        return WorkingMemoryState(
            session_id=session_id,
            entries=entries,
            total_tokens=total_tokens,
            max_entries=self._config.working_max_entries,
        )

    async def clear(self, session_id: str) -> int:
        """Clear all working entries for a session. Return count deleted."""
        return await self._store.delete_working_entries(session_id)

    async def flush_to_episodic(
        self,
        session_id: str,
        agent_id: str,
        episodic: EpisodicLayer,
    ) -> list[Episode]:
        """Flush working memory to episodic layer, then clear working memory."""
        state = await self.get(session_id)
        source_to_event = {
            "tool_output": EpisodeEvent.TOOL_RESULT,
            "user": EpisodeEvent.USER_MESSAGE,
            "user_message": EpisodeEvent.USER_MESSAGE,
            "agent_thought": EpisodeEvent.AGENT_RESPONSE,
            "agent": EpisodeEvent.AGENT_RESPONSE,
            "injection": EpisodeEvent.CUSTOM,
        }
        episodes: list[Episode] = []
        for entry in state.entries:
            event = source_to_event.get(entry.source or "", EpisodeEvent.CUSTOM)
            ep = Episode(
                session_id=session_id,
                agent_id=agent_id,
                event=event,
                content=entry.content,
                importance=entry.importance,
                metadata=entry.metadata,
            )
            saved = await episodic.record(ep)
            episodes.append(saved)
        await self.clear(session_id)
        log.info(
            "flushed %d working entries → episodic for session %s",
            len(episodes),
            session_id[:12],
        )
        return episodes

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Simple token estimate: ~1.3 tokens per whitespace-delimited word."""
        return int(len(text.split()) * 1.3)
