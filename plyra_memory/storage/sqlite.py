"""SQLite storage backend using aiosqlite with WAL mode."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from plyra_memory.config import MemoryConfig
from plyra_memory.schema import (
    Episode,
    EpisodeEvent,
    EpisodicQuery,
    Fact,
    FactRelation,
    SemanticQuery,
    Session,
    WorkingEntry,
)
from plyra_memory.storage.base import StorageBackend

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema version — bump when tables change.
# ---------------------------------------------------------------------------
_SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _dt_to_str(dt: datetime) -> str:
    return dt.isoformat()


def _str_to_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _dict_to_json(d: dict | list | None) -> str:
    return json.dumps(d) if d else "{}"


def _json_to_dict(s: str | None) -> dict:
    return json.loads(s) if s else {}


# ---------------------------------------------------------------------------
# SQLiteStore
# ---------------------------------------------------------------------------


class SQLiteStore(StorageBackend):
    """Async SQLite storage with WAL mode."""

    def __init__(self, db_path: str, config: MemoryConfig) -> None:
        self._db_path = Path(db_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: aiosqlite.Connection | None = None
        self._config = config

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(str(self._db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute("PRAGMA synchronous=NORMAL")

        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                created_at TEXT NOT NULL,
                ended_at TEXT,
                framework TEXT,
                metadata TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS working_entries (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.5,
                source TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_working_session
                ON working_entries(session_id);

            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                tool_error TEXT,
                importance REAL NOT NULL DEFAULT 0.5,
                access_count INTEGER NOT NULL DEFAULT 0,
                sequence_num INTEGER NOT NULL DEFAULT 0,
                promoted INTEGER NOT NULL DEFAULT 0,
                promoted_to TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_episodes_session
                ON episodes(session_id);
            CREATE INDEX IF NOT EXISTS idx_episodes_agent
                ON episodes(agent_id);
            CREATE INDEX IF NOT EXISTS idx_episodes_event
                ON episodes(event);
            CREATE INDEX IF NOT EXISTS idx_episodes_created
                ON episodes(created_at);

            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.8,
                importance REAL NOT NULL DEFAULT 0.5,
                access_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                last_confirmed TEXT NOT NULL,
                ttl_days INTEGER,
                source_episode_id TEXT,
                promoted_from TEXT,
                fingerprint TEXT NOT NULL UNIQUE,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_fingerprint
                ON facts(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_facts_agent
                ON facts(agent_id);
            """
        )
        await self._conn.commit()

        # Initialise or check schema version
        cursor = await self._conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            await self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
            await self._conn.commit()
            log.info(
                "Initialised SQLite store at %s (schema v%d)",
                self._db_path,
                _SCHEMA_VERSION,
            )
        else:
            existing = row[0]
            if existing != _SCHEMA_VERSION:
                log.warning(
                    "Schema version mismatch: db=%d code=%d — "
                    "run migrations or recreate the database",
                    existing,
                    _SCHEMA_VERSION,
                )
            else:
                log.debug(
                    "Opened SQLite store at %s (schema v%d)",
                    self._db_path,
                    existing,
                )

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            log.debug("Closed SQLite store")

    # ---- helpers ----

    def _ensure_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("SQLiteStore not initialized — call initialize() first")
        return self._conn

    async def begin(self) -> None:
        """Begin an explicit transaction (for batch writes)."""
        conn = self._ensure_conn()
        await conn.execute("BEGIN")

    async def commit(self) -> None:
        """Commit the current transaction."""
        conn = self._ensure_conn()
        await conn.commit()

    # ---- Sessions ----

    async def save_session(self, session: Session) -> Session:
        conn = self._ensure_conn()
        await conn.execute(
            """INSERT INTO sessions
               (id, agent_id, user_id, created_at, ended_at, framework, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session.id,
                session.agent_id,
                session.user_id,
                _dt_to_str(session.created_at),
                _dt_to_str(session.ended_at) if session.ended_at else None,
                session.framework,
                _dict_to_json(session.metadata),
            ),
        )
        await conn.commit()
        return session

    async def get_session(self, session_id: str) -> Session | None:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    async def update_session(self, session: Session) -> Session:
        conn = self._ensure_conn()
        await conn.execute(
            """UPDATE sessions SET agent_id=?, user_id=?, ended_at=?,
               framework=?, metadata=? WHERE id=?""",
            (
                session.agent_id,
                session.user_id,
                _dt_to_str(session.ended_at) if session.ended_at else None,
                session.framework,
                _dict_to_json(session.metadata),
                session.id,
            ),
        )
        await conn.commit()
        return session

    def _row_to_session(self, row: aiosqlite.Row) -> Session:
        return Session(
            id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"] or None,
            created_at=_str_to_dt(row["created_at"]),
            ended_at=_str_to_dt(row["ended_at"]) if row["ended_at"] else None,
            framework=row["framework"] or None,
            metadata=_json_to_dict(row["metadata"]),
        )

    # ---- Working Entries ----

    async def save_working_entry(self, entry: WorkingEntry) -> WorkingEntry:
        conn = self._ensure_conn()
        await conn.execute(
            """INSERT INTO working_entries
               (id, session_id, agent_id, content,
                importance, source, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                entry.session_id,
                entry.agent_id,
                entry.content,
                entry.importance,
                entry.source,
                _dt_to_str(entry.created_at),
                _dict_to_json(entry.metadata),
            ),
        )
        await conn.commit()
        return entry

    async def get_working_entries(self, session_id: str) -> list[WorkingEntry]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM working_entries WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_working(r) for r in rows]

    async def delete_working_entries(self, session_id: str) -> int:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM working_entries WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        count = row[0] if row else 0
        await conn.execute(
            "DELETE FROM working_entries WHERE session_id = ?", (session_id,)
        )
        await conn.commit()
        return count

    async def delete_working_entry_by_id(self, entry_id: str) -> bool:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "DELETE FROM working_entries WHERE id = ?", (entry_id,)
        )
        await conn.commit()
        return cursor.rowcount > 0

    def _row_to_working(self, row: aiosqlite.Row) -> WorkingEntry:
        return WorkingEntry(
            id=row["id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"] or "",
            content=row["content"],
            importance=row["importance"],
            source=row["source"] or None,
            created_at=_str_to_dt(row["created_at"]),
            metadata=_json_to_dict(row["metadata"]),
        )

    # ---- Episodes ----

    async def save_episode(self, episode: Episode) -> Episode:
        conn = self._ensure_conn()
        await conn.execute(
            """INSERT INTO episodes
               (id, session_id, agent_id, event, content, tool_name,
                tool_input, tool_output, tool_error, importance, access_count,
                sequence_num, promoted, promoted_to, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode.id,
                episode.session_id,
                episode.agent_id,
                episode.event.value,
                episode.content,
                episode.tool_name,
                _dict_to_json(episode.tool_input) if episode.tool_input else None,
                episode.tool_output,
                episode.tool_error,
                episode.importance,
                episode.access_count,
                episode.sequence_num,
                1 if episode.promoted else 0,
                episode.promoted_to,
                _dt_to_str(episode.created_at),
                _dict_to_json(episode.metadata),
            ),
        )
        await conn.commit()
        return episode

    async def get_episode(self, episode_id: str) -> Episode | None:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM episodes WHERE id = ?", (episode_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_episode(row)

    async def get_episodes(self, query: EpisodicQuery) -> list[Episode]:
        conn = self._ensure_conn()
        conditions: list[str] = []
        params: list[object] = []

        if query.session_id:
            conditions.append("session_id = ?")
            params.append(query.session_id)
        if query.agent_id:
            conditions.append("agent_id = ?")
            params.append(query.agent_id)
        if query.event_types:
            placeholders = ",".join("?" for _ in query.event_types)
            conditions.append(f"event IN ({placeholders})")
            params.extend(e.value for e in query.event_types)
        if query.tool_names:
            placeholders = ",".join("?" for _ in query.tool_names)
            conditions.append(f"tool_name IN ({placeholders})")
            params.extend(query.tool_names)
        if query.since:
            conditions.append("created_at >= ?")
            params.append(_dt_to_str(query.since))
        if query.until:
            conditions.append("created_at <= ?")
            params.append(_dt_to_str(query.until))
        if query.min_importance > 0:
            conditions.append("importance >= ?")
            params.append(query.min_importance)
        if not query.include_promoted:
            conditions.append("promoted = 0")

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = (
            f"SELECT * FROM episodes WHERE {where} "  # noqa: S608
            "ORDER BY created_at DESC LIMIT ?"
        )
        params.append(query.top_k)

        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [self._row_to_episode(r) for r in rows]

    async def increment_episode_access(self, episode_id: str) -> int:
        conn = self._ensure_conn()
        await conn.execute(
            "UPDATE episodes SET access_count = access_count + 1 WHERE id = ?",
            (episode_id,),
        )
        await conn.commit()
        cursor = await conn.execute(
            "SELECT access_count FROM episodes WHERE id = ?", (episode_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def mark_episode_promoted(self, episode_id: str, fact_id: str) -> None:
        conn = self._ensure_conn()
        await conn.execute(
            "UPDATE episodes SET promoted = 1, promoted_to = ? WHERE id = ?",
            (fact_id, episode_id),
        )
        await conn.commit()

    def _row_to_episode(self, row: aiosqlite.Row) -> Episode:
        return Episode(
            id=row["id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            event=EpisodeEvent(row["event"]),
            content=row["content"],
            tool_name=row["tool_name"] or None,
            tool_input=(json.loads(row["tool_input"]) if row["tool_input"] else None),
            tool_output=row["tool_output"] or None,
            tool_error=row["tool_error"] or None,
            importance=row["importance"],
            access_count=row["access_count"],
            sequence_num=row["sequence_num"],
            promoted=bool(row["promoted"]),
            promoted_to=row["promoted_to"] or None,
            created_at=_str_to_dt(row["created_at"]),
            metadata=_json_to_dict(row["metadata"]),
        )

    # ---- Facts ----

    async def save_fact(self, fact: Fact) -> Fact:
        conn = self._ensure_conn()
        # Check for fingerprint collision → merge and update
        existing = await self.get_fact_by_fingerprint(fact.fingerprint)
        if existing:
            # Merge: keep original id/created_at/promoted_from, update rest
            merged_confidence = (existing.confidence + fact.confidence) / 2.0
            now = _dt_to_str(datetime.now(UTC))
            await conn.execute(
                """UPDATE facts SET confidence=?, last_confirmed=?,
                   access_count=access_count+1, content=?, importance=?,
                   metadata=?, object=?
                   WHERE fingerprint=?""",
                (
                    merged_confidence,
                    now,
                    fact.content,
                    fact.importance,
                    _dict_to_json(fact.metadata),
                    fact.object,
                    fact.fingerprint,
                ),
            )
            await conn.commit()
            updated = await self.get_fact_by_fingerprint(fact.fingerprint)
            return updated if updated else fact
        else:
            await conn.execute(
                """INSERT INTO facts
                   (id, agent_id, user_id, subject, predicate, object, content,
                    confidence, importance, access_count, created_at,
                    last_accessed, last_confirmed, ttl_days,
                    source_episode_id, promoted_from, fingerprint, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact.id,
                    fact.agent_id,
                    fact.user_id,
                    fact.subject,
                    fact.predicate.value,
                    fact.object,
                    fact.content,
                    fact.confidence,
                    fact.importance,
                    fact.access_count,
                    _dt_to_str(fact.created_at),
                    _dt_to_str(fact.last_accessed),
                    _dt_to_str(fact.last_confirmed),
                    fact.ttl_days,
                    fact.source_episode_id,
                    fact.promoted_from,
                    fact.fingerprint,
                    _dict_to_json(fact.metadata),
                ),
            )
            await conn.commit()
            return fact

    async def get_fact(self, fact_id: str) -> Fact | None:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM facts WHERE id = ?", (fact_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_fact(row)

    async def get_fact_by_fingerprint(self, fingerprint: str) -> Fact | None:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM facts WHERE fingerprint = ?", (fingerprint,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_fact(row)

    async def get_facts(self, query: SemanticQuery) -> list[Fact]:
        conn = self._ensure_conn()
        conditions: list[str] = []
        params: list[object] = []

        if query.agent_id:
            conditions.append("agent_id = ?")
            params.append(query.agent_id)
        if query.user_id:
            conditions.append("user_id = ?")
            params.append(query.user_id)
        if query.subjects:
            placeholders = ",".join("?" for _ in query.subjects)
            conditions.append(f"subject IN ({placeholders})")
            params.extend(query.subjects)
        if query.predicates:
            placeholders = ",".join("?" for _ in query.predicates)
            conditions.append(f"predicate IN ({placeholders})")
            params.extend(p.value for p in query.predicates)
        if query.min_confidence > 0:
            conditions.append("confidence >= ?")
            params.append(query.min_confidence)
        if not query.include_expired:
            conditions.append(
                "NOT (ttl_days IS NOT NULL AND "
                "CAST((julianday('now') - julianday(created_at)) AS INT)"
                " > ttl_days)"
            )

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = (
            f"SELECT * FROM facts WHERE {where} "  # noqa: S608
            "ORDER BY confidence DESC LIMIT ?"
        )
        params.append(query.top_k)

        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        facts = [self._row_to_fact(r) for r in rows]

        # Apply decay_score filter in Python (computed field)
        if query.min_decay_score > 0:
            facts = [f for f in facts if f.decay_score >= query.min_decay_score]

        return facts

    async def update_fact_access(self, fact_id: str) -> None:
        conn = self._ensure_conn()
        now = _dt_to_str(datetime.now(UTC))
        await conn.execute(
            "UPDATE facts SET last_accessed = ?, access_count = access_count + 1 "
            "WHERE id = ?",
            (now, fact_id),
        )
        await conn.commit()

    async def delete_fact(self, fact_id: str) -> bool:
        conn = self._ensure_conn()
        cursor = await conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
        await conn.commit()
        return cursor.rowcount > 0

    def _row_to_fact(self, row: aiosqlite.Row) -> Fact:
        return Fact(
            id=row["id"],
            agent_id=row["agent_id"],
            user_id=row["user_id"] or None,
            subject=row["subject"],
            predicate=FactRelation(row["predicate"]),
            object=row["object"],
            content=row["content"],
            confidence=row["confidence"],
            importance=row["importance"],
            access_count=row["access_count"],
            created_at=_str_to_dt(row["created_at"]),
            last_accessed=_str_to_dt(row["last_accessed"]),
            last_confirmed=_str_to_dt(row["last_confirmed"]),
            ttl_days=row["ttl_days"],
            source_episode_id=row["source_episode_id"] or None,
            promoted_from=row["promoted_from"] or None,
            fingerprint=row["fingerprint"],
            metadata=_json_to_dict(row["metadata"]),
        )

    # ---- Counts ----

    async def count_memories(self) -> dict[str, int]:
        conn = self._ensure_conn()
        result: dict[str, int] = {}
        for table, key in [
            ("working_entries", "working"),
            ("episodes", "episodic"),
            ("facts", "semantic"),
        ]:
            cursor = await conn.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608
            )
            row = await cursor.fetchone()
            result[key] = row[0] if row else 0
        return result
