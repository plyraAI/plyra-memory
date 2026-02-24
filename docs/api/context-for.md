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
