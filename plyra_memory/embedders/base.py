"""Abstract base class for embedders."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract embedder interface."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Return the embedding dimension."""

    async def embed_cached(self, text: str) -> list[float]:
        """Embed with caching.  Default falls back to ``embed()``."""
        return await self.embed(text)
