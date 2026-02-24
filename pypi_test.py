import asyncio, tempfile
from pathlib import Path

async def test():
    tmp = tempfile.mkdtemp()
    from plyra_memory import Memory, MemoryConfig, __version__
    print(f'plyra-memory {__version__} installed from PyPI')

    config = MemoryConfig(
        store_url=str(Path(tmp) / 'release.db'),
        vectors_url=str(Path(tmp) / 'release_vectors'),
        cache_enabled=False,
    )
    async with Memory(config=config, agent_id='release-test') as m:
        result = await m.remember('my name is Taylor, I prefer TypeScript')
        assert len(result['facts']) >= 1, 'fact extraction failed'
        ctx = await m.context_for('what does the user prefer?', token_budget=512)
        assert ctx.content, 'context is empty'
        print(f'End-to-end OK: {len(result["facts"])} facts, context={ctx.token_count} tokens')

    print('POST-PUBLISH SMOKE TEST PASSED')
    import shutil; shutil.rmtree(tmp, ignore_errors=True)

asyncio.run(test())
