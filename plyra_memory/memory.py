"""plyra-memory — main public API."""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any

from plyra_memory.config import MemoryConfig
from plyra_memory.schema import (
    ContextResult,
    Episode,
    EpisodeEvent,
    Fact,
    FactRelation,
    MemoryLayer,
    RecallRequest,
    RecallResult,
    Session,
    WorkingEntry,
    _new_id,
)

if TYPE_CHECKING:
    from plyra_memory.embedders.base import Embedder
    from plyra_memory.layers.episodic import EpisodicLayer
    from plyra_memory.layers.semantic import SemanticLayer
    from plyra_memory.layers.working import WorkingMemoryLayer
    from plyra_memory.retrieval.cache import SemanticCache
    from plyra_memory.retrieval.engine import HybridRetrieval
    from plyra_memory.storage.base import StorageBackend
    from plyra_memory.vectors.base import VectorBackend

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic fact-extraction patterns  (subject, predicate, object_template)
# ---------------------------------------------------------------------------
_FACT_PATTERNS: list[tuple[re.Pattern[str], str, FactRelation, str]] = [
    (
        re.compile(r"my name is (\w+)", re.IGNORECASE),
        "user",
        FactRelation.IS,
        r"named \1",
    ),
    (
        re.compile(
            r"i(?:'m| am) (?:a |an )?(\w[\w\s]{2,30}?)(?:\.|,|$| and| who)",
            re.IGNORECASE,
        ),
        "user",
        FactRelation.IS_A,
        r"\1",
    ),
    (
        re.compile(
            r"i (?:prefer|like|love|enjoy) ([\w\s]+?)(?:\.|,|$| over| more| and)",
            re.IGNORECASE,
        ),
        "user",
        FactRelation.PREFERS,
        r"\1",
    ),
    (
        re.compile(
            r"i (?:don't like|dislike|hate|don't enjoy) ([\w\s]+?)(?:\.|,|$| and)",
            re.IGNORECASE,
        ),
        "user",
        FactRelation.DISLIKES,
        r"\1",
    ),
    (
        re.compile(
            r"i(?:'m| am) working on ([\w\s]+?)(?:\.|,|$| and| with)",
            re.IGNORECASE,
        ),
        "user",
        FactRelation.WORKS_ON,
        r"\1",
    ),
    (
        re.compile(r"i use ([\w\s]+?)(?:\.|,|$| for| and)", re.IGNORECASE),
        "user",
        FactRelation.USES,
        r"\1",
    ),
    (
        re.compile(
            r"i(?:'m| am) (?:based in|from|living in|located in) "
            r"([\w\s]+?)(?:\.|,|$| and)",
            re.IGNORECASE,
        ),
        "user",
        FactRelation.LOCATED_IN,
        r"\1",
    ),
    (
        re.compile(r"i know ([\w\s]+?)(?:\.|,|$| and| very)", re.IGNORECASE),
        "user",
        FactRelation.KNOWS,
        r"\1",
    ),
]


