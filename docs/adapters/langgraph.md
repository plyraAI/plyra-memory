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
