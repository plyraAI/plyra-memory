"""AutoGen adapter – MemoryHook for agent pipelines."""

from __future__ import annotations

from typing import Any

from plyra_memory.schema import EpisodeEvent


class MemoryHook:
    """Hook for AutoGen agents — ``context_for`` + ``remember``.

    Usage::

        hook = MemoryHook(memory)
        ctx  = await hook.on_message("what file?")
        await hook.on_response("Use main.py")
    """

    def __init__(self, memory: Any) -> None:
        self._memory = memory

    async def on_message(self, message: str, **kwargs: Any) -> dict[str, Any]:
        """Return memory context for an incoming message."""
        ctx = await self._memory.context_for(message)
        return {
            "memory_context": ctx.content,
            "token_count": ctx.token_count,
            "memories_used": ctx.memories_used,
        }

    async def on_response(self, response: str, **kwargs: Any) -> None:
        """Persist an agent response via ``memory.remember``."""
        await self._memory.remember(
            response,
            event=EpisodeEvent.AGENT_RESPONSE,
            source="agent",
        )

    async def on_tool_call(self, tool_name: str, result: str, **kwargs: Any) -> None:
        """Persist a tool result via ``memory.remember``."""
        await self._memory.remember(
            f"[{tool_name}] {result}",
            event=EpisodeEvent.TOOL_RESULT,
            tool_name=tool_name,
            source="tool",
        )
