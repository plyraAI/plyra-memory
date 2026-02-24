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
