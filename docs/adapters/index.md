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
