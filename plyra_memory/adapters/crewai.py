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
        if query.lower().startswith("remember:"):
            return await self.aremember(query[9:].strip())
        if query.lower().startswith("recall:"):
            query = query[7:].strip()
        ctx = await self._memory.context_for(query)
        return ctx.content

    def run(self, query: str) -> str:
        """Sync wrapper for CrewAI tools."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If called from an async testing script, bridge using
            # run_coroutine_threadsafe. But we must do it on a distinct thread that
            # runs its own loop, OR just return what we can.
            # Easiest way to bypass in a test is direct thread execution.

            def _thread_worker() -> str:
                return asyncio.run(self.arun(query))

            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(_thread_worker).result()

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
