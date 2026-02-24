import os

files = {
    "mkdocs.yml": r"""
site_name: plyra-memory
site_url: https://plyraai.github.io/plyra-memory
site_description: Persistent structured memory for AI agents. Local-first, server-optional.
site_author: Plyra
repo_name: plyraAI/plyra-memory
repo_url: https://github.com/plyraAI/plyra-memory
edit_uri: edit/main/docs/

theme:
  name: material
  logo: assets/logo-mark.svg
  favicon: assets/logo-mark.svg
  palette:
    - scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
    - scheme: default
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
  font:
    text: DM Sans
    code: JetBrains Mono
  features:
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.top
    - navigation.footer
    - search.highlight
    - search.suggest
    - content.code.copy
    - content.code.annotate
    - toc.follow

extra_css:
  - stylesheets/extra.css

plugins:
  - search
  - minify:
      minify_html: true

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - attr_list
  - md_in_html
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Quickstart: quickstart.md
  - Concepts: concepts.md
  - API Reference:
    - Overview: api/index.md
    - remember(): api/remember.md
    - context_for(): api/context-for.md
    - recall(): api/recall.md
    - Layer access: api/layers.md
    - MemoryConfig: api/config.md
    - Schema: api/schema.md
  - Adapters:
    - Overview: adapters/index.md
    - LangGraph: adapters/langgraph.md
    - AutoGen: adapters/autogen.md
    - LangChain: adapters/langchain.md
    - CrewAI: adapters/crewai.md
    - OpenAI Agents: adapters/openai-agents.md
    - Plain Python: adapters/plain-python.md
  - Fact Extraction:
    - Overview: extraction/index.md
    - RegexExtractor: extraction/regex.md
    - LLMExtractor: extraction/llm.md
    - Custom extractor: extraction/custom.md
  - Server Mode:
    - Overview: server/index.md
    - Connect to server: server/quickstart.md
    - Azure deployment: server/azure.md
  - Guides:
    - Local vs server: guides/local-vs-server.md
    - Cross-session memory: guides/cross-session.md
    - Multi-agent setup: guides/multi-agent.md
    - Fact extraction tips: guides/fact-extraction.md
    - Production checklist: guides/production.md
  - Changelog: changelog.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/plyraAI
    - icon: fontawesome/brands/x-twitter
      link: https://x.com/plyraAI
  analytics:
    provider: google
    property: !ENV [GOOGLE_ANALYTICS_ID, ""]

copyright: >
  Copyright &copy; 2025 Plyra —
  <a href="https://github.com/plyraAI/plyra-memory/blob/main/LICENSE">Apache 2.0</a>
""",
    "docs/stylesheets/extra.css": r"""
/* ── Plyra brand colors ──────────────────────────────────────────────────── */
:root {
  --plyra-teal:    #2dd4bf;
  --plyra-teal-dk: #0d9488;
  --plyra-indigo:  #818cf8;
  --plyra-bg:      #0d1117;
  --plyra-surface: #161b22;
  --plyra-muted:   #5a7a96;
}

/* Material theme overrides */
[data-md-color-scheme="slate"] {
  --md-primary-fg-color:        #818cf8;
  --md-primary-fg-color--light: #a5b4fc;
  --md-primary-fg-color--dark:  #6366f1;
  --md-accent-fg-color:         #2dd4bf;
  --md-default-bg-color:        #0d1117;
  --md-default-bg-color--light: #161b22;
  --md-default-fg-color:        #e6edf3;
  --md-default-fg-color--light: #8b949e;
  --md-code-bg-color:           #161b22;
  --md-code-fg-color:           #e6edf3;
}

[data-md-color-scheme="default"] {
  --md-primary-fg-color:        #818cf8;
  --md-accent-fg-color:         #0d9488;
}

/* ── Typography ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

.md-header__title {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  letter-spacing: -0.02em;
}

/* ── Code blocks ─────────────────────────────────────────────────────────── */
.highlight code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
}

/* ── Nav active state ────────────────────────────────────────────────────── */
.md-nav__link--active {
  color: var(--plyra-indigo) !important;
  font-weight: 500;
}

/* ── Admonition custom colors ────────────────────────────────────────────── */
.md-typeset .admonition.tip,
.md-typeset details.tip {
  border-color: var(--plyra-teal);
}
.md-typeset .tip > .admonition-title,
.md-typeset .tip > summary {
  background-color: rgba(45, 212, 191, 0.1);
}
.md-typeset .tip > .admonition-title::before,
.md-typeset .tip > summary::before {
  background-color: var(--plyra-teal);
}

/* ── Tables ──────────────────────────────────────────────────────────────── */
.md-typeset table:not([class]) th {
  background-color: var(--plyra-surface);
  color: var(--plyra-indigo);
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.md-footer {
  background-color: var(--plyra-bg);
}

/* ── Home page hero ──────────────────────────────────────────────────────── */
.plyra-hero {
  text-align: center;
  padding: 3rem 0 2rem;
}
.plyra-hero h1 {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 2.5rem;
  letter-spacing: -0.03em;
  color: var(--plyra-indigo);
}
.plyra-hero .tagline {
  color: var(--plyra-muted);
  font-size: 1.1rem;
  margin-top: 0.5rem;
}
.plyra-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}
.plyra-card {
  background: var(--plyra-surface);
  border: 1px solid rgba(129, 140, 248, 0.2);
  border-radius: 8px;
  padding: 1.25rem;
}
.plyra-card h3 {
  color: var(--plyra-indigo);
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0 0 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.plyra-card p {
  color: var(--plyra-muted);
  font-size: 0.875rem;
  margin: 0;
}
""",
    "docs/index.md": r"""
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
""",
    "docs/quickstart.md": r"""
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
""",
    "docs/concepts.md": r"""
# Concepts

How plyra-memory's three-layer cognitive model works.

## The three layers

```
                    memory.remember(content)
                           ↓
┌──────────────────────────────────────────────┐
│ Working memory                               │
│ Current session. Max 50 entries.             │
│ Lowest-importance evicted when full.         │
│ Flushed to episodic on session end.          │
├──────────────────────────────────────────────┤
│ Episodic memory                              │
│ Permanent event log. Every session.          │
│ Vector-embedded. Retrieved by similarity.    │
│ Auto-promoted to semantic at access_count≥3  │
│ or age≥7 days.                               │
├──────────────────────────────────────────────┤
│ Semantic memory                              │
│ Structured facts. Subject/predicate/object.  │
│ Confidence decay over time.                  │
│ Fingerprint deduplication.                   │
└──────────────────────────────────────────────┘
                           ↓
                  memory.context_for(query)
                    → prompt-ready string
```

## Working memory

Working memory holds the current conversation — raw messages and tool
outputs from this session. It's fast, session-scoped, and bounded.

- **Capacity:** 50 entries (configurable via `working_max_entries`)
- **Eviction:** when full, the lowest-importance entry is deleted
- **Lifetime:** current session only
- **Flush:** when the session ends (or `memory.flush()` is called),
  working entries are converted to episodic events

```python
# Working memory — happens automatically inside remember()
from plyra_memory import Memory

memory = Memory()
async def test():
    await memory.working.add(dict(
        session_id=memory.session_id,
        content="user asked about deployment",
        importance=0.7,
        source="user_message",
    ))
```

## Episodic memory

Episodic memory is the permanent event log. Every exchange is stored
and never deleted (unless summarized). It's vector-embedded so retrieval
is semantic — not keyword matching.

- **Storage:** SQLite (facts) + ChromaDB (vectors)
- **Retrieval:** cosine similarity on sentence-transformer embeddings
- **Lifetime:** forever (or until summarized when session exceeds threshold)
- **Auto-promotion:** episodes accessed ≥3 times or older than 7 days
  are automatically promoted to semantic facts

```python
# Episodic — happens automatically inside remember()
from plyra_memory import Memory
from plyra_memory.schema import EpisodeEvent, Episode

memory = Memory()
async def test2():
    await memory.episodic.record(Episode(
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        event=EpisodeEvent.USER_MESSAGE,
        content="user asked about LangGraph deployment",
        importance=0.8,
    ))
```

## Semantic memory

Semantic memory stores structured facts — things the agent knows about
the world or the user that should persist regardless of how they came up.

- **Structure:** subject → predicate → object (e.g. `user PREFERS Python`)
- **Deduplication:** fingerprint on (agent_id, subject, predicate) —
  same fact updated in place, not duplicated
- **Decay:** confidence decays exponentially over time:
  `score = confidence × exp(-0.05 × days_since_access)`
- **Predicates:** IS, PREFERS, DISLIKES, USES, WORKS_ON, BELONGS_TO,
  LOCATED_IN, KNOWS, HAS, RELATED_TO

```python
from plyra_memory.schema import FactRelation, Fact

memory = Memory()
async def test3():
    await memory.semantic.learn(Fact(
        agent_id=memory.agent_id,
        content="user prefers Python",
        subject="user",
        predicate=FactRelation.PREFERS,
        object="Python",
        confidence=0.9,
    ))
```

## Retrieval and context injection

`context_for()` queries all three layers and assembles a prompt-ready
context string within a token budget:

```python
from plyra_memory import Memory

memory = Memory()
async def test4():
    ctx = await memory.context_for(
        query="what does the user prefer?",
        token_budget=2048,    # default
    )
```

Retrieval uses hybrid scoring: vector similarity + recency + importance.
Semantic facts score highest (structured, high signal).
Episodic events score by similarity + how recent they are.
Working entries score by importance within the session.

## Auto-promotion

Episodes automatically graduate to semantic facts when either trigger fires:

- **Access count:** episode recalled ≥3 times → promoted
- **Age:** episode older than 7 days → promoted

This means the semantic layer grows organically from conversation history
without any explicit `semantic.learn()` calls.

Configure thresholds in [MemoryConfig](api/config.md):

```python
from plyra_memory import MemoryConfig

config = MemoryConfig(
    semantic_promotion_threshold=3,   # access count trigger
    promotion_age_days=7,             # age trigger
    promotion_check_enabled=True,
)
```

## Episodic summarization

When a session accumulates more than `summarize_session_threshold` episodes
(default 20), plyra-memory compresses them:

- **Recent episodes** (last 30 days): LLM-summarized into one dense episode
- **Old episodes** (older than 30 days): deleted entirely

This keeps the database from growing unbounded while preserving signal.
Requires an LLM client (`Memory.with_anthropic()` or `Memory.with_openai()`).

---

**Next:** [API reference →](api/index.md) or [pick your framework →](adapters/index.md)
""",
    "docs/api/index.md": r"""
# API Reference

Complete reference for the `Memory` class and all public methods.

## Memory class

```python
from plyra_memory import Memory, MemoryConfig

# Zero config — local SQLite + ChromaDB
memory = Memory()

# With agent identifier
memory = Memory(agent_id="support-agent")

# With LLM fact extraction (Anthropic)
# memory = Memory.with_anthropic(api_key="sk-ant-...")

# With LLM fact extraction (OpenAI)
# memory = Memory.with_openai(api_key="sk-...")

# Full config
# memory = Memory(
#     config=MemoryConfig(...),
#     agent_id="my-agent",
#     extractor=LLMExtractor(client),
#     llm_client=client,
# )
```

## Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `MemoryConfig \| None` | `None` | Full config object. Uses defaults if omitted. |
| `agent_id` | `str` | `"default-agent"` | Stable identifier for this agent. Use same value across restarts to retain memory. |
| `session_id` | `str \| None` | `None` | Current session ID. Auto-generated if omitted. |
| `extractor` | `BaseExtractor \| None` | `None` | Fact extractor. Uses `RegexExtractor` fallback if omitted. |
| `llm_client` | `Any \| None` | `None` | LLM client for episodic summarization. |

## Class methods

| Method | Description |
|--------|-------------|
| `Memory.with_anthropic(api_key, ...)` | Convenience constructor with Anthropic client |
| `Memory.with_openai(api_key, ...)` | Convenience constructor with OpenAI client |

## Instance methods

| Method | Returns | Description |
|--------|---------|-------------|
| `await memory.remember(content, ...)` | `dict` | Write to all memory layers |
| `await memory.context_for(query, ...)` | `ContextResult` | Get prompt-ready context |
| `await memory.recall(query, ...)` | `RecallResult` | Search memory |
| `await memory.flush()` | `list[Episode]` | Flush working memory to episodic |
| `await memory.close()` | `None` | Close connections, cancel tasks |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `memory.agent_id` | `str` | Agent identifier |
| `memory.session_id` | `str` | Current session ID |
| `memory.working` | `WorkingMemoryLayer` | Direct working layer access |
| `memory.episodic` | `EpisodicLayer` | Direct episodic layer access |
| `memory.semantic` | `SemanticLayer` | Direct semantic layer access |

## Context manager

```python
from plyra_memory import Memory

async def test():
    # Recommended — handles close() automatically
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("hello")

    # Or manually
    memory = Memory(agent_id="my-agent")
    try:
        await memory.remember("hello")
    finally:
        await memory.close()
```

## Server mode

When `PLYRA_SERVER_URL` and `PLYRA_API_KEY` are set, `Memory()` routes
all operations to the remote server automatically.

```bash
export PLYRA_SERVER_URL=http://localhost:7700
export PLYRA_API_KEY=plm_live_abc123
```

```python
from plyra_memory import Memory

# Same code — local or server
async def test():
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("hello")
```

→ [Server mode docs](../server/index.md)

---

**Methods:**
[remember() →](remember.md) ·
[context_for() →](context-for.md) ·
[recall() →](recall.md) ·
[Layer access →](layers.md) ·
[MemoryConfig →](config.md) ·
[Schema →](schema.md)
""",
    "docs/api/remember.md": r"""
# memory.remember()

Universal write method. One call persists content to all relevant memory layers.

## Signature

```python
# await memory.remember(
#     content: str,
#     importance: float = 0.6,
#     source: str | None = None,
#     metadata: dict | None = None,
# ) -> dict
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | required | The content to store |
| `importance` | `float` | `0.6` | Priority 0.0–1.0. Higher = less likely to be evicted from working memory. |
| `source` | `str \| None` | `None` | Content origin. Maps to EpisodeEvent. |
| `metadata` | `dict \| None` | `None` | Arbitrary key-value metadata stored with the entry. |

### Source values

| Value | EpisodeEvent |
|-------|-------------|
| `"user_message"` | `USER_MESSAGE` |
| `"agent_response"` | `AGENT_RESPONSE` |
| `"tool_output"` | `TOOL_RESULT` |
| `"tool_call"` | `TOOL_CALL` |
| `None` or `"agent"` | `AGENT_RESPONSE` |

## Returns

```python
{
    "working_entry": "WorkingEntry | None",
    "episode": "Episode | None",
    "facts": [],   # always [] — extraction runs in background
}
```

!!! note "Fact extraction is asynchronous"
    Facts appear in semantic memory within ~500ms after `remember()` returns.
    Use `memory.semantic.query()` to check after a short delay if needed.

## What it does internally

```
remember(content)
    ↓
    ├── working.add()           synchronous — available immediately
    ├── episodic.record()       synchronous — available immediately
    └── asyncio.create_task()   background — fact extraction via extractor
              ↓
        RegexExtractor (default) or LLMExtractor
              ↓
        semantic.learn() for each detected fact
```

## Examples

```python
from plyra_memory import Memory

memory = Memory()
async def test():
    # Basic
    await memory.remember("user asked about deployment")

    # With source and importance
    await memory.remember(
        "user said they prefer TypeScript",
        source="user_message",
        importance=0.85,
    )

    # With metadata
    await memory.remember(
        "tool returned 42 results",
        source="tool_output",
        metadata={"tool": "web_search", "query": "python async"},
    )
```

## Fact extraction patterns

When using `RegexExtractor` (default), these patterns trigger fact storage:

| Pattern | Predicate | Example |
|---------|-----------|---------|
| `my name is X` | IS | `my name is Alex` |
| `I prefer X` | PREFERS | `I prefer async Python` |
| `I don't like X` | DISLIKES | `I don't like verbose APIs` |
| `I use X` | USES | `I use VSCode` |
| `I'm working on X` | WORKS_ON | `I'm working on a RAG pipeline` |
| `I work at X` | BELONGS_TO | `I work at Acme Corp` |
| `I'm based in X` | LOCATED_IN | `I'm based in Chennai` |
| `I know X` | KNOWS | `I know LangChain well` |

For higher recall, use [LLMExtractor](../extraction/llm.md).

---

← [API overview](index.md) · [context_for() →](context-for.md)
""",
    "docs/api/context-for.md": r"""
# memory.context_for()

Retrieve relevant memory and return a prompt-ready context string.
Call this before every LLM invocation.

## Signature

```python
# await memory.context_for(
#     query: str,
#     token_budget: int = 2048,
#     layers: list[MemoryLayer] | None = None,
# ) -> ContextResult
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | What to search for. Usually the user's latest message. |
| `token_budget` | `int` | `2048` | Max tokens in returned context. Memories added until budget exhausted. |
| `layers` | `list[MemoryLayer] \| None` | `None` | Which layers to search. Defaults to all three. |

## Returns: ContextResult

```python
# ctx.content        # str  — inject this into your LLM prompt
# ctx.token_count    # int  — tokens used
# ctx.token_budget   # int  — budget requested
# ctx.memories_used  # int  — number of memories included
# ctx.cache_hit      # bool — True if result served from SemanticCache
# ctx.latency_ms     # float
```

## Usage

```python
from plyra_memory import Memory

memory = Memory()
async def test():
    ctx = await memory.context_for("what stack does the user prefer?")
    user_message = "hey"
    # Inject into prompt
    prompt = f"You are a helpful assistant.\n\n{ctx.content}\n\nUser: {user_message}"
```

## Retrieval scoring

Memories are scored and ranked before selection:

```
semantic facts      weight: 0.5   (highest — structured, high signal)
episodic events     weight: 0.3   (vector similarity + recency)
working entries     weight: 0.2   (importance score, current session)

final_score = semantic_score × 0.5
            + episodic_score × 0.3
            + working_score  × 0.2
```

Memories are added to context in score order until `token_budget` is reached.

## Limit to specific layers

```python
from plyra_memory.schema import MemoryLayer
from plyra_memory import Memory

memory = Memory()
query = "what"
async def test():
    # Semantic only — fastest, structured facts only
    ctx = await memory.context_for(
        query,
        layers=[MemoryLayer.SEMANTIC],
    )

    # Episodic + semantic — skip working memory
    ctx = await memory.context_for(
        query,
        layers=[MemoryLayer.EPISODIC, MemoryLayer.SEMANTIC],
    )
```

## SemanticCache

`context_for()` results are cached by query similarity.
If a new query is within 0.90 cosine similarity of a cached query,
the cached result is returned immediately.

Configure:

```python
from plyra_memory import MemoryConfig

config = MemoryConfig(
    cache_enabled=True,                    # default True
    cache_similarity_threshold=0.90,       # default
)
```

---

← [remember()](remember.md) · [recall() →](recall.md)
""",
    "docs/api/config.md": r"""
# MemoryConfig

Full configuration reference for plyra-memory.

## Import

```python
from plyra_memory import MemoryConfig
```

## All options

```python
from plyra_memory import MemoryConfig

config = MemoryConfig(
    # Storage
    store_url="~/.plyra/memory.db",        # SQLite path
    vectors_url="~/.plyra/memory.index",   # ChromaDB path
    embed_model="all-MiniLM-L6-v2",        # sentence-transformers model

    # Working memory
    working_max_entries=50,                # max entries per session

    # Retrieval
    default_token_budget=2048,             # default for context_for()
    fusion_weights={                       # must sum to 1.0
        "semantic": 0.5,
        "episodic": 0.3,
        "working":  0.2,
    },

    # SemanticCache
    cache_enabled=True,
    cache_similarity_threshold=0.90,

    # Auto-promotion
    semantic_promotion_threshold=3,        # access_count trigger
    promotion_age_days=7,                  # age trigger
    promotion_check_enabled=True,

    # Episodic summarization
    summarize_enabled=True,
    summarize_session_threshold=20,        # episodes per session before summarizing
    summarize_recent_days=30,              # recent = within N days → LLM summary
    summarize_max_episodes=10,             # max episodes per summary call

    # Server mode (auto-detected from env vars)
    # Set via: PLYRA_SERVER_URL + PLYRA_API_KEY
)
```

## Environment variables

All config fields can be set via env vars with `PLYRA_` prefix:

```bash
PLYRA_STORE_URL=~/.plyra/memory.db
PLYRA_WORKING_MAX_ENTRIES=50
PLYRA_CACHE_ENABLED=true
PLYRA_SEMANTIC_PROMOTION_THRESHOLD=3
```

## Per-use-case presets

```python
from plyra_memory import MemoryConfig

# Minimal — fastest, no summarization
config = MemoryConfig(
    cache_enabled=False,
    summarize_enabled=False,
    promotion_check_enabled=False,
    working_max_entries=20,
)

# Full intelligence — needs LLM client
config = MemoryConfig(
    summarize_enabled=True,
    summarize_session_threshold=15,
    promotion_check_enabled=True,
    semantic_promotion_threshold=2,
)

# High-traffic server
config = MemoryConfig(
    cache_enabled=True,
    cache_similarity_threshold=0.85,   # more aggressive caching
    summarize_session_threshold=10,    # summarize sooner
    working_max_entries=30,
)
```

---

← [Layer access](layers.md) · [Schema →](schema.md)
""",
    "docs/adapters/index.md": r"""
# Adapters

plyra-memory works with every major agent framework through thin adapter wrappers.
All adapters expose the same two operations:

```
context_for(query)   →   read memory before LLM call
remember(content)    →   write memory after agent responds
```

## Framework support

| Framework | Import | Pattern |
|-----------|--------|---------|
| [LangGraph](langgraph.md) | `create_memory_nodes(memory)` | Two nodes in StateGraph |
| [AutoGen](autogen.md) | `MemoryHook(memory)` | Register on ConversableAgent |
| [LangChain](langchain.md) | `PlyraMemory(memory)` | Drop-in for ConversationBufferMemory |
| [CrewAI](crewai.md) | `MemoryTool(memory)` | Tool in Agent tools list |
| [OpenAI Agents](openai-agents.md) | `create_memory_tools(memory)` | Function tools |
| [Plain Python](plain-python.md) | `Memory()` directly | No adapter needed |

## Key design principle

**No framework is required at import time.**

```python
# This works even if langgraph is not installed
from plyra_memory.adapters.langgraph import create_memory_nodes
```

Framework imports happen lazily inside methods, not at module level.
`pip install plyra-memory` pulls in zero framework dependencies.

## Server mode

All adapters work identically in server mode.
Set `PLYRA_SERVER_URL` + `PLYRA_API_KEY` — no adapter code changes needed.

```bash
export PLYRA_SERVER_URL=http://localhost:7700
export PLYRA_API_KEY=plm_live_abc123
```

→ [Server mode docs](../server/index.md)

---

Pick your framework:
[LangGraph →](langgraph.md) ·
[AutoGen →](autogen.md) ·
[LangChain →](langchain.md) ·
[CrewAI →](crewai.md) ·
[OpenAI Agents →](openai-agents.md) ·
[Plain Python →](plain-python.md)
""",
    "docs/adapters/langgraph.md": r"""
# LangGraph

Two patterns: two nodes (recommended) or one combined node.

## Install

```bash
pip install plyra-memory langgraph
```

## Two-node pattern (recommended)

```python
from plyra_memory import Memory
from plyra_memory.adapters.langgraph import create_memory_nodes
# from langgraph.graph import StateGraph, MessagesState, END

memory = Memory(agent_id="my-agent")
ctx_node, rec_node = create_memory_nodes(memory)

# graph = StateGraph(MessagesState)
# graph.add_node("memory_in",  ctx_node)     # reads before LLM
# graph.add_node("llm",        your_llm_node)
# graph.add_node("memory_out", rec_node)     # writes after LLM

# graph.set_entry_point("memory_in")
# graph.add_edge("memory_in",  "llm")
# graph.add_edge("llm",        "memory_out")
# graph.add_edge("memory_out", END)
```

`ctx_node` injects memory context into `state["memory_context"]`.
Use it in your LLM node:

```python
# async def your_llm_node(state: MessagesState) -> dict:
#     memory_ctx = state.get("memory_context", "")
#     messages = state["messages"]

#     system = f"You are a helpful assistant.\n\n{memory_ctx}" if memory_ctx else \
#              "You are a helpful assistant."

#     response = await llm.ainvoke([SystemMessage(system)] + messages)
#     return {"messages": [response]}
```

## Single-node pattern

For simpler graphs where one node handles both read and write:

```python
# from plyra_memory.adapters.langgraph import memory_node
# graph.add_node("memory", memory_node(memory))
```

!!! warning "LangGraph ToolNode"
    Do not use `guard.wrap()` or direct memory wrapping with `ToolNode`.
    LangGraph's `ToolNode` manages internal state that conflicts with middleware.
    Always use `create_memory_nodes()` or `memory_node()` as graph nodes.

## State schema

`ctx_node` writes to `state["memory_context"]` (str).
Declare it in your state class:

```python
# from typing import Annotated
# from langgraph.graph import MessagesState

# class State(MessagesState):
#     memory_context: str = ""
```

---

← [Adapters overview](index.md) · [AutoGen →](autogen.md)
""",
    "docs/extraction/index.md": r"""
# Fact Extraction

How plyra-memory extracts structured facts from free text.

## Overview

When you call `memory.remember("my name is Alex")`, plyra-memory
automatically detects this as a fact and stores it in semantic memory:

```
subject:    user
predicate:  IS
object:     Alex
confidence: 0.95
```

This happens in the background — `remember()` returns immediately.

## Two extractors

| Extractor | Speed | Recall | Cost |
|-----------|-------|--------|------|
| [RegexExtractor](regex.md) | instant | ~60% | free |
| [LLMExtractor](llm.md) | ~500ms | ~95% | API call per message |

## Default behavior

Without configuration, `RegexExtractor` is used:

```python
from plyra_memory import Memory

memory = Memory()
async def test():
    # Uses regex — fast, no API calls
    await memory.remember("I prefer TypeScript")
    # → fact: user PREFERS TypeScript
```

## With LLM extraction

```python
import anthropic
from plyra_memory import Memory

# memory = Memory.with_anthropic(api_key="sk-ant-...")
# await memory.remember("I mostly reach for TypeScript these days")
# → fact: user PREFERS TypeScript   ← caught by LLM, missed by regex
```

## Custom extractor

Implement `BaseExtractor` to use any extraction method:

```python
from plyra_memory.extraction.base import BaseExtractor
from plyra_memory.schema import FactRelation
from plyra_memory import Memory

class MyExtractor(BaseExtractor):
    async def extract(self, text: str, agent_id: str) -> list[dict]:
        # your logic
        return [{"subject": "user", "predicate": FactRelation.KNOWS,
                 "object": "something", "confidence": 0.8}]

memory = Memory(extractor=MyExtractor())
```

→ [Custom extractor guide](custom.md)

---

[RegexExtractor →](regex.md) · [LLMExtractor →](llm.md) · [Custom →](custom.md)
""",
    "docs/server/index.md": r"""
# Server Mode

Connect plyra-memory to a shared server — all agents share one memory layer.

## When to use server mode

| | Local | Server |
|---|---|---|
| Agents | one process | unlimited, any machine |
| Memory | `~/.plyra/` | mounted volume or Postgres |
| Isolation | by `agent_id` | workspace → user → agent |
| Setup | zero | two env vars |
| Use case | development, single-agent | production, multi-agent teams |

## How it works

```
Agent A  ─┐
Agent B  ──┤── plyra-memory-server ── persistent storage
Agent C  ─┘         ↑
               plm_live_abc123
```

`Memory()` detects `PLYRA_SERVER_URL` and routes all operations
to the server via HTTP. No code changes required.

## Quickstart

```bash
# 1. Run the server
docker run -p 7700:7700 \
  -e PLYRA_ADMIN_API_KEY=your-admin-key \
  ghcr.io/plyraai/plyra-memory-server:latest

# 2. Create an API key
curl -X POST http://localhost:7700/admin/keys \
  -H "Authorization: Bearer your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "my-workspace", "env": "live"}'

# 3. Set env vars
export PLYRA_SERVER_URL=http://localhost:7700
export PLYRA_API_KEY=plm_live_abc123...
```

```python
# Same code as local mode
from plyra_memory import Memory

async def test():
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("user prefers Python")
        ctx = await memory.context_for("what stack?")
```

## Workspace isolation

Every API key belongs to a workspace. Memory is isolated between workspaces.

```python
# Workspace "acme" — key plm_live_acme...
# Workspace "other" — key plm_live_other...
# They cannot see each other's memory — enforced server-side
```

Within a workspace, memory is further namespaced by `user_id` and `agent_id`.

→ [Full server docs](https://plyraai.github.io/plyra-memory-server)
→ [Azure deployment](azure.md)
→ [Connect to server quickstart](quickstart.md)

---

← [Extraction](../extraction/index.md) · [Guides →](../guides/local-vs-server.md)
""",
    "docs/server/azure.md": r"""
# Azure Container Apps Deployment

Deploy plyra-memory-server to Azure Container Apps.
Free tier available. Scales to zero when idle.

## Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login
az extension add --name containerapp --upgrade
```

## Deploy

```bash
# 1. Create resource group
az group create --name plyra-rg --location eastus

# 2. Create Container Apps environment
az containerapp env create \
  --name plyra-env \
  --resource-group plyra-rg \
  --location eastus

# 3. Create Azure File Share for persistent storage
az storage account create \
  --name plyrastorage \
  --resource-group plyra-rg \
  --sku Standard_LRS

az storage share create \
  --name plyra-data \
  --account-name plyrastorage

# 4. Deploy the container
az containerapp create \
  --name plyra-memory-server \
  --resource-group plyra-rg \
  --environment plyra-env \
  --image ghcr.io/plyraai/plyra-memory-server:latest \
  --target-port 7700 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --env-vars \
    PLYRA_ADMIN_API_KEY=secretref:admin-key \
    PLYRA_STORE_URL=/data/memory.db \
    PLYRA_VECTORS_URL=/data/memory.index \
    PLYRA_KEY_STORE_URL=/data/keys.db
```

## Get your URL

```bash
az containerapp show \
  --name plyra-memory-server \
  --resource-group plyra-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
# → plyra-memory-server.eastus.azurecontainerapps.io
```

## Connect the library

```bash
export PLYRA_SERVER_URL=https://plyra-memory-server.eastus.azurecontainerapps.io
export PLYRA_API_KEY=plm_live_...
```

```python
from plyra_memory import Memory

async def test():
    async with Memory(agent_id="my-agent") as memory:
        await memory.remember("hello from Azure")
```

---

← [Server overview](index.md) · [Guides →](../guides/production.md)
""",
    "docs/guides/local-vs-server.md": r"""
# Local vs Server Mode

How to decide which mode to use.

## Decision guide

```
Are you building a prototype or running locally?
  → Local mode. Zero setup.

Do you need memory shared across multiple agents or machines?
  → Server mode.

Is this a production deployment with multiple users?
  → Server mode with workspace isolation.

Are you unsure?
  → Start local. Add PLYRA_SERVER_URL later — zero code changes.
```

## Comparison

| | Local | Server |
|---|---|---|
| **Install** | `pip install plyra-memory` | `docker compose up` |
| **Config** | none | two env vars |
| **Storage** | `~/.plyra/` | mounted volume |
| **Agents** | one process | unlimited, any machine |
| **Isolation** | by `agent_id` | workspace → user → agent |
| **Scale** | single node | multi-instance with Postgres |
| **LLM extraction** | optional | optional (configured server-side) |
| **Cost** | free | hosting cost |

## Migration: local → server

No code changes required. Just add env vars:

```bash
# Was: local mode (no env vars needed)
# Now: server mode
export PLYRA_SERVER_URL=https://your-server.azurecontainerapps.io
export PLYRA_API_KEY=plm_live_abc123
```

Your agent code stays identical.

---

← [Server overview](../server/index.md) · [Multi-agent →](multi-agent.md)
""",
    "docs/changelog.md": r"""
# Changelog

## v0.2.0

- LLM fact extraction (`LLMExtractor`) — Anthropic and OpenAI support
- Auto-promotion: episodes → semantic facts at access_count≥3 or age≥7 days
- Episodic summarization: LLM-compressed when session exceeds threshold
- `Memory.with_anthropic()` and `Memory.with_openai()` convenience constructors
- Extraction runs as background task — `remember()` is non-blocking
- `RegexExtractor` extracted into proper class, now the default fallback
- 123 tests passing

## v0.1.0

- Three-layer cognitive memory: working, episodic, semantic
- Local storage: SQLite + ChromaDB + sentence-transformers
- Universal API: `memory.remember()` + `memory.context_for()`
- Framework adapters: LangGraph, AutoGen, LangChain, CrewAI, OpenAI Agents
- HTTP server: `plyra-memory serve` → localhost:7700
- CLI: `serve`, `ping`, `stats`, `reset`
- SemanticCache with configurable similarity threshold
- 94 tests passing on Python 3.11, 3.12, 3.13

---

[GitHub releases](https://github.com/plyraAI/plyra-memory/releases)
""",
    ".github/workflows/docs.yml": r"""
name: Docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: astral-sh/setup-uv@v3

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install docs dependencies
        run: |
          uv pip install --system \
            mkdocs-material \
            mkdocs-minify-plugin \
            mkdocs-git-revision-date-localized-plugin

      - name: Build and deploy docs
        run: mkdocs gh-deploy --force --clean
""",
    # Missing files basic stubs
    "docs/api/recall.md": "# `memory.recall()`\n\nThe internal recall mechanism retrieving memory manually.",
    "docs/api/layers.md": "# Layer Access\n\nDirect low-level access to the memory layer APIs.",
    "docs/api/schema.md": "# Pydantic Schema\n\nPydantic schema to deal with events, working structures. See schema file for all details.",
    "docs/adapters/autogen.md": """# AutoGen

```python
from plyra_memory import Memory
from plyra_memory.adapters.autogen import MemoryHook

memory = Memory(agent_id="my-agent")
hook = MemoryHook(memory)

# Register on agent manually using corresponding hook functionality.
```""",
    "docs/adapters/langchain.md": """# LangChain

```python
from plyra_memory import Memory
from plyra_memory.adapters.langchain import PlyraMemory

memory = Memory(agent_id="my-agent")
lc_memory = PlyraMemory(memory)
```""",
    "docs/adapters/crewai.md": """# CrewAI

```python
from plyra_memory import Memory
from plyra_memory.adapters.crewai import MemoryTool

memory = Memory(agent_id="my-agent")
tool = MemoryTool(memory)
```""",
    "docs/adapters/openai-agents.md": """# OpenAI Agents

```python
from plyra_memory import Memory
from plyra_memory.adapters.openai_agents import create_memory_tools

memory = Memory(agent_id="my-agent")
tools = create_memory_tools(memory)
```""",
    "docs/adapters/plain-python.md": """# Plain Python

```python
import asyncio
from plyra_memory import Memory

async def main():
    async with Memory() as memory:
        await memory.remember("I am testing")
```""",
    "docs/extraction/regex.md": "# Regex Extractor\n\nExtraction via Regular Expression patterns across memory statements.",
    "docs/extraction/llm.md": "# LLM Extractor\n\nExtraction via Anthropic and OpenAI LLM models seamlessly.",
    "docs/extraction/custom.md": "# Custom Extractions\n\nCustom integrations of extraction hooks to the memory structure.",
    "docs/server/quickstart.md": "# Quickstart (Server)\n\nStartup the server easily locally.",
    "docs/guides/cross-session.md": "# Cross-session Persistence\n\nKeeps all state using UUIDs natively resolving your session requirements across restarts.",
    "docs/guides/multi-agent.md": "# Multi-agent Deployment\n\nCombine Agents and let them share their environments through context API features.",
    "docs/guides/fact-extraction.md": "# Fact Extraction Tips\n\nAdjust constraints such as recency, and decay metrics seamlessly.",
    "docs/guides/production.md": "# Production Checklist\n\nChecks to run continuously to achieve production ready quality."
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print("Files generated.")
