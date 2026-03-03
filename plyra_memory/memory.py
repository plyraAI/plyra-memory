"""plyra-memory — main public API."""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING, Any

from plyra_memory.config import MemoryConfig
from plyra_memory.schema import (
    ContextResult,
    Episode,
    EpisodeEvent,
    Fact,
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
        extractor=None,
        llm_client=None,
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
        self._extractor = extractor
        self._llm_client = llm_client

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
        self._promoter = None
        self._summarizer = None
        self._bg_tasks: set = set()

        # HTTP backend mode
        self._use_http = False
        self._http_backend = None

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        # Auto-detect server mode
        server_url = os.environ.get("PLYRA_SERVER_URL") or self._config.__dict__.get(
            "server_url"
        )
        api_key = os.environ.get("PLYRA_API_KEY")

        if server_url and api_key:
            from plyra_memory.backends.http import HTTPMemoryBackend

            self._http_backend = HTTPMemoryBackend(
                server_url=server_url,
                api_key=api_key,
                agent_id=self._agent_id,
            )
            self._use_http = True
            self._initialized = True
            log.info("Memory initialized in HTTP mode (server=%s)", server_url)
            return

        self._use_http = False
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

        # Auto-configure extractor from env vars if not explicitly provided
        if self._extractor is None:
            groq_key = getattr(self._config, "groq_api_key", None)
            anthropic_key = getattr(self._config, "anthropic_api_key", None)
            openai_key = getattr(self._config, "openai_api_key", None)

            if groq_key:
                try:
                    from openai import OpenAI

                    from .extraction.llm import LLMExtractor

                    client = OpenAI(
                        api_key=groq_key,
                        base_url="https://api.groq.com/openai/v1",
                    )
                    self._extractor = LLMExtractor(client, model="llama-3.1-8b-instant")
                    self._llm_client = client
                    log.debug(
                        "LLM extraction: Groq llama-3.1-8b-instant (from GROQ_API_KEY)"
                    )
                except ImportError:
                    log.warning(
                        "GROQ_API_KEY set but openai package not installed "
                        "— using regex"
                    )

            elif anthropic_key:
                try:
                    import anthropic

                    from .extraction.llm import LLMExtractor

                    client = anthropic.Anthropic(api_key=anthropic_key)
                    self._extractor = LLMExtractor(client)
                    self._llm_client = client
                    log.debug(
                        "LLM extraction: Anthropic claude-haiku "
                        "(from ANTHROPIC_API_KEY)"
                    )
                except ImportError:
                    log.warning(
                        "ANTHROPIC_API_KEY set but anthropic package not installed"
                    )

            elif openai_key:
                try:
                    from openai import OpenAI

                    from .extraction.llm import LLMExtractor

                    client = OpenAI(api_key=openai_key)
                    self._extractor = LLMExtractor(client)
                    self._llm_client = client
                    log.debug(
                        "LLM extraction: OpenAI gpt-4o-mini (from OPENAI_API_KEY)"
                    )
                except ImportError:
                    log.warning("OPENAI_API_KEY set but openai package not installed")

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

        # Initialize consolidation components
        from plyra_memory.consolidation.promoter import AutoPromoter
        from plyra_memory.consolidation.summarizer import EpisodicSummarizer

        self._promoter = AutoPromoter(self._store, self.semantic, self._config)
        self._summarizer = EpisodicSummarizer(
            self._store, self._vectors, self._embedder, self._config, self._llm_client
        )

        self._retrieval = HybridRetrieval(
            self.working,
            self.episodic,
            self.semantic,
            self._embedder,
            self._config,
            promoter=self._promoter,
            bg_tasks=self._bg_tasks,
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

        # Route to HTTP backend if in server mode
        if self._use_http:
            return await self._http_backend.recall(query, top_k)

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
        result = await self._retrieval.recall(request, query_embedding=query_embedding)

        if self._config.cache_enabled:
            await self._cache.set(query, result, query_embedding=query_embedding)

        return result

    async def context_for(
        self,
        query: str,
        token_budget: int | None = None,
        layers: list[Any] | None = None,
    ) -> ContextResult:
        """Build a context string within a token budget."""
        await self._ensure_initialized()

        # Route to HTTP backend if in server mode
        if self._use_http:
            return await self._http_backend.context_for(
                query, token_budget or self._config.default_token_budget
            )

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

        # Route to HTTP backend if in server mode
        if self._use_http:
            return await self._http_backend.remember(
                content, importance, source, metadata
            )

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
        results["working_entry"] = results["working"]

        # 2. Episodic layer
        episode_obj = Episode(
            session_id=self._session_id,
            agent_id=self._agent_id,
            event=event,
            content=content,
            importance=importance,
            tool_name=tool_name,
            metadata=meta,
        )
        results["episodic"] = await self.episodic.record(episode_obj)
        results["episode"] = results["episodic"]

        # 3. Semantic — extract facts (background task, non-blocking)
        async def _bg_extract():
            try:
                return await self._extract_and_learn(content)
            except Exception:
                return []

        # Fire and forget — extraction runs after remember() returns
        import asyncio

        task = asyncio.create_task(_bg_extract())
        results["facts"] = []  # facts not available synchronously anymore

        # Store task reference to prevent GC
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

        return results

    async def _extract_and_learn(self, text: str) -> list[Fact]:
        """
        Extract facts from text using configured extractor.
        Falls back to RegexExtractor if no LLMExtractor configured.
        """
        assert self.semantic is not None
        from plyra_memory.extraction.regex import RegexExtractor

        extractor = self._extractor or RegexExtractor()

        candidates = await extractor.extract(text, self._agent_id)
        stored = []
        for kwargs in candidates:
            try:
                # Create Fact object from extracted data
                fact = Fact(
                    agent_id=self._agent_id,
                    content=(
                        f"{kwargs['subject']} "
                        f"{kwargs['predicate'].value} "
                        f"{kwargs['object_']}"
                    ),
                    subject=kwargs["subject"],
                    predicate=kwargs["predicate"],
                    object=kwargs["object_"],
                    confidence=kwargs.get("confidence", 0.8),
                    source_episode_id=kwargs.get("source_episode_id"),
                    metadata=kwargs.get("metadata", {}),
                )
                # Store the fact
                result = await self.semantic.learn(fact)
                stored.append(result)
            except Exception:
                pass
        return stored

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

        # Trigger summarization check after flush
        if self._summarizer:
            import asyncio

            task = asyncio.create_task(
                self._summarizer.maybe_summarize(self._session_id, self._agent_id)
            )
            self._bg_tasks.add(task)
            task.add_done_callback(self._bg_tasks.discard)

        return episodes

    async def close(self) -> None:
        """Close all connections."""
        if self._use_http and self._http_backend:
            await self._http_backend.close()
            self._initialized = False
            return

        if self._initialized:
            assert self._store is not None
            assert self._vectors is not None

            # Cancel all pending background tasks before closing the DB
            import asyncio

            for task in list(self._bg_tasks):
                task.cancel()
            if self._bg_tasks:
                await asyncio.gather(*self._bg_tasks, return_exceptions=True)
            self._bg_tasks.clear()

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

    @classmethod
    def with_anthropic(
        cls,
        api_key: str,
        agent_id: str = "default-agent",
        config: MemoryConfig | None = None,
        **kwargs,
    ) -> Memory:
        """Anthropic convenience constructor for extraction + summarization."""
        import anthropic

        from plyra_memory.extraction.llm import LLMExtractor

        client = anthropic.Anthropic(api_key=api_key)
        extractor = LLMExtractor(client)
        return cls(
            config=config,
            agent_id=agent_id,
            extractor=extractor,
            llm_client=client,
            **kwargs,
        )

    @classmethod
    def with_openai(
        cls,
        api_key: str,
        agent_id: str = "default-agent",
        config: MemoryConfig | None = None,
        **kwargs,
    ) -> Memory:
        """OpenAI convenience constructor for extraction + summarization."""
        import openai

        from plyra_memory.extraction.llm import LLMExtractor

        client = openai.OpenAI(api_key=api_key)
        extractor = LLMExtractor(client)
        return cls(
            config=config,
            agent_id=agent_id,
            extractor=extractor,
            llm_client=client,
            **kwargs,
        )

    @classmethod
    def with_groq(
        cls,
        api_key: str,
        agent_id: str = "default-agent",
        config: MemoryConfig | None = None,
        model: str = "llama-3.1-8b-instant",
        **kwargs,
    ) -> Memory:
        """
        Convenience constructor with Groq client for extraction + summarization.

        Groq provides OpenAI-compatible API with free tier and fast inference.
        llama-3.1-8b-instant: ~800 tokens/second, generous free tier.

        Usage:
            memory = Memory.with_groq(api_key="gsk_...")
            memory = Memory.with_groq(
                api_key="gsk_...",
                model="llama-3.3-70b-versatile",  # smarter model
            )
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for Groq support. "
                "Install with: pip install openai"
            )
        from .extraction.llm import LLMExtractor

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        extractor = LLMExtractor(client, model=model)
        return cls(
            config=config,
            agent_id=agent_id,
            extractor=extractor,
            llm_client=client,
            **kwargs,
        )
