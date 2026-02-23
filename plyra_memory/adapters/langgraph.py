"""LangGraph adapter – two-node pattern: context_node → remember_node."""

from __future__ import annotations

from typing import Any

from plyra_memory.schema import EpisodeEvent


def _extract_query(state: dict[str, Any]) -> str:
    """Pull the user query from typical LangGraph state shapes."""
    query = state.get("input", "") or state.get("query", "")
    if not query:
        messages = state.get("messages", [])
        if messages:
            last = messages[-1]
            query = last.get("content", "") if isinstance(last, dict) else str(last)
    return query or ""


async def context_node(state: dict[str, Any], *, memory: Any) -> dict[str, Any]:
    """Inject ``memory_context`` into LangGraph state.

    Usage::

        from plyra_memory.adapters.langgraph import context_node

        graph.add_node("ctx", lambda s: context_node(s, memory=mem))
    """
    query = _extract_query(state)
    if not query:
        return state
    ctx = await memory.context_for(query)
    state["memory_context"] = ctx.content
    state["memory_token_count"] = ctx.token_count
    return state


async def remember_node(state: dict[str, Any], *, memory: Any) -> dict[str, Any]:
    """Persist the last message via ``memory.remember()``.

    Usage::

        graph.add_node("rec", lambda s: remember_node(s, memory=mem))
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last = messages[-1]
    content = last.get("content", "") if isinstance(last, dict) else str(last)
    role = last.get("role", "assistant") if isinstance(last, dict) else "assistant"

    event_map = {
        "user": EpisodeEvent.USER_MESSAGE,
        "assistant": EpisodeEvent.AGENT_RESPONSE,
        "tool": EpisodeEvent.TOOL_CALL,
    }
    event = event_map.get(role, EpisodeEvent.AGENT_RESPONSE)

    if content:
        await memory.remember(content, event=event, source=role)
    return state