class Memory:
    """
    Zero-config local memory for AI agents.

    Usage::

        async with Memory() as mem:
            await mem.working.add("user debugging LangGraph")
            ctx = await mem.context_for("help debug")
    """

    def __init__(
        self,
        config: MemoryConfig | None = None,
        agent_id: str = "default-agent",
        session_id: str | None = None,
        *,
        embedder: Embedder | None = None,
        vectors: VectorBackend | None = None,
        store: StorageBackend | None = None,
    ) -> None:
        self._config = config or MemoryConfig.default()
        self._agent_id = agent_id
        self._session_id = session_id or _new_id()
        self._initialized = False
        self._start_time: float = 0.0

        # Pre-injected components (optional DI)
        self._injected_store = store
        self._injected_vectors = vectors
        self._injected_embedder = embedder

        # All None until _ensure_initialized
        self._store: StorageBackend | None = None
        self._vectors: VectorBackend | None = None
        self._embedder: Embedder | None = None
        self.working: WorkingMemoryLayer | None = None  # type: ignore[assignment]
        self.episodic: EpisodicLayer | None = None  # type: ignore[assignment]
        self.semantic: SemanticLayer | None = None  # type: ignore[assignment]
        self._retrieval: HybridRetrieval | None = None
        self._cache: SemanticCache | None = None
        self._session: Session | None = None

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        self._start_time = time.monotonic()

        from plyra_memory.layers.episodic import EpisodicLayer
        from plyra_memory.layers.semantic import SemanticLayer
        from plyra_memory.layers.working import WorkingMemoryLayer
        from plyra_memory.retrieval.cache import SemanticCache
        from plyra_memory.retrieval.engine import HybridRetrieval

        # Use injected components or create defaults
        if self._injected_store is not None:
            self._store = self._injected_store
        else:
            from plyra_memory.storage.sqlite import SQLiteStore

            self._store = SQLiteStore(self._config.store_url, self._config)
        await self._store.initialize()

        if self._injected_vectors is not None:
            self._vectors = self._injected_vectors
        else:
            from plyra_memory.vectors.chroma import ChromaVectors

            self._vectors = ChromaVectors(
                self._config.vectors_url,
                collection_name=self._config.chroma_collection_name,
            )
        await self._vectors.initialize()

        if self._injected_embedder is not None:
            self._embedder = self._injected_embedder
        else:
            from plyra_memory.embedders.sentence_transformers import (
                SentenceTransformerEmbedder,
            )

            self._embedder = SentenceTransformerEmbedder(
                self._config.embed_model,
                cache_size=self._config.embedding_cache_size,
            )

        self.working = WorkingMemoryLayer(self._store, self._config)
        self.episodic = EpisodicLayer(
            self._store, self._vectors, self._embedder, self._config
        )
        self.semantic = SemanticLayer(
            self._store, self._vectors, self._embedder, self._config
        )
        self._retrieval = HybridRetrieval(
            self.working,
            self.episodic,
            self.semantic,
            self._embedder,
            self._config,
        )
        self._cache = SemanticCache(self._embedder, self._config)

        # Create or resume session
        existing = await self._store.get_session(self._session_id)
        if existing:
            self._session = existing
        else:
            self._session = Session(id=self._session_id, agent_id=self._agent_id)
            await self._store.save_session(self._session)

        self._initialized = True
        log.info(
            "Memory initialised (session=%s agent=%s)",
            self._session_id[:12],
            self._agent_id,
        )

    async def recall(
        self,
        query: str,
        top_k: int = 10,
        layers: list[Any] | None = None,
    ) -> RecallResult:
        """Recall relevant memories across all layers."""
        await self._ensure_initialized()
        assert self._cache is not None
        assert self._retrieval is not None

        # Cache.get returns (result_or_None, query_embedding) — the
        # embedding is always computed exactly once and reused everywhere.
        cached, query_embedding = await self._cache.get(query)
        if cached:
            return cached

        request = RecallRequest(
            query=query,
            session_id=self._session_id,
            agent_id=self._agent_id,
            top_k=top_k,
            layers=layers or list(MemoryLayer),
            similarity_weight=self._config.default_similarity_weight,
            recency_weight=self._config.default_recency_weight,
            importance_weight=self._config.default_importance_weight,
        )
        result = await self._retrieval.recall(
            request, query_embedding=query_embedding
        )

        if self._config.cache_enabled:
            await self._cache.set(
                query, result, query_embedding=query_embedding
            )

        return result

    async def context_for(
        self,
        query: str,
        token_budget: int | None = None,
        layers: list[Any] | None = None,
    ) -> ContextResult:
        """Build a context string within a token budget."""
        await self._ensure_initialized()
        budget = token_budget or self._config.default_token_budget

        recall_result = await self.recall(query, top_k=50, layers=layers)

        parts: list[str] = []
        token_count = 0
        for ranked in recall_result.results:
            est = int(len(ranked.content.split()) * 1.3) + 5
            if token_count + est > budget:
                break
            parts.append(f"[{ranked.layer.value.upper()}] {ranked.content}")
            token_count += est

        return ContextResult(
            query=query,
            content="\n".join(parts),
            token_count=token_count,
            token_budget=budget,
            memories_used=len(parts),
            cache_hit=recall_result.cache_hit,
            latency_ms=recall_result.latency_ms,
        )

    # ------------------------------------------------------------------
    # Universal write
    # ------------------------------------------------------------------

    async def remember(
        self,
        content: str,
        *,
        importance: float = 0.5,
        source: str | None = None,
        event: EpisodeEvent = EpisodeEvent.AGENT_RESPONSE,
        tool_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write *content* to all three memory layers in one call.

        1. **Working** — adds a ``WorkingEntry``.
        2. **Episodic** — records an ``Episode``.
        3. **Semantic** — runs heuristic fact extraction and calls
           ``semantic.learn`` for every fact found.

        Returns ``{"working": WorkingEntry, "episodic": Episode,
        "facts": [Fact, ...]}``.
        """
        await self._ensure_initialized()
        assert self.working is not None
        assert self.episodic is not None

        meta = metadata or {}
        results: dict[str, Any] = {"working": None, "episodic": None, "facts": []}

        # 1. Working memory
        entry = WorkingEntry(
            session_id=self._session_id,
            agent_id=self._agent_id,
            content=content,
            importance=importance,
            source=source,
            metadata=meta,
        )
        results["working"] = await self.working.add(entry)

        # 2. Episodic layer
        episode = Episode(
            session_id=self._session_id,
            agent_id=self._agent_id,
            event=event,
            content=content,
            importance=importance,
            tool_name=tool_name,
            metadata=meta,
        )
        results["episodic"] = await self.episodic.record(episode)

        # 3. Semantic — extract facts (never raises)
        results["facts"] = await self._extract_and_learn(content)

        return results

    async def _extract_and_learn(self, text: str) -> list[Fact]:
        """Heuristic regex fact extraction.  **Never raises.**"""
        assert self.semantic is not None
        learned: list[Fact] = []
        for pattern, subject, predicate, obj_template in _FACT_PATTERNS:
            try:
                match = pattern.search(text)
                if not match:
                    continue
                obj_value = match.expand(obj_template).strip()
                if len(obj_value) < 2:
                    continue
                fact = Fact(
                    agent_id=self._agent_id,
                    subject=subject,
                    predicate=predicate,
                    object=obj_value,
                    confidence=self._config.fact_extraction_confidence,
                )
                result = await self.semantic.learn(fact)
                learned.append(result)
            except Exception:
                log.debug("fact extraction skipped for pattern %s", pattern.pattern)
        return learned

    # ------------------------------------------------------------------
    # Flush / lifecycle
    # ------------------------------------------------------------------

    async def flush(self) -> list[Episode]:
        """Flush working memory → episodic, end current session."""
        await self._ensure_initialized()
        assert self.working is not None
        assert self.episodic is not None
        assert self._store is not None
        assert self._session is not None

        episodes = await self.working.flush_to_episodic(
            self._session_id, self._agent_id, self.episodic
        )
        self._session = self._session.end()
        await self._store.update_session(self._session)
        return episodes

    async def close(self) -> None:
        """Close all connections."""
        if self._initialized:
            assert self._store is not None
            assert self._vectors is not None
            await self._store.close()
            await self._vectors.close()
            self._initialized = False

    async def __aenter__(self) -> Memory:
        await self._ensure_initialized()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def agent_id(self) -> str:
        return self._agent_id
