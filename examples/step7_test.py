"""Step 7 — cross-session persistence test."""

import asyncio
import shutil
from pathlib import Path

from plyra_memory import EpisodeEvent, FactRelation, Memory, MemoryConfig
from plyra_memory.schema import Episode, Fact

DB = "C:/Users/306589/Documents/plyra-memory/.tmp/persist_test.db"
VEC = "C:/Users/306589/Documents/plyra-memory/.tmp/persist_test_vectors"


async def session_one() -> str:
    config = MemoryConfig(store_url=DB, vectors_url=VEC, cache_enabled=False)
    async with Memory(config=config, agent_id="persist-agent") as memory:
        fact = Fact(
            agent_id=memory.agent_id,
            subject="user",
            predicate=FactRelation.PREFERS,
            object="dark mode",
            confidence=0.95,
        )
        await memory.semantic.learn(fact)

        episode = Episode(
            session_id=memory.session_id,
            agent_id=memory.agent_id,
            event=EpisodeEvent.USER_MESSAGE,
            content="I always use dark mode in my editor",
            importance=0.8,
        )
        await memory.episodic.record(episode)

        counts = await memory._store.count_memories()
        print(f"Session 1 stored: {counts}")
        return memory.session_id


async def session_two(first_session_id: str) -> None:
    config = MemoryConfig(store_url=DB, vectors_url=VEC, cache_enabled=False)
    # Different session_id — simulates a new conversation
    async with Memory(config=config, agent_id="persist-agent") as memory:
        assert memory.session_id != first_session_id, "should be new session"
        counts = await memory._store.count_memories()
        print(f"Session 2 sees: {counts}")
        assert counts["semantic"] >= 1, "semantic memory must persist across sessions"
        assert counts["episodic"] >= 1, "episodic memory must persist across sessions"

        # Can recall what was stored in session 1
        result = await memory.recall("what does the user prefer for their editor?")
        print(f"Cross-session recall: {len(result.results)} results")
        for r in result.results:
            print(f"  [{r.layer.value}] {r.content[:80]}")
        assert len(result.results) > 0, "must recall from previous session"
        print("CROSS-SESSION PERSISTENCE TEST PASSED")


async def run() -> None:
    # Clean up from any previous run
    for p in [Path(DB), Path(VEC)]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    sid = await session_one()
    await session_two(sid)


asyncio.run(run())
