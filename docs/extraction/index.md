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
