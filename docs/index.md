---
hide:
  - navigation
  - toc
---

<div class="plyra-hero">
  <h1>plyra-memory</h1>
  <p class="tagline">Persistent structured memory for AI agents.<br>
  Local-first. Server-optional. Framework-agnostic.</p>
</div>

```bash
pip install plyra-memory
```

```python
from plyra_memory import Memory

async with Memory(agent_id="my-agent") as memory:
    await memory.remember("user prefers TypeScript and hates verbose config")
    ctx = await memory.context_for("what stack does the user like?")
    print(ctx.content)
    # → "User prefers TypeScript. Dislikes verbose configuration."
```

<div class="plyra-grid">
  <div class="plyra-card">
    <h3>Three Memory Layers</h3>
    <p>Working → Episodic → Semantic. Automatic promotion. LLM-powered extraction.</p>
  </div>
  <div class="plyra-card">
    <h3>Framework-Agnostic</h3>
    <p>LangGraph, AutoGen, LangChain, CrewAI, OpenAI Agents, plain Python.</p>
  </div>
  <div class="plyra-card">
    <h3>Local-First</h3>
    <p>Zero config. SQLite + ChromaDB on disk. Add a server URL to go multi-agent.</p>
  </div>
  <div class="plyra-card">
    <h3>Production-Grade</h3>
    <p>Server mode with workspace isolation. Azure-ready Docker image.</p>
  </div>
</div>

## Architecture

```mermaid
graph LR
  A["Your Agent"] --> B["Memory()"]
  B --> C{Mode?}
  C -->|"No env vars"| D["Local Mode"]
  C -->|"PLYRA_SERVER_URL set"| E["Server Mode"]
  D --> F["SQLite\n~/.plyra/memory.db"]
  D --> G["ChromaDB\n~/.plyra/vectors/"]
  E --> H["plyra-memory-server\nAzure / Docker"]
  H --> I["Shared SQLite\n/data/memory.db"]
  H --> J["Shared Vectors\n/data/memory.index"]

  style B fill:#818cf8,color:#0d1117
  style D fill:#161b22,color:#e6edf3
  style E fill:#161b22,color:#e6edf3
  style H fill:#2dd4bf,color:#0d1117
```

## Three-Layer Memory Model

```mermaid
graph TD
  A["remember('user prefers Python')"] --> B["Working Memory\nRecent context\nfast read/write"]
  B -->|"access_count >= 3\nor age >= 7 days"| C["Episodic Memory\nCompressed sessions\nLLM summarization"]
  C -->|"LLM extraction\nbackground task"| D["Semantic Memory\nFacts + vectors\nchromadb similarity"]
  D --> E["context_for(query)\nreturns ranked, token-budgeted string"]
  B --> E
  C --> E

  style A fill:#0d1117,color:#2dd4bf
  style B fill:#161b22,color:#818cf8
  style C fill:#161b22,color:#818cf8
  style D fill:#161b22,color:#818cf8
  style E fill:#0d1117,color:#2dd4bf
```

## Quick navigation

- New here? → [Quickstart](quickstart.md)
- How does it work? → [Concepts](concepts.md)
- Using LangGraph? → [LangGraph adapter](adapters/langgraph.md)
- Multiple agents? → [Server mode](server/index.md)
- Need guard + memory together? → [Guard integration](guard-integration.md)

---

[GitHub](https://github.com/plyraAI/plyra-memory) · [PyPI](https://pypi.org/project/plyra-memory) · [plyra-guard](https://plyraai.github.io/plyra-guard) · [@plyraAI](https://x.com/plyraAI)
