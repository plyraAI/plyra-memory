"""
plyra-memory chatbot — terminal chatbot with persistent memory and Groq LLM.

Uses plyra-memory's three-layer cognitive memory (working / episodic / semantic)
and Groq's OpenAI-compatible API for chat completions.

Usage:
    python examples/chatbot.py --agent-id my-agent
    python examples/chatbot.py --agent-id my-agent --reset

Environment:
    GROQ_API_KEY   — required, your Groq API key

Special commands:
    memory  — print current memory state
    quit    — exit the chatbot
"""

from __future__ import annotations

# Inject OS certificate store before any network calls (corporate proxy fix)
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

import argparse
import asyncio
import os
import shutil
import ssl
import sys
from pathlib import Path

import httpx
from openai import OpenAI

from plyra_memory import (
    EpisodeEvent,
    Memory,
    MemoryConfig,
)
from plyra_memory.schema import (
    EpisodicQuery,
    SemanticQuery,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_DB = str(Path.home() / ".plyra" / "chatbot.db")
DEFAULT_VEC = str(Path.home() / ".plyra" / "chatbot.index")
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """\
You are a helpful AI assistant with persistent cognitive memory.
You have access to memories from previous conversations.
When memories are provided as context, use them naturally in your responses.
If you remember the user's name, preferences, or projects — mention them
naturally without being prompted. Be concise, warm, and helpful.
"""


# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------


async def build_memory_context(memory: Memory, user_message: str) -> str:
    """Build a memory context string for the LLM prompt."""
    ctx = await memory.context_for(user_message, token_budget=512)
    return ctx.content


async def show_memory_state(memory: Memory) -> None:
    """Print current memory state for debugging."""
    assert memory._store is not None

    counts = await memory._store.count_memories()
    print("\n  ── Memory State ──")
    print(f"  Working:  {counts.get('working', 0)} entries")
    print(f"  Episodic: {counts.get('episodic', 0)} episodes")
    print(f"  Semantic: {counts.get('semantic', 0)} facts")

    # Show semantic facts
    facts = await memory.semantic.query(
        SemanticQuery(agent_id=memory.agent_id, top_k=20)
    )
    if facts:
        print("\n  ── Semantic Facts ──")
        for f in facts:
            print(
                f"  • {f.subject} [{f.predicate.value}] "
                f"{f.object} (conf={f.confidence:.2f})"
            )

    # Show recent episodes
    episodes = await memory.episodic.query(
        EpisodicQuery(agent_id=memory.agent_id, top_k=5)
    )
    if episodes:
        print(f"\n  ── Recent Episodes (last {len(episodes)}) ──")
        for ep in episodes[-3:]:
            preview = ep.content[:80].replace("\n", " ")
            print(f"  • [{ep.event.value}] {preview}...")

    print()


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def get_llm_client() -> OpenAI:
    """Create an OpenAI client pointing at Groq."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Set it with: $env:GROQ_API_KEY = 'gsk_...'")
        sys.exit(1)

    # Use default SSL context (truststore-injected) for corporate proxies
    ctx = ssl.create_default_context()
    http_client = httpx.Client(verify=ctx)

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        http_client=http_client,
    )


def call_llm(
    client: OpenAI,
    conversation: list[dict[str, str]],
    memory_context: str,
) -> str:
    """Call Groq LLM with memory context injected into the system prompt."""
    system = SYSTEM_PROMPT
    if memory_context:
        system += (
            "\n\n--- MEMORIES FROM PREVIOUS CONVERSATIONS ---\n"
            + memory_context
            + "\n--- END MEMORIES ---"
        )

    messages = [{"role": "system", "content": system}] + conversation

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


async def main() -> None:
    parser = argparse.ArgumentParser(description="plyra-memory chatbot with Groq LLM")
    parser.add_argument(
        "--agent-id",
        default="chatbot-agent",
        help="Agent ID for memory persistence (default: chatbot-agent)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset memory (delete DB and vectors) before starting",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"SQLite database path (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--vectors",
        default=DEFAULT_VEC,
        help=f"ChromaDB vectors path (default: {DEFAULT_VEC})",
    )
    args = parser.parse_args()

    # Reset if requested
    if args.reset:
        for p in [Path(args.db), Path(args.vectors)]:
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        print("  [RESET] Memory cleared.\n")

    config = MemoryConfig(
        store_url=args.db,
        vectors_url=args.vectors,
        cache_enabled=False,
    )

    client = get_llm_client()
    conversation: list[dict[str, str]] = []

    print("╔══════════════════════════════════════╗")
    print("║  plyra-memory chatbot (Groq LLM)     ║")
    print("║  Commands: memory | quit              ║")
    print("╚══════════════════════════════════════╝")
    print()

    async with Memory(config=config, agent_id=args.agent_id) as memory:
        print(f"  Agent: {args.agent_id}")
        print(f"  Session: {memory.session_id[:12]}...")

        counts = await memory._store.count_memories()
        total = sum(counts.values())
        if total > 0:
            print(
                f"  Loaded {total} memories "
                f"(W:{counts['working']} "
                f"E:{counts['episodic']} "
                f"S:{counts['semantic']})"
            )
        print()

        while True:
            try:
                user_input = input("you › ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                # Flush working memory to episodic before quitting
                episodes = await memory.flush()
                print(f"\n  [FLUSH] {len(episodes)} entries moved to episodic memory.")
                print("Goodbye!")
                break

            if user_input.lower() == "memory":
                await show_memory_state(memory)
                continue

            # 1. Remember the user message (writes to all 3 layers + extracts facts)
            result = await memory.remember(
                user_input,
                importance=0.6,
                source="user",
                event=EpisodeEvent.USER_MESSAGE,
            )
            facts = result["facts"]
            if facts:
                names = [f"{f.subject}→{f.predicate.value}→{f.object}" for f in facts]
                print(f"  [FACTS] Stored: {', '.join(names)}")

            # 2. Retrieve memory context
            memory_context = await build_memory_context(memory, user_input)
            if memory_context:
                print(f"  [MEMORY] retrieved context ({len(memory_context)} chars)")

            # 3. Call LLM with memory context
            conversation.append({"role": "user", "content": user_input})
            try:
                response = call_llm(client, conversation, memory_context)
            except Exception as exc:
                print(f"  [ERROR] LLM call failed: {exc}")
                conversation.pop()
                continue

            conversation.append({"role": "assistant", "content": response})
            print(f"\nassistant › {response}\n")

            # 4. Remember assistant response
            await memory.remember(
                response,
                importance=0.7,
                source="assistant",
                event=EpisodeEvent.AGENT_RESPONSE,
            )


if __name__ == "__main__":
    asyncio.run(main())
