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
