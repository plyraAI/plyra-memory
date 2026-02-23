"""Abstract base class for vector backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VectorBackend(ABC):
    """Abstract async vector store backend."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store."""

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store."""

    @abstractmethod
    async def upsert(self, id: str, embedding: list[float], metadata: dict) -> None:
        """Insert or update a vector."""

    @abstractmethod
    async def query(
        self, embedding: list[float], top_k: int, filters: dict | None = None
    ) -> list[dict]:
        """Query for similar vectors. Returns list of {id, score, metadata}."""

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete a vector by ID."""

    @abstractmethod
    async def count(self) -> int:
        """Return total number of vectors stored."""
