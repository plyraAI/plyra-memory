"""
Episodic summarization.
Two-stage when session episodes exceed threshold:
  - Recent (within summarize_recent_days): LLM-summarized → one SUMMARY episode
  - Old (beyond summarize_recent_days): deleted entirely

If no LLM extractor configured, recent episodes are also deleted (not summarized).
"""

from __future__ import annotations

import asyncio
import logging

from ..config import MemoryConfig
from ..embedders.base import Embedder
from ..schema import Episode, EpisodeEvent, _utcnow
from ..storage.base import StorageBackend
from ..vectors.base import VectorBackend

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """Summarize the following conversation episodes into a single,
dense paragraph that captures all key information, decisions, preferences, and facts.
Focus on what would be most useful to remember for future conversations.
Be specific. Include names, technologies, preferences, and project details.
Do not include filler phrases like "The conversation covered..." — just state facts.

Episodes to summarize:
{episodes_text}

Summary (2-4 sentences, dense with specifics):"""


class EpisodicSummarizer:
    """
    Compresses old episodes into summaries to prevent unbounded DB growth.
    Called on session flush and optionally on server startup.
    """

    def __init__(
        self,
        store: StorageBackend,
        vectors: VectorBackend,
        embedder: Embedder,
        config: MemoryConfig,
        llm_client=None,  # optional — same client passed to LLMExtractor
    ):
        self._store = store
        self._vectors = vectors
        self._embedder = embedder
        self._config = config
        self._llm_client = llm_client

    async def maybe_summarize(self, session_id: str, agent_id: str) -> bool:
        """
        Check if session needs summarization, run if so.
        Returns True if summarization ran.
        Never raises.
        """
        if not self._config.summarize_enabled:
            return False

        try:
            count = await self._store.get_session_episode_count(session_id)
            if count < self._config.summarize_session_threshold:
                return False

            recent, old = await self._store.get_episodes_for_summarization(
                session_id=session_id,
                threshold=self._config.summarize_session_threshold,
            )

            ran = False

            # Stage 1: Summarize recent episodes with LLM (or delete if no LLM)
            if recent:
                if self._llm_client is not None:
                    summary_ep = await self._summarize_with_llm(
                        recent, session_id, agent_id
                    )
                    if summary_ep:
                        # Delete originals, keep summary
                        await self._delete_episodes([ep.id for ep in recent])
                        logger.info(
                            f"Summarized {len(recent)} recent episodes "
                            f"for session {session_id[:8]}"
                        )
                        ran = True
                else:
                    # No LLM — delete recent too (graceful degradation)
                    await self._delete_episodes([ep.id for ep in recent])
                    logger.info(
                        f"Deleted {len(recent)} recent episodes "
                        f"(no LLM configured for summarization)"
                    )
                    ran = True

            # Stage 2: Delete old episodes unconditionally
            if old:
                await self._delete_episodes([ep.id for ep in old])
                logger.info(
                    f"Deleted {len(old)} old episodes for session {session_id[:8]}"
                )
                ran = True

            return ran

        except Exception as e:
            logger.warning(f"Summarization failed for session {session_id}: {e}")
            return False

    async def _summarize_with_llm(
        self,
        episodes: list[Episode],
        session_id: str,
        agent_id: str,
    ) -> Episode | None:
        """Compress a list of episodes into a single SUMMARY episode."""
        try:
            # Build the episodes text
            chunks = []
            for ep in episodes[: self._config.summarize_max_episodes]:
                ts = ep.created_at.strftime("%Y-%m-%d %H:%M")
                chunks.append(f"[{ts}] {ep.event.value}: {ep.content[:300]}")
            episodes_text = "\n\n".join(chunks)

            prompt = SUMMARIZE_PROMPT.format(episodes_text=episodes_text)

            # Call LLM (detect style same as LLMExtractor)
            summary_text = await asyncio.wait_for(
                self._call_llm(prompt),
                timeout=30.0,  # longer timeout for summarization
            )

            if not summary_text or len(summary_text.strip()) < 20:
                return None

            # Create summary episode
            summary = Episode(
                session_id=session_id,
                agent_id=agent_id,
                event=EpisodeEvent.SUMMARY,
                content=f"[SUMMARY of {len(episodes)} episodes] {summary_text.strip()}",
                importance=0.9,  # summaries are high importance
                summarized=True,
                metadata={
                    "summarized_count": len(episodes),
                    "summarized_at": _utcnow().isoformat(),
                    "oldest_episode": min(ep.created_at for ep in episodes).isoformat(),
                    "newest_episode": max(ep.created_at for ep in episodes).isoformat(),
                },
            )
            saved = await self._store.save_episode(summary)

            # Embed and store in vectors
            embedding = await self._embedder.embed(saved.content)
            await self._vectors.upsert(
                id=saved.id,
                embedding=embedding,
                metadata={
                    "layer": "episodic",
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "importance": 0.9,
                    "is_summary": True,
                },
            )
            return saved

        except TimeoutError:
            logger.warning("Summarization LLM call timed out")
            return None
        except Exception as e:
            logger.warning(f"LLM summarization failed: {e}")
            return None

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM — same dual-style detection as LLMExtractor."""
        client = self._llm_client
        is_anthropic = hasattr(client, "messages") and not hasattr(client, "chat")
        is_async = "async" in type(client).__name__.lower()

        if is_anthropic:
            if is_async:
                resp = await client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                )
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        messages=[{"role": "user", "content": prompt}],
                    ),
                )
                # If result is a coroutine, await it
                if asyncio.iscoroutine(result):
                    resp = await result
                else:
                    resp = result
            return resp.content[0].text
        else:
            # OpenAI style
            if is_async:
                resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                )
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=512,
                        messages=[{"role": "user", "content": prompt}],
                    ),
                )
                # If result is a coroutine, await it
                if asyncio.iscoroutine(result):
                    resp = await result
                else:
                    resp = result
            return resp.choices[0].message.content

    async def _delete_episodes(self, episode_ids: list[str]) -> None:
        """Delete episodes from store and vectors."""
        if not episode_ids:
            return
        await self._store.delete_episodes_by_ids(episode_ids)
        for eid in episode_ids:
            try:
                await self._vectors.delete(eid)
            except Exception:
                pass  # vector deletion is best-effort
