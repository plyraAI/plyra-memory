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
