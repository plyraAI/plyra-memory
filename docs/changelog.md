# Changelog

## v0.3.0

- **Groq support** — `Memory.with_groq()`, `GROQ_API_KEY` auto-detection
  - `llama-3.1-8b-instant` default — 800 tokens/second, free tier
  - Any OpenAI-compatible provider supported via `LLMExtractor(client, base_url=...)`
- **HTTP backend** — `PLYRA_SERVER_URL` + `PLYRA_API_KEY` activates server mode
  - Zero code changes — same `Memory()` API
  - All adapters (LangGraph, AutoGen, LangChain, CrewAI, OpenAI Agents) work in server mode
- **plyra-memory-server** — production server live at Azure Central India
- **AutoGen adapter fix** — `before_reply()` return type corrected to `list`
- **OpenAI Agents adapter fix** — `_MemoryTool` wrapper for proper `.name` + `.coroutine`
- 101+ tests passing

## v0.2.0

- LLM fact extraction (`LLMExtractor`) — Anthropic and OpenAI support
- Auto-promotion: episodes → semantic facts at access_count≥3 or age≥7 days
- Episodic summarization: LLM-compressed when session exceeds threshold
- `Memory.with_anthropic()` and `Memory.with_openai()` convenience constructors
- Extraction runs as background task — `remember()` is non-blocking
- `RegexExtractor` extracted into proper class, now the default fallback
- 123 tests passing

## v0.1.0

- Three-layer cognitive memory: working, episodic, semantic
- Local storage: SQLite + ChromaDB + sentence-transformers
- Universal API: `memory.remember()` + `memory.context_for()`
- Framework adapters: LangGraph, AutoGen, LangChain, CrewAI, OpenAI Agents
- HTTP server: `plyra-memory serve` → localhost:7700
- CLI: `serve`, `ping`, `stats`, `reset`
- SemanticCache with configurable similarity threshold
- 94 tests passing on Python 3.11, 3.12, 3.13

---

[GitHub releases](https://github.com/plyraAI/plyra-memory/releases)
