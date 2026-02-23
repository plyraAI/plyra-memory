"""Step 6 — fact extraction test (no LLM call)."""

import asyncio

# Import the extraction function from the chatbot example
from examples.chatbot import _extract_and_store_facts
from plyra_memory import Memory, MemoryConfig
from plyra_memory.schema import SemanticQuery


async def test():
    config = MemoryConfig(
        store_url="C:/Users/306589/Documents/plyra-memory/.tmp/fact_test.db",
        vectors_url="C:/Users/306589/Documents/plyra-memory/.tmp/fact_test_vectors",
        cache_enabled=False,
    )
    async with Memory(config=config, agent_id="fact-test-agent") as memory:
        test_messages = [
            "My name is Alex",
            "I prefer Python over JavaScript",
            "I don't like verbose frameworks",
            "I'm working on a LangGraph pipeline",
            "I'm based in San Francisco",
        ]
        for msg in test_messages:
            print(f"processing: {msg}")
            await _extract_and_store_facts(memory, msg)

        facts = await memory.semantic.query(
            SemanticQuery(agent_id=memory.agent_id, top_k=20)
        )
        print(f"stored {len(facts)} facts:")
        for f in facts:
            print(
                f"  {f.subject} [{f.predicate.value}] "
                f"{f.object} (conf={f.confidence:.2f})"
            )

        assert len(facts) >= 4, f"expected 4+ facts, got {len(facts)}"
        print("FACT EXTRACTION TEST PASSED")


asyncio.run(test())
