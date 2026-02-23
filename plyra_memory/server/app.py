"""FastAPI server for plyra-memory."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from plyra_memory.config import MemoryConfig
from plyra_memory.memory import Memory
from plyra_memory.schema import (
    EpisodicQuery,
    Fact,
    HealthStatus,
    SemanticQuery,
    WorkingEntry,
)

_memory: Memory | None = None


def _get_memory() -> Memory:
    assert _memory is not None, "Memory not initialized"
    return _memory


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    global _memory  # noqa: PLW0603
    config = MemoryConfig.default()
    _memory = Memory(config=config)
    await _memory._ensure_initialized()  # noqa: SLF001
    yield
    if _memory is not None:
        await _memory.close()
        _memory = None


def create_app(config: MemoryConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="plyra-memory",
        description="Cognitive memory for AI agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - t0) * 1000
        response.headers["X-Latency-Ms"] = f"{elapsed:.1f}"
        return response

    # ---------- Health & Info ----------

    @app.get("/")
    async def root():
        return {"name": "plyra-memory", "version": "0.1.0", "status": "ok"}

    @app.get("/health")
    async def health():
        mem = _get_memory()
        cfg = mem._config  # noqa: SLF001
        return HealthStatus(
            status="ok",
            version="0.1.0",
            store_path=cfg.store_url,
            vectors_path=cfg.vectors_url,
            embed_model=cfg.embed_model,
        ).model_dump()

    @app.get("/stats")
    async def stats():
        mem = _get_memory()
        store = mem._store  # noqa: SLF001
        vectors = mem._vectors  # noqa: SLF001
        assert store is not None
        assert vectors is not None

        working = await store.get_working_entries(mem.session_id)
        ep_query = EpisodicQuery(agent_id=mem.agent_id, top_k=200)
        episodes_count = len(await store.get_episodes(ep_query))
        fact_query = SemanticQuery(agent_id=mem.agent_id, top_k=200)
        facts_count = len(await store.get_facts(fact_query))
        vector_count = await vectors.count()

        return {
            "session_id": mem.session_id,
            "agent_id": mem.agent_id,
            "working_entries": len(working),
            "episodes": episodes_count,
            "facts": facts_count,
            "vectors": vector_count,
        }

    # ---------- Working Memory ----------

    @app.post("/working")
    async def add_working(entry: dict[str, Any]):
        mem = _get_memory()
        assert mem.working is not None
        we = WorkingEntry(
            session_id=mem.session_id,
            agent_id=mem.agent_id,
            **entry,
        )
        result = await mem.working.add(we)
        return result.model_dump(mode="json")

    @app.get("/working/{session_id}")
    async def get_working(session_id: str):
        mem = _get_memory()
        assert mem.working is not None
        entries = await mem.working.get(session_id)
        return [e.model_dump(mode="json") for e in entries]

    @app.delete("/working/{session_id}")
    async def clear_working(session_id: str):
        mem = _get_memory()
        assert mem.working is not None
        await mem.working.clear(session_id)
        return {"cleared": True, "session_id": session_id}

    # ---------- Episodic Memory ----------

    @app.post("/episodes")
    async def query_episodes(query: EpisodicQuery):
        mem = _get_memory()
        assert mem.episodic is not None
        results = await mem.episodic.query(query)
        return [e.model_dump(mode="json") for e in results]

    @app.get("/episodes/{episode_id}")
    async def get_episode(episode_id: str):
        mem = _get_memory()
        assert mem.episodic is not None
        episode = await mem.episodic.get(episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        return episode.model_dump(mode="json")

    # ---------- Semantic Memory ----------

    @app.put("/facts")
    async def learn_fact(fact_data: dict[str, Any]):
        mem = _get_memory()
        assert mem.semantic is not None
        fact = Fact(agent_id=mem.agent_id, **fact_data)
        result = await mem.semantic.learn(fact)
        return result.model_dump(mode="json")

    @app.delete("/facts/{fact_id}")
    async def forget_fact(fact_id: str):
        mem = _get_memory()
        assert mem.semantic is not None
        success = await mem.semantic.forget(fact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Fact not found")
        return {"deleted": True, "fact_id": fact_id}

    # ---------- Recall & Context ----------

    @app.post("/recall")
    async def recall(body: dict[str, Any]):
        mem = _get_memory()
        query_text = body.get("query", "")
        top_k = body.get("top_k", 10)
        layers = body.get("layers")
        result = await mem.recall(query_text, top_k=top_k, layers=layers)
        return result.model_dump(mode="json")

    @app.post("/context")
    async def context(body: dict[str, Any]):
        mem = _get_memory()
        query_text = body.get("query", "")
        token_budget = body.get("token_budget")
        layers = body.get("layers")
        result = await mem.context_for(
            query_text, token_budget=token_budget, layers=layers
        )
        return result.model_dump(mode="json")

    return app


class MemoryServer:
    """Wrapper for running the server programmatically."""

    def __init__(
        self,
        config: MemoryConfig | None = None,
        host: str = "0.0.0.0",
        port: int = 7700,
    ) -> None:
        self.config = config or MemoryConfig.default()
        self.host = host
        self.port = port
        self.app = create_app(self.config)

    def run(self) -> None:
        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)
