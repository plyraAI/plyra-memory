"""Abstract base class for memory exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MemoryExporter(ABC):
    """Abstract exporter interface for memory operation events."""

    @abstractmethod
    async def export(self, event: dict) -> None:
        """Export a memory operation event."""
