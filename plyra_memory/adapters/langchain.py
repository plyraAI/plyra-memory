"""LangChain adapter – BaseMemory-compatible wrapper."""

from __future__ import annotations

from typing import Any

from plyra_memory.schema import EpisodeEvent


class PlyraMemory:
    """LangChain-compatible memory using ``context_for`` + ``remember``.

    Usage::

        lc_mem = PlyraMemory(memory)
        ctx = await lc_mem.aload_memory_variables({"input": "hello"})
        await lc_mem.asave_context({"input": "hi"}, {"output": "hey!"})
    """

    memory_key: str = "memory_context"

    def __init__(self, memory: Any, memory_key: str = "memory_context") -> None:
        self._memory = memory
        self.memory_key = memory_key

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    # -- read ---------------------------------------------------------------

    async def aload_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        """Load memory context for the given inputs."""
        query = inputs.get("input", "") or inputs.get("query", "")
        if not query:
            return {self.memory_key: ""}
        ctx = await self._memory.context_for(query)
        return {self.memory_key: ctx.content}

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        """Sync wrapper — requires a running event loop."""
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            self.aload_memory_variables(inputs)
        )

    # -- write --------------------------------------------------------------

    async def asave_context(
        self, inputs: dict[str, Any], outputs: dict[str, str]
    ) -> None:
        """Persist both sides of a conversation turn via ``remember``."""
        user_msg = inputs.get("input", "")
        if user_msg:
            await self._memory.remember(
                user_msg, event=EpisodeEvent.USER_MESSAGE, source="user"
            )

        ai_msg = outputs.get("output", "") or outputs.get("response", "")
        if ai_msg:
            await self._memory.remember(
                ai_msg, event=EpisodeEvent.AGENT_RESPONSE, source="agent"
            )

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """Sync wrapper."""
        import asyncio

        asyncio.get_event_loop().run_until_complete(self.asave_context(inputs, outputs))

    # -- clear --------------------------------------------------------------

    async def aclear(self) -> None:
        """Clear working memory for current session."""
        await self._memory.working.clear(self._memory.session_id)

    def clear(self) -> None:
        """Sync wrapper."""
        import asyncio

        asyncio.get_event_loop().run_until_complete(self.aclear())
