"""
LLM-based fact extractor.
Works with any client that has a messages.create() interface
(Anthropic, OpenAI, or any compatible API).
"""

from __future__ import annotations

import asyncio
import json
import logging

from ..schema import FactRelation
from .base import BaseExtractor
from .regex import RegexExtractor

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """You are a fact extraction engine. Extract structured facts
from the user's message.

Rules:
- Only extract facts the user states about themselves (subject = "user")
- Only extract clear, explicit statements — not implications or guesses
- Use ONLY these predicates: is, prefers, dislikes, uses, works_on, belongs_to,
  located_in, knows, has, related_to
- Confidence: 0.95 for very explicit ("my name is X"), 0.8 for clear
  ("I prefer X"), 0.7 for implied
- Return ONLY valid JSON. No explanation. No markdown. No preamble.
- If no facts, return: {{"facts": []}}

Output format:
{{
  "facts": [
    {{"subject": "user", "predicate": "is", "object": "Alex", "confidence": 0.95}},
    {{"subject": "user", "predicate": "prefers", "object": "Python", "confidence": 0.8}}
  ]
}}

User message: {text}"""


class LLMExtractor(BaseExtractor):
    """
    LLM-based fact extractor. Accepts any client with a messages API.

    Supports:
      - anthropic.Anthropic()
      - anthropic.AsyncAnthropic()
      - openai.OpenAI()
      - openai.AsyncOpenAI()
      - Any object with .chat.completions.create() or .messages.create()

    Falls back to RegexExtractor on any error.

    Usage:
        import anthropic
        extractor = LLMExtractor(anthropic.Anthropic())

        import openai
        extractor = LLMExtractor(openai.OpenAI())

        memory = Memory(extractor=extractor)
    """

    # Predicate string → FactRelation mapping
    PREDICATE_MAP: dict[str, FactRelation] = {
        "is": FactRelation.IS,
        "prefers": FactRelation.PREFERS,
        "dislikes": FactRelation.DISLIKES,
        "uses": FactRelation.USES,
        "works_on": FactRelation.WORKS_ON,
        "belongs_to": FactRelation.BELONGS_TO,
        "located_in": FactRelation.LOCATED_IN,
        "knows": FactRelation.KNOWS,
        "has": FactRelation.HAS,
        "related_to": FactRelation.RELATED_TO,
        "learned_from": FactRelation.LEARNED_FROM,
    }

    def __init__(
        self,
        client,
        model: str | None = None,
        max_tokens: int = 512,
        timeout: float = 10.0,
    ):
        self._client = client
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._fallback = RegexExtractor()

        # Auto-detect client type and set default model
        client_type = type(client).__module__
        if model:
            self._model = model
        elif "anthropic" in client_type:
            self._model = "claude-haiku-4-5-20251001"
        elif "openai" in client_type:
            self._model = "gpt-4o-mini"
        else:
            self._model = model or "claude-haiku-4-5-20251001"

        # Detect if client is async
        self._is_async = "async" in type(client).__name__.lower() or hasattr(
            client, "_async_httpx_client"
        )

        # Detect API style (anthropic vs openai)
        self._is_anthropic = hasattr(client, "messages") and not hasattr(client, "chat")
        self._is_openai = hasattr(client, "chat") and hasattr(
            client.chat, "completions"
        )

    async def extract(self, text: str, agent_id: str) -> list[dict]:
        """
        Extract facts via LLM. Falls back to regex on any error.
        Enforces self._timeout — never blocks remember() for more than 10s.
        """
        # Skip extraction for very short or clearly non-informational text
        if len(text.strip()) < 10:
            return []

        try:
            raw = await asyncio.wait_for(
                self._call_llm(text),
                timeout=self._timeout,
            )
            return self._parse_response(raw)
        except TimeoutError:
            logger.warning(
                f"LLM extraction timed out after {self._timeout}s, using regex"
            )
            return await self._fallback.extract(text, agent_id)
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, using regex fallback")
            return await self._fallback.extract(text, agent_id)

    async def _call_llm(self, text: str) -> str:
        prompt = EXTRACT_PROMPT.format(text=text)

        if self._is_anthropic:
            return await self._call_anthropic(prompt)
        elif self._is_openai:
            return await self._call_openai(prompt)
        else:
            # Generic: try anthropic style first, then openai style
            try:
                return await self._call_anthropic(prompt)
            except Exception:
                return await self._call_openai(prompt)

    async def _call_anthropic(self, prompt: str) -> str:
        if self._is_async:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        else:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )
        return response.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        if self._is_async:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        else:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )
        return response.choices[0].message.content

    def _parse_response(self, raw: str) -> list[dict]:
        """Parse LLM JSON response into fact dicts."""
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            data = json.loads(cleaned)
            facts = data.get("facts", [])
            result = []
            for f in facts:
                predicate_str = f.get("predicate", "").lower().replace(" ", "_")
                predicate = self.PREDICATE_MAP.get(predicate_str)
                if not predicate:
                    continue
                obj = str(f.get("object", "")).strip()
                subj = str(f.get("subject", "user")).strip()
                conf = float(f.get("confidence", 0.8))
                if obj and subj and 0.0 <= conf <= 1.0:
                    result.append(
                        {
                            "subject": subj,
                            "predicate": predicate,
                            "object_": obj,
                            "confidence": min(conf, 1.0),
                        }
                    )
            return result
        except Exception as e:
            logger.warning(f"Failed to parse LLM extraction response: {e}")
            return []
