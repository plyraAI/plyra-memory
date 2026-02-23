"""StdoutExporter — prints structured memory events to terminal via Rich."""

from __future__ import annotations

from plyra_memory.exporters.base import MemoryExporter


class StdoutExporter(MemoryExporter):
    """Prints memory operation events to stdout using Rich."""

    def __init__(self) -> None:
        from rich.console import Console

        self._console = Console()

    async def export(self, event: dict) -> None:
        ts = event.get("timestamp", "")[:19]
        op = event.get("op_type", "unknown")
        sid = (event.get("session_id") or "")[:8]
        ms = event.get("latency_ms", 0)
        self._console.print(
            f"[dim]{ts}[/dim] [bold #818cf8]{op}[/bold #818cf8] "
            f"[dim]{sid}[/dim] [dim]{ms:.1f}ms[/dim]"
        )
