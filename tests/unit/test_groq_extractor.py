"""Tests for Groq support in LLMExtractor and Memory.with_groq()."""

from unittest.mock import MagicMock, patch

import pytest

from plyra_memory.extraction.llm import LLMExtractor
from plyra_memory.schema import FactRelation


class MockGroqClient:
    """
    Simulates OpenAI client pointed at Groq base URL.
    Has chat.completions interface (OpenAI style).
    """

    class _Completions:
        async def create(self, **kwargs):
            class _Message:
                content = '{"facts": [{"subject": "user", "predicate": "prefers", "object": "Groq", "confidence": 0.9}]}'

            class _Choice:
                message = _Message()

            class _Response:
                choices = [_Choice()]

            return _Response()

    class _Chat:
        completions = None

    def __init__(self):
        self._client = MagicMock()
        self._client.base_url = "https://api.groq.com/openai/v1"
        self.base_url = "https://api.groq.com/openai/v1"
        self.chat = self._Chat()
        self.chat.completions = self._Completions()


def test_groq_detected_from_base_url():
    client = MockGroqClient()
    extractor = LLMExtractor(client)
    assert extractor._model == "llama-3.1-8b-instant"
    assert extractor._is_openai is True  # uses OpenAI interface


def test_groq_model_override():
    client = MockGroqClient()
    extractor = LLMExtractor(client, model="llama-3.3-70b-versatile")
    assert extractor._model == "llama-3.3-70b-versatile"


@pytest.mark.asyncio
async def test_groq_extraction_returns_facts():
    client = MockGroqClient()
    extractor = LLMExtractor(client)
    extractor._is_async = True
    extractor._is_openai = True

    facts = await extractor.extract("I prefer Groq for fast inference", "agent")
    assert isinstance(facts, list)
    assert len(facts) >= 1
    assert facts[0]["predicate"] == FactRelation.PREFERS


@pytest.mark.asyncio
async def test_groq_falls_back_on_error():
    """If Groq API fails, falls back to regex — never raises."""

    class FailingGroqClient:
        base_url = "https://api.groq.com/openai/v1"

        class chat:
            class completions:
                async def create(**kwargs):
                    raise ConnectionError("Groq API unreachable")

    extractor = LLMExtractor(FailingGroqClient(), model="llama-3.1-8b-instant")
    extractor._is_async = True
    extractor._is_openai = True

    # Should fall back to regex, not raise
    facts = await extractor.extract("I prefer Python", "agent")
    assert isinstance(facts, list)


def test_memory_with_groq_constructor():
    """Memory.with_groq() creates Memory with correct extractor."""
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.base_url = "https://api.groq.com/openai/v1"
        mock_openai.return_value = mock_client

        from plyra_memory import Memory

        memory = Memory.with_groq(api_key="gsk_test_key")

        # Verify OpenAI client was created with Groq base URL
        mock_openai.assert_called_once_with(
            api_key="gsk_test_key",
            base_url="https://api.groq.com/openai/v1",
        )
        assert memory._extractor is not None
        assert memory._llm_client is not None


def test_memory_with_groq_model_override():
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.base_url = "https://api.groq.com/openai/v1"
        mock_openai.return_value = mock_client

        from plyra_memory import Memory

        memory = Memory.with_groq(
            api_key="gsk_test",
            model="llama-3.3-70b-versatile",
        )
        assert memory._extractor._model == "llama-3.3-70b-versatile"
