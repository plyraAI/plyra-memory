---
hide:
  - toc
---

<div class="plyra-hero">
  <h1>plyra-memory</h1>
  <p class="tagline">Persistent structured memory for AI agents.<br>
  Local-first. Server-optional. Framework-agnostic.</p>
</div>

<div class="plyra-grid">
  <div class="plyra-card">
    <h3>Zero config</h3>
    <p>pip install and go. SQLite + ChromaDB, everything local.</p>
  </div>
  <div class="plyra-card">
    <h3>Three layers</h3>
    <p>Working, episodic, and semantic memory. One API for all three.</p>
  </div>
  <div class="plyra-card">
    <h3>Five frameworks</h3>
    <p>LangGraph, AutoGen, LangChain, CrewAI, OpenAI Agents.</p>
  </div>
  <div class="plyra-card">
    <h3>Server mode</h3>
    <p>Two env vars. All agents share one memory layer.</p>
  </div>
</div>

## Install

```bash
pip install plyra-memory
```

## The simplest possible usage

```python
from plyra_memory import Memory

async with Memory() as memory:
    await memory.remember("user prefers Python async frameworks")
    ctx = await memory.context_for("what stack does the user use?")
    print(ctx.content)
```

That's it. Memory persists across restarts. No config required.

## How it works

```
Your agent calls  →  memory.remember(content)
                         ↓
                  ┌──────────────────────┐
                  │  working memory      │  this session
                  │  episodic memory     │  all sessions, vector search
                  │  semantic memory     │  extracted facts, decay model
                  └──────────────────────┘
                         ↓
Your agent calls  →  memory.context_for(query)
                         ↓
                  prompt-ready context string, injected before LLM call
```

## Next steps

<div class="plyra-grid">
  <div class="plyra-card">
    <h3><a href="quickstart/">Quickstart</a></h3>
    <p>Running example in 5 minutes.</p>
  </div>
  <div class="plyra-card">
    <h3><a href="concepts/">Concepts</a></h3>
    <p>How the three memory layers work.</p>
  </div>
  <div class="plyra-card">
    <h3><a href="adapters/">Adapters</a></h3>
    <p>LangGraph, AutoGen, LangChain, CrewAI, OpenAI.</p>
  </div>
  <div class="plyra-card">
    <h3><a href="server/">Server mode</a></h3>
    <p>Multi-agent, multi-tenant deployment.</p>
  </div>
</div>

---

Part of the [Plyra](https://plyraai.github.io) open-source stack.
Also see [plyra-guard](https://plyraai.github.io/plyra-guard) — action middleware for agents.
