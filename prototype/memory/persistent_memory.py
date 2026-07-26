"""Persistent Memory — SQLite-backed long-term storage.

All access must go through the Memory Manager. This module
provides the storage backend only.
"""

import json
import logging
import os
import sqlite3
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from prototype.common import Episode

logger = logging.getLogger("alfa.memory.persistent")

# Default database path relative to the project root
_DEFAULT_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "memory.db")


class PersistentMemory:
    """SQLite-backed persistent memory storage.

    Stores Episodes with full metadata, tags, and importance scoring.
    Future vector database backends will implement the same interface.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._loaded = False

    def load(self) -> None:
        """Initialize the database and create tables if needed."""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._loaded = True
        logger.info("Persistent Memory loaded: %s", self._db_path)

    def is_loaded(self) -> bool:
        return self._loaded

    def _create_tables(self) -> None:
        """Create the memory tables if they don't exist."""
        assert self._conn is not None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'episodic',
                tags TEXT DEFAULT '[]',
                importance INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC)
        """)
        self._conn.commit()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def store(self, episode: Episode, memory_type: str = "episodic",
             summary: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store an episode in persistent memory.

        Returns:
            The episode ID.
        """
        assert self._conn is not None
        now = time.time()
        self._conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, content, memory_type, tags, importance, summary, created_at, updated_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                episode.id,
                episode.content,
                memory_type,
                json.dumps(episode.tags),
                episode.importance,
                summary,
                episode.timestamp.timestamp() if episode.timestamp else now,
                now,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        logger.debug("Memory stored: id=%s type=%s", episode.id[:8], memory_type)
        return episode.id

    def retrieve(self, memory_id: str) -> Optional[Episode]:
        """Retrieve a single memory by ID or ID prefix."""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT * FROM memories WHERE id = ? OR id LIKE ?",
            (memory_id, f"{memory_id}%"),
        ).fetchone()
        if row:
            return self._row_to_episode(row)
        return None

    def search(self, query: str, limit: int = 10,
               memory_type: Optional[str] = None) -> List[Episode]:
        """Search memories by content keyword match."""
        assert self._conn is not None
        if memory_type:
            rows = self._conn.execute(
                """SELECT * FROM memories
                   WHERE memory_type = ? AND content LIKE ?
                   ORDER BY importance DESC, updated_at DESC
                   LIMIT ?""",
                (memory_type, f"%{query}%", limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT * FROM memories
                   WHERE content LIKE ?
                   ORDER BY importance DESC, updated_at DESC
                   LIMIT ?""",
                (f"%{query}%", limit),
            ).fetchall()
        return [self._row_to_episode(row) for row in rows]

    def list_all(self, limit: int = 50,
                 memory_type: Optional[str] = None) -> List[Episode]:
        """List all memories, optionally filtered by type."""
        assert self._conn is not None
        if memory_type:
            rows = self._conn.execute(
                """SELECT * FROM memories WHERE memory_type = ?
                   ORDER BY updated_at DESC LIMIT ?""",
                (memory_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_episode(row) for row in rows]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID or ID prefix."""
        assert self._conn is not None
        cursor = self._conn.execute(
            "DELETE FROM memories WHERE id = ? OR id LIKE ?",
            (memory_id, f"{memory_id}%"),
        )
        self._conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug("Memory deleted: %s", memory_id[:8])
        return deleted

    def clear(self, memory_type: Optional[str] = None) -> int:
        """Clear all memories (optionally of a specific type).

        Returns:
            Number of memories cleared.
        """
        assert self._conn is not None
        if memory_type:
            cursor = self._conn.execute(
                "DELETE FROM memories WHERE memory_type = ?", (memory_type,)
            )
        else:
            cursor = self._conn.execute("DELETE FROM memories")
        self._conn.commit()
        count = cursor.rowcount
        logger.info("Cleared %d memories (type=%s)", count, memory_type or "all")
        return count

    def count(self, memory_type: Optional[str] = None) -> int:
        """Count memories, optionally filtered by type."""
        assert self._conn is not None
        if memory_type:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM memories WHERE memory_type = ?",
                (memory_type,),
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        return row[0] if row else 0

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_episode(row: sqlite3.Row) -> Episode:
        """Convert a database row to an Episode."""
        from datetime import datetime
        tags = json.loads(row["tags"]) if row["tags"] else []
        return Episode(
            id=row["id"],
            content=row["content"],
            tags=tags,
            importance=row["importance"],
            timestamp=datetime.fromtimestamp(row["created_at"]),
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
        self._loaded = False
        logger.info("Persistent Memory shutdown")
