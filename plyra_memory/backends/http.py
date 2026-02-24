"""
HTTP backend for plyra-memory.
Activated when PLYRA_SERVER_URL is set.
Proxies all Memory operations to a plyra-memory-server instance.
"""

from __future__ import annotations

import httpx

from ..schema import ContextResult, RecallResult


class HTTPMemoryBackend:
    """
    Drop-in backend that routes memory operations to a remote server.
    Used when PLYRA_SERVER_URL env var is set.
    """

    def __init__(
        self,
        server_url: str,
        api_key: str,
        agent_id: str,
        user_id: str | None = None,
        timeout: float = 30.0,
    ):
        self._base = server_url.rstrip("/")
        self._agent_id = agent_id
        self._user_id = user_id
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base,
                headers=self._headers,
                timeout=self._timeout,
            )
        return self._client

    async def remember(
        self,
        content: str,
        importance: float = 0.6,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        client = await self._get_client()
        resp = await client.post(
            "/v1/remember",
            json={
                "content": content,
                "importance": importance,
                "source": source,
                "agent_id": self._agent_id,
                "user_id": self._user_id,
                "metadata": metadata or {},
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def context_for(self, query: str, token_budget: int = 2048) -> ContextResult:
        client = await self._get_client()
        resp = await client.post(
            "/v1/context",
            json={
                "query": query,
                "token_budget": token_budget,
                "agent_id": self._agent_id,
                "user_id": self._user_id,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        return ContextResult(
            query=data["query"],
            content=data["content"],
            token_count=data["token_count"],
            token_budget=data["token_budget"],
            memories_used=data["memories_used"],
            cache_hit=data.get("cache_hit", False),
            latency_ms=data.get("latency_ms", 0),
        )

    async def recall(self, query: str, top_k: int = 10) -> RecallResult:
        client = await self._get_client()
        resp = await client.post(
            "/v1/recall",
            json={
                "query": query,
                "top_k": top_k,
                "agent_id": self._agent_id,
                "user_id": self._user_id,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        from ..schema import MemoryLayer, RankedMemory

        results = []
        for r in data.get("results", []):
            results.append(RankedMemory(**r))
        return RecallResult(
            query=data["query"],
            results=results,
            total_found=data["total_found"],
            layers_searched=list(MemoryLayer),
            cache_hit=data.get("cache_hit", False),
            latency_ms=data.get("latency_ms", 0),
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
