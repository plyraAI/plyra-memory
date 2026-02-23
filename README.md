# plyra-memory

**Typed, three-layer cognitive memory for AI agents.**

> v0.1.0 — Local-only: SQLite + ChromaDB + sentence-transformers

---

## Overview

plyra-memory gives your AI agent a persistent, structured memory with three cognitive layers:

| Layer | Purpose | Storage |
|-------|---------|---------|
| **Working** | Current session scratchpad | SQLite |
| **Episodic** | Event timeline with vector search | SQLite + ChromaDB |
| **Semantic** | Knowledge graph (subject–predicate–object) | SQLite + ChromaDB |

A hybrid retrieval engine fuses results across all three layers, ranking by similarity, recency, and importance.

## Quick Start

### Install

```bash
pip install plyra-memory
# or with uv
uv add plyra-memory
```

### Python API

```python
import asyncio
from plyra_memory import Memory, WorkingEntry, Episode, EpisodeEvent, Fact, FactRelation

async def main():
    async with Memory(agent_id="my-agent") as mem:
        # Working memory — session scratchpad
        await mem.working.add(WorkingEntry(
            session_id=mem.session_id,
            agent_id=mem.agent_id,
            content="User is debugging LangGraph",
        ))

        # Episodic memory — record events
        await mem.episodic.record(Episode(
            session_id=mem.session_id,
            agent_id=mem.agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="How do I add memory to my agent?",
        ))

        # Semantic memory — learn facts
        await mem.semantic.learn(Fact(
            agent_id=mem.agent_id,
            subject="LangGraph",
            predicate=FactRelation.IS_A,
            object="agent framework",
        ))

        # Recall — fused retrieval across all layers
        result = await mem.recall("LangGraph memory")
        for r in result.results:
            print(f"[{r.layer.value}] {r.content} (score={r.score:.2f})")

        # Context — token-budgeted context string
        ctx = await mem.context_for("help with LangGraph")
        print(ctx.content)

asyncio.run(main())
```

### HTTP Server

```bash
# Start the server
plyra-memory serve

# Or with options
plyra-memory serve --host 0.0.0.0 --port 7700 --reload
```

### CLI Commands

```bash
plyra-memory --help        # Show all commands
plyra-memory serve         # Start HTTP server
plyra-memory ping          # Check server health
plyra-memory stats         # Show memory statistics
plyra-memory reset --confirm  # Delete all local data
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Server info |
| GET | `/health` | Health check |
| GET | `/stats` | Memory statistics |
| POST | `/working` | Add working memory entry |
| GET | `/working/{sid}` | Get working entries |
| DELETE | `/working/{sid}` | Clear working entries |
| POST | `/episodes` | Query episodes |
| GET | `/episodes/{id}` | Get episode by ID |
| PUT | `/facts` | Learn a fact |
| DELETE | `/facts/{id}` | Forget a fact |
| POST | `/recall` | Hybrid recall |
| POST | `/context` | Context builder |

## Framework Adapters

### LangGraph

```python
from plyra_memory import Memory
from plyra_memory.adapters.langgraph import context_node, remember_node

mem = Memory()
graph.add_node("ctx", lambda s: context_node(s, memory=mem))
graph.add_node("rec", lambda s: remember_node(s, memory=mem))
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

## Configuration

Configuration via environment variables (prefix `PLYRA_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PLYRA_STORE_URL` | `~/.plyra/memory.db` | SQLite database path |
| `PLYRA_VECTORS_URL` | `~/.plyra/memory.index` | ChromaDB index path |
| `PLYRA_EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `PLYRA_EMBED_DIM` | `384` | Embedding dimension |
| `PLYRA_LOG_LEVEL` | `INFO` | Log level |
| `PLYRA_SERVER_PORT` | `7700` | HTTP server port |
| `PLYRA_ENV` | `development` | Environment name |

## Architecture

```
┌──────────────┐
│   Memory     │  ← Public API (async context manager)
├──────────────┤
│  Retrieval   │  ← HybridRetrieval + SemanticCache
├──────┬───┬───┤
│ Work │Epi│Sem│  ← Three cognitive layers
├──────┴───┴───┤
│Storage│Vector│  ← SQLite + ChromaDB
├───────┴──────┤
│  Embedder    │  ← sentence-transformers
└──────────────┘
```

## Development

```bash
# Clone & setup
git clone https://github.com/your-org/plyra-memory.git
cd plyra-memory
uv sync --all-extras

# Lint
uv run ruff check .
uv run ruff format .

# Test
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# Run server
uv run plyra-memory serve
```

## Docker

```bash
docker compose up
```

## License

MIT
