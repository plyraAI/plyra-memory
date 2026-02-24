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
