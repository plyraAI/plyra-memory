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
