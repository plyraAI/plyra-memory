"""Step 5 — memory-only test (no LLM call)."""

import asyncio

from plyra_memory import EpisodeEvent, FactRelation, Memory, MemoryConfig
from plyra_memory.schema import Episode, Fact, WorkingEntry


async def test():
    config = MemoryConfig(
        store_url="C:/Users/306589/Documents/plyra-memory/.tmp/chatbot_test.db",
        vectors_url="C:/Users/306589/Documents/plyra-memory/.tmp/chatbot_test_vectors",
        cache_enabled=False,
    )
    async with Memory(config=config, agent_id="test-chatbot") as memory:
        # Working memory
        entry = WorkingEntry(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            content="user said hello",
            importance=0.6,
            source="user_message",
        )
        await memory.working.add(entry)

        # Episodic
        episode = Episode(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            event=EpisodeEvent.AGENT_RESPONSE,
            content="User: hello. Assistant: Hi there!",
            importance=0.7,
        )
        await memory.episodic.record(episode)

        # Semantic
        fact = Fact(
            agent_id=memory.agent_id,
            subject="user",
            predicate=FactRelation.PREFERS,
            object="Python",
            confidence=0.9,
        )
        result = await memory.semantic.learn(fact)
        print(f"fact stored: {result.subject} {result.predicate.value} {result.object}")
        print(f"fingerprint: {result.fingerprint}")

        # Recall
        recall_result = await memory.recall("what does the user prefer?")
        print(f"recall returned {len(recall_result.results)} results")
        for r in recall_result.results:
            print(f"  [{r.layer.value}] score={r.score:.3f} | {r.content[:60]}")

        # Context
        ctx = await memory.context_for("what does the user like?", token_budget=512)
        print(f"context ({ctx.token_count} tokens, {ctx.memories_used} memories):")
        print(ctx.content[:200])

        counts = await memory._store.count_memories()
        print(f"memory counts: {counts}")
        assert counts["working"] >= 1
        assert counts["episodic"] >= 1
        assert counts["semantic"] >= 1
        print("ALL ASSERTIONS PASSED")


asyncio.run(test())
