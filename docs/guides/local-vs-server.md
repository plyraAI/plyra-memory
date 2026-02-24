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
