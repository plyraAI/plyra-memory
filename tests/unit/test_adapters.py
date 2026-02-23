"""Tests for all five framework adapters."""

from __future__ import annotations

import pytest

from plyra_memory import Memory, MemoryConfig
from plyra_memory.adapters.autogen import MemoryHook
from plyra_memory.adapters.crewai import MemoryTool
from plyra_memory.adapters.langchain import PlyraMemory
from plyra_memory.adapters.langgraph import context_node, remember_node
from plyra_memory.adapters.openai_agents import (
    context_tool,
    get_openai_tools,
    remember_tool,
)

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter_config(tmp_path) -> MemoryConfig:
    return MemoryConfig(
        store_url=str(tmp_path / "adapter_test.db"),
        vectors_url=str(tmp_path / "adapter_test.index"),
        embed_model="mock",
        embed_dim=384,
        working_max_entries=50,
        cache_enabled=False,
    )


# ---------------------------------------------------------------------------
# LangGraph
# ---------------------------------------------------------------------------


class TestLangGraph:
    async def test_context_node_sets_memory_context(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            state = {"input": "hello"}
            result = await context_node(state, memory=mem)
            assert "memory_context" in result
            assert "memory_token_count" in result

    async def test_context_node_empty_input(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            state: dict = {}
            result = await context_node(state, memory=mem)
            assert "memory_context" not in result

    async def test_context_node_messages_fallback(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            state = {"messages": [{"role": "user", "content": "yo"}]}
            result = await context_node(state, memory=mem)
            assert "memory_context" in result

    async def test_remember_node_records(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            state = {
                "messages": [{"role": "assistant", "content": "Sure, here you go."}]
            }
            await remember_node(state, memory=mem)
            # Should have written to working + episodic
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count >= 1

    async def test_remember_node_empty_messages(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            state: dict = {"messages": []}
            result = await remember_node(state, memory=mem)
            assert result == state


# ---------------------------------------------------------------------------
# AutoGen
# ---------------------------------------------------------------------------


class TestAutoGen:
    async def test_on_message_returns_context(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            hook = MemoryHook(mem)
            result = await hook.on_message("what file?")
            assert "memory_context" in result
            assert "token_count" in result
            assert "memories_used" in result

    async def test_on_response_remembers(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            hook = MemoryHook(mem)
            await hook.on_response("Use main.py")
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count >= 1

    async def test_on_tool_call_remembers(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            hook = MemoryHook(mem)
            await hook.on_tool_call("search", "found 3 results")
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count >= 1


# ---------------------------------------------------------------------------
# LangChain
# ---------------------------------------------------------------------------


class TestLangChain:
    async def test_memory_variables(self, adapter_config, mock_embedder, mock_vectors):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            lc = PlyraMemory(mem)
            assert lc.memory_variables == ["memory_context"]

    async def test_aload_empty_query(self, adapter_config, mock_embedder, mock_vectors):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            lc = PlyraMemory(mem)
            result = await lc.aload_memory_variables({})
            assert result == {"memory_context": ""}

    async def test_aload_with_input(self, adapter_config, mock_embedder, mock_vectors):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            lc = PlyraMemory(mem)
            result = await lc.aload_memory_variables({"input": "hello"})
            assert "memory_context" in result

    async def test_asave_context_remembers_both(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            lc = PlyraMemory(mem)
            await lc.asave_context({"input": "hi"}, {"output": "hey!"})
            ws = await mem.working.get(mem.session_id)
            # Both user + assistant => 2 entries
            assert ws.entry_count >= 2

    async def test_aclear(self, adapter_config, mock_embedder, mock_vectors):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            lc = PlyraMemory(mem)
            await lc.asave_context({"input": "hi"}, {"output": "hey!"})
            await lc.aclear()
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count == 0


# ---------------------------------------------------------------------------
# CrewAI
# ---------------------------------------------------------------------------


class TestCrewAI:
    async def test_arun_returns_string(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            tool = MemoryTool(mem)
            result = await tool.arun("some query")
            assert isinstance(result, str)

    async def test_aremember_stores(self, adapter_config, mock_embedder, mock_vectors):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            tool = MemoryTool(mem)
            msg = await tool.aremember("user likes pizza")
            assert "Stored:" in msg
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count >= 1


# ---------------------------------------------------------------------------
# OpenAI Agents
# ---------------------------------------------------------------------------


class TestOpenAIAgents:
    async def test_context_tool_returns_string(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            result = await context_tool("what file?", memory=mem)
            assert isinstance(result, str)

    async def test_remember_tool_stores(
        self, adapter_config, mock_embedder, mock_vectors
    ):
        async with Memory(
            config=adapter_config,
            embedder=mock_embedder,
            vectors=mock_vectors,
        ) as mem:
            msg = await remember_tool("user asked about files", memory=mem)
            assert "Stored:" in msg
            ws = await mem.working.get(mem.session_id)
            assert ws.entry_count >= 1

    def test_get_openai_tools_schema(self, adapter_config, mock_embedder, mock_vectors):
        """Tool definitions have the right shape."""
        # get_openai_tools doesn't need an initialized Memory
        tools = get_openai_tools(None)
        assert len(tools) == 2
        names = {t["function"]["name"] for t in tools}
        assert "memory_context" in names
        assert "memory_remember" in names
        for t in tools:
            assert t["type"] == "function"
            assert "parameters" in t["function"]
