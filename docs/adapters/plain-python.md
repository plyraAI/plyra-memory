# Plain Python

```python
import asyncio
from plyra_memory import Memory

async def main():
    async with Memory() as memory:
        await memory.remember("I am testing")
```
