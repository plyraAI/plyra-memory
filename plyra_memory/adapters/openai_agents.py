"""OpenAI Agents SDK adapter – function tools for memory."""

from __future__ import annotations

from typing import Any

from plyra_memory.schema import EpisodeEvent


async def context_tool(query: str, *, memory: Any) -> str:
    """Read from memory. Returns context string."""
    ctx = await memory.context_for(query)
    return ctx.content


async def remember_tool(
    content: str,
    *,
    memory: Any,
    source: str = "agent",
) -> str:
    """Write to all memory layers via ``memory.remember``."""
    result = await memory.remember(
        content,
        event=EpisodeEvent.AGENT_RESPONSE,
        source=source,
    )
    ep = result.get("episodic")
    return f"Stored: {ep.content[:80] if ep else content[:80]}"


def get_openai_tools(memory: Any) -> list[dict[str, Any]]:
    """Return OpenAI function-calling tool definitions.

    Usage::

        tools = get_openai_tools(mem)
        # Pass tools to OpenAI API or Agents SDK
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "memory_context",
                "description": (
                    "Read relevant context from the agent's cognitive memory."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query to search memory.",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "memory_remember",
                "description": (
                    "Write information to all three memory layers "
                    "(working, episodic, semantic)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to store in memory.",
                        },
                        "source": {
                            "type": "string",
                            "description": "Source label (default: 'agent').",
                            "default": "agent",
                        },
                    },
                    "required": ["content"],
                },
            },
        },
    ]


def create_memory_tools(memory: Any) -> list[Any]:
    """Return callable tools bound to memory for Agent SDK usage."""
    import functools

    return [
        functools.partial(memory_recall, memory=memory),
        functools.partial(memory_remember, memory=memory),
    ]


memory_recall = context_tool
memory_remember = remember_tool
