"""plyra-memory CLI – Click + Rich."""

from __future__ import annotations

import sys

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="plyra-memory")
def cli() -> None:
    """Plyra Memory – cognitive memory for AI agents."""


@cli.command()
@click.option("--host", default="0.0.0.0", help="Bind host.")
@click.option("--port", default=7700, type=int, help="Bind port.")
@click.option("--reload", "do_reload", is_flag=True, help="Enable auto-reload.")
def serve(host: str, port: int, do_reload: bool) -> None:
    """Start the plyra-memory HTTP server."""
    console.print("\n[bold magenta]╔══════════════════════════════════╗[/]")
    console.print(
        "[bold magenta]║[/]  [bold white]Plyra Memory[/]"
        " [dim]v0.1.0[/]          [bold magenta]║[/]"
    )
    console.print(
        "[bold magenta]║[/]  [dim]Cognitive memory for AI agents[/] [bold magenta]║[/]"
    )
    console.print("[bold magenta]╚══════════════════════════════════╝[/]\n")
    console.print(f"  [green]➜[/] http://{host}:{port}")
    console.print(f"  [green]➜[/] Health: http://{host}:{port}/health")
    console.print()

    import uvicorn

    uvicorn.run(
        "plyra_memory.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=do_reload,
    )


@cli.command()
@click.option("--url", default="http://localhost:7700", help="Server URL.")
def ping(url: str) -> None:
    """Ping the plyra-memory server."""
    import httpx

    try:
        resp = httpx.get(f"{url}/health", timeout=5)
        data = resp.json()
        status = data.get("status", "ok")
        console.print(f"[green]✓[/] Server is [bold green]{status}[/]")
        console.print(f"  Store: {data.get('store_path', 'n/a')}")
        console.print(f"  Vectors: {data.get('vectors_path', 'n/a')}")
        console.print(f"  Model: {data.get('embed_model', 'n/a')}")
    except Exception as exc:
        console.print(f"[red]✗[/] Cannot reach server: {exc}")
        sys.exit(1)


@cli.command()
@click.option("--url", default="http://localhost:7700", help="Server URL.")
def stats(url: str) -> None:
    """Show memory statistics."""
    import httpx

    try:
        resp = httpx.get(f"{url}/stats", timeout=5)
        data = resp.json()
        console.print("[bold]Memory Statistics[/]")
        for key, value in data.items():
            console.print(f"  {key}: [cyan]{value}[/]")
    except Exception as exc:
        console.print(f"[red]✗[/] Cannot reach server: {exc}")
        sys.exit(1)


@cli.command()
@click.option(
    "--confirm",
    is_flag=True,
    prompt="This will delete ALL local memory data. Continue?",
    help="Skip confirmation prompt.",
)
def reset(confirm: bool) -> None:
    """Reset all local memory data."""
    if not confirm:
        console.print("[yellow]Aborted.[/]")
        return

    import shutil
    from pathlib import Path

    plyra_dir = Path.home() / ".plyra"
    if plyra_dir.exists():
        shutil.rmtree(plyra_dir)
        console.print("[green]✓[/] Deleted ~/.plyra")
    else:
        console.print("[dim]Nothing to delete – ~/.plyra does not exist.[/]")


if __name__ == "__main__":
    cli()
