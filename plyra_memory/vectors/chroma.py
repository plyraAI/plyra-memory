"""ChromaDB vector backend."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from plyra_memory.vectors.base import VectorBackend

log = logging.getLogger(__name__)


class ChromaVectors(VectorBackend):
    """ChromaDB persistent vector store."""

    def __init__(
        self,
        path: str,
        collection_name: str = "plyra_memory",
    ) -> None:
        self._path = Path(path).expanduser()
        self._path.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name
        self._client: Any = None
        self._collection: Any = None

    async def initialize(self) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=str(self._path))
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        log.info(
            "Initialised ChromaDB at %s (collection=%s)",
            self._path,
            self._collection_name,
        )

    async def close(self) -> None:
        # no-op for PersistentClient
        pass

    async def upsert(self, id: str, embedding: list[float], metadata: dict) -> None:
        # Chroma doesn't accept None values in metadata — filter them out
        clean_meta = {k: v for k, v in metadata.items() if v is not None}
        self._collection.upsert(
            ids=[id],
            embeddings=[embedding],
            metadatas=[clean_meta],
        )

    async def query(
        self, embedding: list[float], top_k: int, filters: dict | None = None
    ) -> list[dict]:
        count = self._collection.count()
        if count == 0:
            return []
        n = min(top_k, count)
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": n,
            "include": ["distances", "metadatas"],
        }
        if filters:
            kwargs["where"] = filters
        results = self._collection.query(**kwargs)

        items: list[dict] = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            for i, vid in enumerate(ids):
                dist = distances[i] if i < len(distances) else 0.0
                # Chroma cosine distance ∈ [0, 2]. Convert to similarity ∈ [0, 1]:
                score = 1.0 - (dist / 2.0)
                meta = metadatas[i] if i < len(metadatas) else {}
                items.append({"id": vid, "score": max(0.0, score), "metadata": meta})
        return items

    async def delete(self, id: str) -> bool:
        try:
            self._collection.delete(ids=[id])
            return True
        except Exception:
            log.warning("ChromaDB delete failed for id=%s", id, exc_info=True)
            return False

    async def count(self) -> int:
        return self._collection.count()
