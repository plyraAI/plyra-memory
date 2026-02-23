"""CrewAI adapter – Tool wrapper for memory operations."""

from __future__ import annotations

from typing import Any

from plyra_memory.schema import EpisodeEvent


class MemoryTool:
    """CrewAI-compatible tool using ``context_for`` + ``remember``.

    Usage::

        tool = MemoryTool(memory)
        ctx  = await tool.arun("what files?")
        await tool.aremember("user likes Python")
    """

    name: str = "plyra_memory"
    description: str = (
        "Read and write cognitive memory. "
        "Input: a natural language query string. "
        "Output: relevant context from memory."
    )

    def __init__(self, memory: Any) -> None:
        self._memory = memory

    # -- read ---------------------------------------------------------------

    async def arun(self, query: str) -> str:
        """Return memory context for *query*."""
        ctx = await self._memory.context_for(query)
        return ctx.content

    def run(self, query: str) -> str:
        """Sync wrapper for CrewAI tools."""
        import asyncio

        return asyncio.get_event_loop().run_until_complete(self.arun(query))

    # -- write --------------------------------------------------------------

    async def aremember(self, content: str, **kwargs: Any) -> str:
        """Persist *content* via ``memory.remember``."""
        result = await self._memory.remember(
            content,
            event=EpisodeEvent.AGENT_RESPONSE,
            source="crewai",
        )
        ep = result.get("episodic")
        return f"Stored: {ep.content[:80] if ep else content[:80]}"
