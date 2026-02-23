"""plyra-memory configuration — pydantic-settings based config with env var support."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from plyra_memory.schema import PlyraEnv


class MemoryConfig(BaseSettings):
    """Configuration for plyra-memory. All fields map to PLYRA_* env vars."""

    model_config = SettingsConfigDict(
        env_prefix="PLYRA_",
        env_file=".env",
        extra="ignore",
    )

    # Environment
    env: PlyraEnv = PlyraEnv.LOCAL

    # Storage (SQLite only for v0.1)
    store_url: str = "~/.plyra/memory.db"

    # Vectors (ChromaDB only for v0.1)
    vectors_url: str = "~/.plyra/memory.index"

    # Embedder (sentence-transformers only for v0.1)
    embed_model: str = "all-MiniLM-L6-v2"
    embed_dim: int = 384
    embedding_cache_size: int = 2048

    # Working memory
    working_max_entries: int = 50
    working_max_tokens: int = 4_096

    # Episodic memory
    episodic_default_importance: float = 0.5
    episodic_summarize_at_tokens: int = 8_000

    # Semantic memory
    semantic_promotion_threshold: int = 3
    semantic_default_confidence: float = 0.8
    semantic_decay_lambda: float = 0.05

    # Retrieval
    chroma_collection_name: str = "plyra_memory"
    fact_extraction_confidence: float = 0.85

    # Semantic cache
    cache_enabled: bool = True
    cache_similarity_threshold: float = 0.92
    cache_max_size: int = 1_000
    cache_ttl_seconds: int = 3_600

    # Context injection defaults
    default_token_budget: int = 2_048
    default_similarity_weight: float = 0.5
    default_recency_weight: float = 0.3
    default_importance_weight: float = 0.2

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 7700

    # Logging
    log_level: str = "INFO"

    @classmethod
    def default(cls) -> MemoryConfig:
        """Return config with all defaults."""
        return cls()
