"""Unit tests for plyra_memory.config."""

from __future__ import annotations

from plyra_memory.config import MemoryConfig


class TestMemoryConfig:
    def test_defaults(self):
        cfg = MemoryConfig.default()
        assert cfg.embed_dim == 384
        assert cfg.working_max_entries == 50
        assert cfg.server_port == 7700
        assert cfg.embed_model == "all-MiniLM-L6-v2"
        assert "memory.db" in cfg.store_url
        assert "memory.index" in cfg.vectors_url

    def test_custom_values(self, tmp_path):
        cfg = MemoryConfig(
            store_url=str(tmp_path / "custom.db"),
            vectors_url=str(tmp_path / "custom.index"),
            embed_dim=768,
            working_max_entries=100,
            server_port=8080,
        )
        assert cfg.embed_dim == 768
        assert cfg.working_max_entries == 100
        assert cfg.server_port == 8080

    def test_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PLYRA_STORE_URL", str(tmp_path / "env.db"))
        monkeypatch.setenv("PLYRA_LOG_LEVEL", "DEBUG")
        cfg = MemoryConfig()
        assert "env.db" in cfg.store_url
        assert cfg.log_level == "DEBUG"

    def test_cache_settings(self):
        cfg = MemoryConfig.default()
        assert cfg.cache_enabled is True
        assert cfg.cache_max_size > 0
        assert cfg.cache_ttl_seconds > 0

    def test_new_production_fields(self):
        cfg = MemoryConfig.default()
        assert cfg.embedding_cache_size == 2048
        assert cfg.chroma_collection_name == "plyra_memory"
        assert cfg.fact_extraction_confidence == 0.85
        assert cfg.semantic_decay_lambda == 0.05
