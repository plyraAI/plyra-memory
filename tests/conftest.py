"""Shared test fixtures for plyra-memory tests."""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio

from plyra_memory.config import MemoryConfig
from plyra_memory.embedders.base import Embedder
from plyra_memory.schema import _new_id
from plyra_memory.vectors.base import VectorBackend

# ── Mock Embedder ────────────────────────────────────────────


class MockEmbedder(Embedder):
    """Returns [0.1] * 384 for every input. Never loads a real model."""

    @property
    def dim(self) -> int:
        return 384

    async def embed(self, text: str) -> list[float]:
        return [0.1] * 384

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 384 for _ in texts]


# ── Mock Vectors ─────────────────────────────────────────────


class MockVectors(VectorBackend):
    """In-memory vector store for unit tests."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        pass

    async def close(self) -> None:
        self._data.clear()

    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        self._data[id] = {"embedding": embedding, "metadata": metadata or {}}

    async def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Return all IDs with score 0.95 (mock similarity)."""
        results = []
        for doc_id, doc in self._data.items():
            if filters:
                meta = doc["metadata"]
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue
            results.append({"id": doc_id, "score": 0.95, "metadata": doc["metadata"]})
        return results[:top_k]

    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

    async def count(self) -> int:
        return len(self._data)


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def agent_id() -> str:
    return "test-agent"


@pytest.fixture
def session_id() -> str:
    return _new_id()


@pytest.fixture
def config(tmp_path) -> MemoryConfig:
    """Config pointing at tmp_path, never ~/.plyra."""
    return MemoryConfig(
        store_url=str(tmp_path / "test.db"),
        vectors_url=str(tmp_path / "test.index"),
        embed_model="mock",
        embed_dim=384,
        working_max_entries=50,
        cache_enabled=False,
    )


@pytest.fixture
def mock_embedder() -> MockEmbedder:
    return MockEmbedder()


@pytest.fixture
def mock_vectors() -> MockVectors:
    return MockVectors()


@pytest_asyncio.fixture
async def store(config):
    """Initialized SQLite store in tmp_path."""
    from plyra_memory.storage.sqlite import SQLiteStore

    s = SQLiteStore(config.store_url, config)
    await s.initialize()
    yield s
    await s.close()
