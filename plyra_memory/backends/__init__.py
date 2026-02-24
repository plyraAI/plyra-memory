"""Memory backends: local (default) and HTTP (server mode)."""
from .http import HTTPMemoryBackend

__all__ = ["HTTPMemoryBackend"]
