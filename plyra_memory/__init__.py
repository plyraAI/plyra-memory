"""
plyra-memory – typed, three-layer cognitive memory for AI agents.

Features: Memory.with_groq() — Groq LLM extraction (llama-3.1-8b-instant)
"""

__version__ = "0.3.0"

from plyra_memory.config import MemoryConfig
from plyra_memory.consolidation.promoter import AutoPromoter
from plyra_memory.consolidation.summarizer import EpisodicSummarizer
from plyra_memory.extraction.base import BaseExtractor
from plyra_memory.extraction.llm import LLMExtractor
from plyra_memory.extraction.regex import RegexExtractor
from plyra_memory.memory import Memory
from plyra_memory.schema import (
    ContextResult,
    Episode,
    EpisodeEvent,
    EpisodicQuery,
    Fact,
    FactRelation,
    HealthStatus,
    ImportanceLevel,
    MemoryLayer,
    RankedMemory,
    RecallRequest,
    RecallResult,
    SemanticQuery,
    Session,
    WorkingEntry,
    WorkingMemoryState,
)

__all__ = [
    "AutoPromoter",
    "BaseExtractor",
    "ContextResult",
    "Episode",
    "EpisodeEvent",
    "EpisodicQuery",
    "EpisodicSummarizer",
    "Fact",
    "FactRelation",
    "HealthStatus",
    "ImportanceLevel",
    "LLMExtractor",
    "Memory",
    "MemoryConfig",
    "MemoryLayer",
    "RankedMemory",
    "RecallRequest",
    "RecallResult",
    "RegexExtractor",
    "SemanticQuery",
    "Session",
    "WorkingEntry",
    "WorkingMemoryState",
    "__version__",
]
