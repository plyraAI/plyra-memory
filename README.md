<div align="center">

<img src="https://plyraai.github.io/plyra-guard/assets/logo.png" width="72" height="72" alt="Plyra" />

# plyra-memory

**Persistent structured memory for agentic AI**

[![PyPI](https://img.shields.io/pypi/v/plyra-memory?color=2dd4bf&labelColor=0d1117&label=pypi)](https://pypi.org/project/plyra-memory)
[![Python](https://img.shields.io/pypi/pyversions/plyra-memory?color=2dd4bf&labelColor=0d1117)](https://pypi.org/project/plyra-memory)
[![Status](https://img.shields.io/badge/status-alpha-f59e0b?labelColor=0d1117)](https://github.com/plyraAI/plyra-memory)
[![License](https://img.shields.io/badge/license-Apache%202.0-2dd4bf?labelColor=0d1117)](LICENSE)

[Documentation](https://plyraai.github.io/plyra-memory) · [PyPI](https://pypi.org/project/plyra-memory) · [plyra.ai](https://plyraai.github.io)

</div>

---

AI agents forget everything between runs. Context windows overflow. The same user explains themselves again and again.

`plyra-memory` gives your agent a persistent, three-layer cognitive memory — working, episodic, and semantic — with a hybrid retrieval engine that fuses results across all three, ranked by similarity, recency, and importance.

```python
from plyra_memory import Memory

async with Memory(agent_id="support-agent") as mem:
    await mem.remember("User prefers async Python frameworks")

    ctx = await mem.context_for("what stack does the user prefer?")
    print(ctx.content)
    # → "User prefers async Python frameworks (episodic, 0.94)"
```

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      Your Agent                       │
│  (LangGraph / AutoGen / CrewAI / LangChain / Python)  │
└───────────────────────────┬──────────────────────────┘
                            │ remember / recall / context_for
                            ▼
┌──────────────────────────────────────────────────────┐
│                    plyra-memory                       │
│  working layer · episodic layer · semantic layer      │
│  hybrid retrieval · vector search · context builder   │
└───────────┬──────────────────────────┬───────────────┘
            │                          │
            ▼                          ▼
    SQLite (structured)        ChromaDB (vectors)
```

**Three cognitive layers:**

| Layer | Purpose | Storage |
|-------|---------|---------|
| **Working** | Current session scratchpad | SQLite |
| **Episodic** | Event timeline with vector search | SQLite + ChromaDB |
| **Semantic** | Knowledge graph (subject–predicate–object) | SQLite + ChromaDB |

## Why plyra-memory?

- **Local-first** — SQLite + ChromaDB, no external services required
- **Server-optional** — point `PLYRA_SERVER_URL` at a [`plyra-memory-server`](https://github.com/plyraAI/plyra-memory-server) instance for multi-agent, multi-tenant use
- **Framework agnostic** — adapters for LangGraph, LangChain, AutoGen, CrewAI, OpenAI Agents SDK, plain Python
- **Hybrid retrieval** — fuses vector similarity, recency, and importance scores across all three layers
- **Token-budgeted context** — `context_for()` returns a string that fits your token budget, most relevant content first

## Installation

```bash
pip install plyra-memory
# or with uv
uv add plyra-memory
```

## Quickstart

### 1. Remember and recall

```python
import asyncio
from plyra_memory import Memory

async def main():
    async with Memory(agent_id="my-agent") as mem:
        # Write to memory
        await mem.remember("User is debugging a LangGraph state machine")
        await mem.remember("The bug is in the conditional edge logic")

        # Recall — fused search across all layers
        result = await mem.recall("LangGraph bug")
        for r in result.results:
            print(f"[{r.layer.value}] {r.content}  score={r.score:.2f}")

        # Context — token-budgeted string, ready to inject into a prompt
        ctx = await mem.context_for("help with LangGraph issue")
        print(ctx.content)

asyncio.run(main())
```

### 2. Learn explicit facts

```python
from plyra_memory import Memory, Fact, FactRelation

async with Memory(agent_id="my-agent") as mem:
    await mem.semantic.learn(Fact(
        agent_id=mem.agent_id,
        subject="LangGraph",
        predicate=FactRelation.IS_A,
        object="agent framework",
    ))
```

### 3. Connect to a shared server

```bash
export PLYRA_SERVER_URL=http://localhost:7700
export PLYRA_API_KEY=plm_live_abc123
```

No code changes. The library detects `PLYRA_SERVER_URL` and routes all operations to the server automatically.

### 4. Run a local HTTP server

```bash
plyra-memory serve                       # default: localhost:7700
plyra-memory serve --host 0.0.0.0 --port 7700
plyra-memory stats                       # memory statistics
plyra-memory ping                        # health check
plyra-memory reset --confirm             # delete all local data
```

## Framework Integrations

### LangGraph

```python
from plyra_memory import Memory
from plyra_memory.adapters.langgraph import context_node, remember_node

mem = Memory(agent_id="my-agent")
graph.add_node("remember", lambda s: remember_node(s, memory=mem))
graph.add_node("context",  lambda s: context_node(s, memory=mem))
```

### LangChain

```python
from plyra_memory.adapters.langchain import PlyraMemory

lc_mem = PlyraMemory(mem)
context = await lc_mem.aload_memory_variables({"input": "query"})
```

### AutoGen

```python
from plyra_memory.adapters.autogen import MemoryHook

hook = MemoryHook(mem)
context = await hook.on_message("user message")
```

### CrewAI

```python
from plyra_memory.adapters.crewai import MemoryTool

tool = MemoryTool(mem)
result = tool.run("search query")
```

### OpenAI Agents SDK

```python
from plyra_memory.adapters.openai_agents import get_openai_tools

tools = get_openai_tools(mem)
```

### Plain Python

```python
async with Memory(agent_id="my-agent") as mem:
    await mem.remember("any string")
    result = await mem.recall("any query")
    ctx = await mem.context_for("any prompt fragment")
```

## Configuration

All settings via environment variables (prefix `PLYRA_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PLYRA_STORE_URL` | `~/.plyra/memory.db` | SQLite database path |
| `PLYRA_VECTORS_URL` | `~/.plyra/memory.index` | ChromaDB index path |
| `PLYRA_EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `PLYRA_EMBED_DIM` | `384` | Embedding dimension |
| `PLYRA_SERVER_URL` | _(unset)_ | Remote server URL; enables server mode |
| `PLYRA_API_KEY` | _(unset)_ | API key for remote server |
| `PLYRA_SERVER_PORT` | `7700` | Local HTTP server port |
| `PLYRA_LOG_LEVEL` | `INFO` | Log level |

## Development

```bash
git clone https://github.com/plyraAI/plyra-memory
cd plyra-memory
uv sync --all-extras
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run ruff check .
uv run ruff format .
```

## Project Status

`plyra-memory` is in **alpha** (v0.3.x). Core API is stable; minor breaking changes may occur before v1.0 with deprecation notices.

## Part of the Plyra Suite

| Repo | Description |
|------|-------------|
| [`plyra-guard`](https://github.com/plyraAI/plyra-guard) | Action middleware — policy enforcement for agent tool calls |
| [`plyra-memory`](https://github.com/plyraAI/plyra-memory) | Persistent structured memory for agents |
| [`plyra-memory-server`](https://github.com/plyraAI/plyra-memory-server) | Self-hosted memory server backing plyra-memory |
| [`plyra-keys`](https://github.com/plyraAI/plyra-keys) | Internal key management for the Plyra platform |

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<div align="center">

Built by [Plyra](https://plyraai.github.io) · Infrastructure for agentic AI

</div>
