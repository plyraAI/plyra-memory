"""Sentence-transformers embedder (local, CPU/GPU) with LRU cache."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any

from plyra_memory.embedders.base import Embedder

log = logging.getLogger(__name__)

_DEFAULT_CACHE_SIZE = 2048


class SentenceTransformerEmbedder(Embedder):
    """Embedder using sentence-transformers (all-MiniLM-L6-v2 by default).

    Includes an in-memory LRU cache (default 2 048 entries) so repeated
    texts never hit the model twice.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_size: int = _DEFAULT_CACHE_SIZE,
    ) -> None:
        self._model_name = model_name
        self._model: Any = None
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_size = max(0, cache_size)
        self._hits = 0
        self._misses = 0

    # -- model lifecycle ---------------------------------------------------

    def _load(self) -> None:
        if self._model is not None:
            return
        t0 = time.monotonic()
        try:
            import truststore

            truststore.inject_into_ssl()
        except ImportError:
            pass

        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self._model_name)
        elapsed = (time.monotonic() - t0) * 1000
        log.info(
            "Loaded embedding model %s in %.0f ms",
            self._model_name,
            elapsed,
        )

    # -- cache helpers -----------------------------------------------------

    @staticmethod
    def _cache_key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:24]

    def _cache_get(self, text: str) -> list[float] | None:
        key = self._cache_key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def _cache_put(self, text: str, embedding: list[float]) -> None:
        if self._cache_size == 0:
            return
        key = self._cache_key(text)
        self._cache[key] = embedding
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    # -- public API --------------------------------------------------------

    async def embed(self, text: str) -> list[float]:
        cached = self._cache_get(text)
        if cached is not None:
            return cached
        self._load()
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self._model.encode(text)
        )
        result = embedding.tolist()
        self._cache_put(text, result)
        return result

    async def embed_cached(self, text: str) -> list[float]:
        """Alias with explicit cache semantics."""
        return await self.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed, skipping cache hits and only encoding new texts."""
        results: list[list[float] | None] = [None] * len(texts)
        to_encode: list[tuple[int, str]] = []

        for i, t in enumerate(texts):
            cached = self._cache_get(t)
            if cached is not None:
                results[i] = cached
            else:
                to_encode.append((i, t))

        if to_encode:
            self._load()
            encode_texts = [t for _, t in to_encode]
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, lambda: self._model.encode(encode_texts)
            )
            for (idx, txt), emb in zip(to_encode, embeddings):
                vec = emb.tolist()
                self._cache_put(txt, vec)
                results[idx] = vec

        return results  # type: ignore[return-value]

    @property
    def dim(self) -> int:
        if self._model is not None:
            d = self._model.get_sentence_embedding_dimension()
            if d is not None:
                return int(d)
        return 384

    @property
    def cache_stats(self) -> dict[str, int]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
        }
