from ..schema import FactRelation
from .base import BaseExtractor


class RegexExtractor(BaseExtractor):
    """
    Heuristic pattern-matching extractor.
    Fast, no API calls, ~60% recall on natural language.
    Used as fallback when no LLMExtractor is configured.
    """

    PATTERNS: list[tuple[str, FactRelation, float]] = [
        # Identity
        ("my name is ", FactRelation.IS, 0.95),
        ("i'm called ", FactRelation.IS, 0.90),
        ("call me ", FactRelation.IS, 0.88),
        ("i am called ", FactRelation.IS, 0.90),
        # Preferences
        ("i prefer ", FactRelation.PREFERS, 0.88),
        ("i like ", FactRelation.PREFERS, 0.80),
        ("i love ", FactRelation.PREFERS, 0.85),
        ("i enjoy ", FactRelation.PREFERS, 0.80),
        ("i use ", FactRelation.USES, 0.82),
        ("i always use ", FactRelation.USES, 0.88),
        # Dislikes
        ("i don't like ", FactRelation.DISLIKES, 0.85),
        ("i do not like ", FactRelation.DISLIKES, 0.85),
        ("i hate ", FactRelation.DISLIKES, 0.88),
        ("i dislike ", FactRelation.DISLIKES, 0.85),
        ("i avoid ", FactRelation.DISLIKES, 0.80),
        # Work
        ("i'm working on ", FactRelation.WORKS_ON, 0.85),
        ("i am working on ", FactRelation.WORKS_ON, 0.85),
        ("i'm building ", FactRelation.WORKS_ON, 0.83),
        ("i'm developing ", FactRelation.WORKS_ON, 0.83),
        ("my project is ", FactRelation.WORKS_ON, 0.85),
        ("i work on ", FactRelation.WORKS_ON, 0.82),
        # Affiliation
        ("i work at ", FactRelation.BELONGS_TO, 0.88),
        ("i work for ", FactRelation.BELONGS_TO, 0.85),
        # Location
        ("i'm from ", FactRelation.LOCATED_IN, 0.88),
        ("i live in ", FactRelation.LOCATED_IN, 0.90),
        ("i'm based in ", FactRelation.LOCATED_IN, 0.88),
        # Knowledge
        ("i know ", FactRelation.KNOWS, 0.78),
        ("i understand ", FactRelation.KNOWS, 0.78),
        ("i'm familiar with ", FactRelation.KNOWS, 0.80),
    ]

    async def extract(self, text: str, agent_id: str) -> list[dict]:
        text_lower = text.lower()
        candidates = []

        def extract_after(pattern: str, max_words: int = 4) -> str | None:
            if pattern not in text_lower:
                return None
            idx = text_lower.index(pattern) + len(pattern)
            raw = text[idx : idx + 100]
            value = raw.split(".")[0].split(",")[0].split("!")[0].split("?")[0].strip()
            words = value.split()
            return " ".join(words[:max_words]) if words else None

        for pattern, predicate, confidence in self.PATTERNS:
            value = extract_after(pattern)
            if value and len(value) > 1:
                candidates.append(
                    {
                        "subject": "user",
                        "predicate": predicate,
                        "object_": value,
                        "confidence": confidence,
                    }
                )

        # Deduplicate: keep highest confidence per predicate
        seen: dict[str, dict] = {}
        for c in candidates:
            key = c["predicate"].value
            if key not in seen or c["confidence"] > seen[key]["confidence"]:
                seen[key] = c

        return list(seen.values())
