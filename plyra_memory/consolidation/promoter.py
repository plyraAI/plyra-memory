"""
Auto-promotion: promotes frequently-accessed or old episodes to semantic facts.
Two triggers, whichever fires first:
  - access_count >= config.semantic_promotion_threshold
  - episode age >= config.promotion_age_days
"""

from __future__ import annotations

import logging

from ..config import MemoryConfig
from ..layers.semantic import SemanticLayer
from ..schema import Episode, Fact, FactRelation
from ..storage.base import StorageBackend

logger = logging.getLogger(__name__)


class AutoPromoter:
    """
    Checks episodes for promotion eligibility and promotes them to semantic facts.
    Called after every episodic.search() hit (non-blocking, background task).
    """

    def __init__(
        self,
        store: StorageBackend,
        semantic: SemanticLayer,
        config: MemoryConfig,
    ):
        self._store = store
        self._semantic = semantic
        self._config = config

    async def check_and_promote(self, agent_id: str) -> list[Fact]:
        """
        Find episodes eligible for promotion and promote them.
        Returns list of Facts created.
        Never raises — errors are logged and swallowed.
        """
        if not self._config.promotion_check_enabled:
            return []

        try:
            episodes = await self._store.get_episodes_for_promotion(
                agent_id=agent_id,
                min_access_count=self._config.semantic_promotion_threshold,
                min_age_days=self._config.promotion_age_days,
            )
            if not episodes:
                return []

            promoted: list[Fact] = []
            for episode in episodes:
                fact = await self._promote_episode(episode)
                if fact:
                    promoted.append(fact)
                    await self._store.mark_episode_promoted(episode.id, fact.id)
                    logger.debug(
                        f"Promoted episode {episode.id[:8]} → fact {fact.id[:8]} "
                        f"(access_count={episode.access_count})"
                    )
            return promoted

        except Exception as e:
            logger.warning(f"Auto-promotion failed: {e}")
            return []

    async def _promote_episode(self, episode: Episode) -> Fact | None:
        """Convert one episode to a semantic fact."""
        try:
            # Determine predicate from episode event type
            from ..schema import EpisodeEvent

            event_predicate_map = {
                EpisodeEvent.USER_MESSAGE: FactRelation.KNOWS,
                EpisodeEvent.AGENT_RESPONSE: FactRelation.KNOWS,
                EpisodeEvent.TOOL_RESULT: FactRelation.HAS,
                EpisodeEvent.TOOL_CALL: FactRelation.USES,
                EpisodeEvent.PLAN_CREATED: FactRelation.WORKS_ON,
                EpisodeEvent.CUSTOM: FactRelation.RELATED_TO,
            }
            predicate = event_predicate_map.get(episode.event, FactRelation.RELATED_TO)

            # Truncate long episodes to first 500 chars for semantic storage
            content = episode.content
            if len(content) > 500:
                content = content[:497] + "..."

            # Create Fact object first
            fact = Fact(
                agent_id=episode.agent_id,
                content=content,
                subject="agent",
                predicate=predicate,
                object=content[:200],
                confidence=min(0.5 + (episode.access_count * 0.1), 0.95),
                source_episode_id=episode.id,
                metadata={
                    "promoted_from_event": episode.event.value,
                    "original_session": episode.session_id,
                    "access_count_at_promotion": episode.access_count,
                },
            )
            # Now learn it
            result = await self._semantic.learn(fact)
            return result
        except Exception as e:
            logger.warning(f"Failed to promote episode {episode.id}: {e}")
            return None
