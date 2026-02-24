# Quickstart

Get persistent memory working in your agent in 5 minutes.

## Install

```bash
pip install plyra-memory
```

## Basic usage

```python
import asyncio
from plyra_memory import Memory

async def main():
    async with Memory(agent_id="my-agent") as memory:

        # Write to memory
        await memory.remember("my name is Alex")
        await memory.remember("I prefer Python async frameworks")
        await memory.remember("I'm building a LangGraph agent")

        # Read from memory — prompt-ready context string
        ctx = await memory.context_for("what is the user working on?")
        print(ctx.content)
        # → "user is Alex, prefers Python async frameworks,
        #    building a LangGraph agent"

asyncio.run(main())
```

## Cross-session persistence

Memory persists across restarts automatically.
Run this twice — the second run recalls what the first stored.

```python
import asyncio
from plyra_memory import Memory

async def session():
    # Same agent_id = same memory across runs
    async with Memory(agent_id="my-agent") as memory:
        user_input = input("you: ")
        ctx = await memory.context_for(user_input)

        # Inject context into your LLM prompt
        prompt = f"{ctx.content}\n\nUser: {user_input}" if ctx.content else user_input

        # ... call your LLM here ...
        response = "I remember you from last time!"

        # Store the exchange
        await memory.remember(user_input, source="user_message")
        await memory.remember(response, source="agent_response")
        print(f"agent: {response}")

asyncio.run(session())
```

## With LLM fact extraction

Pass an Anthropic or OpenAI client to extract structured facts automatically:

```python
import anthropic
from plyra_memory import Memory

client = anthropic.Anthropic()
memory = Memory.with_anthropic(api_key=client.api_key, agent_id="my-agent")

async with memory:
    # "my name is Alex" → fact: user IS Alex (confidence 0.95)
    # "I prefer TypeScript" → fact: user PREFERS TypeScript
    # "I'm building a SaaS" → fact: user WORKS_ON SaaS
    await memory.remember("my name is Alex, I prefer TypeScript")
```

See [LLM fact extraction](extraction/llm.md) for full details.

## With a framework

=== "LangGraph"

    ```python
    from plyra_memory import Memory
    from plyra_memory.adapters.langgraph import create_memory_nodes
    from langgraph.graph import StateGraph
    
    # Needs dummy values to parse correctly for quickstart stub
    State = dict
    your_llm_node = lambda state: state

    memory = Memory(agent_id="my-agent")
    ctx_node, rec_node = create_memory_nodes(memory)

    graph = StateGraph(State)
    graph.add_node("memory_in",  ctx_node)   # reads memory before LLM
    graph.add_node("llm",        your_llm_node)
    graph.add_node("memory_out", rec_node)   # writes memory after LLM
    graph.add_edge("memory_in",  "llm")
    graph.add_edge("llm",        "memory_out")
    ```

=== "AutoGen"

    ```python
    from plyra_memory import Memory
    from plyra_memory.adapters.autogen import MemoryHook

    memory = Memory(agent_id="my-agent")
    hook = MemoryHook(memory)

    # agent.register_hook("process_all_messages_before_reply", hook.before_reply)
    # agent.register_hook("process_message_before_send",       hook.before_send)
    ```

=== "LangChain"

    ```python
    from plyra_memory import Memory
    from plyra_memory.adapters.langchain import PlyraMemory
    # from langchain.chains import ConversationChain

    memory = Memory(agent_id="my-agent")
    # chain = ConversationChain(llm=your_llm, memory=PlyraMemory(memory))
    ```

=== "CrewAI"

    ```python
    from plyra_memory import Memory
    from plyra_memory.adapters.crewai import MemoryTool
    # from crewai import Agent

    memory = Memory(agent_id="my-agent")
    # agent = Agent(role="Assistant", tools=[MemoryTool(memory)])
    ```

=== "OpenAI Agents"

    ```python
    from plyra_memory import Memory
    from plyra_memory.adapters.openai_agents import create_memory_tools

    memory = Memory(agent_id="my-agent")
    tools = create_memory_tools(memory)
    # Pass tools to your OpenAI function calling setup
    ```

## Server mode

Connect to a shared server — two env vars, no code changes:

```bash
export PLYRA_SERVER_URL=http://localhost:7700
export PLYRA_API_KEY=plm_live_abc123...
```

```python
# Identical code — routes to server automatically
async def test():
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("user prefers Python")
```

See [server mode](server/index.md) for full setup.

## What's stored where

| Layer | What | How long |
|-------|------|----------|
| Working | Current session messages | Session only |
| Episodic | All exchanges, all sessions | Forever, vector-indexed |
| Semantic | Extracted facts (name, prefs, project) | Forever, decay model |

→ [Concepts](concepts.md) explains each layer in depth.

---

**Next:** [Concepts →](concepts.md) or jump to your [framework adapter →](adapters/index.md)
