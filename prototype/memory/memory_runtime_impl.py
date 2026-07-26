"""Default Memory Runtime implementation using existing backends.

Working Memory -> existing Memory class (in-memory list)
Long Term Memory -> existing PersistentMemory (SQLite)
Graph Memory -> SQLite-backed graph (simple adjacency list)
Vector Memory -> SQLite-backed vector store (brute-force similarity)
"""

import json
import logging
import math
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from prototype.common import Episode
from prototype.memory.memory import Memory
from prototype.memory.persistent_memory import PersistentMemory
from prototype.memory.memory_runtime import (
    GraphEdge, GraphNode, GraphMemoryInterface, LongTermMemoryInterface,
    MemoryEntry, MemoryRuntimeInterface, MemoryType, QueryResult,
    VectorMemoryInterface, WorkingMemoryInterface,
)

logger = logging.getLogger("alfa.memory.runtime")

_DEFAULT_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "memory.db")


class DefaultWorkingMemory(WorkingMemoryInterface):
    """In-memory working memory backed by existing Memory class."""

    def __init__(self) -> None:
        self._memory = Memory()
        self._entries: Dict[str, MemoryEntry] = {}

    def load(self) -> None:
        self._memory.load()

    def store(self, entry: MemoryEntry) -> str:
        self._memory.remember(entry.content, tags=entry.tags, importance=entry.importance)
        self._entries[entry.id] = entry
        return entry.id

    def recall(self, query: str, limit: int = 10) -> QueryResult:
        start = time.time()
        episodes = self._memory.recall(query, limit=limit)
        entries = [MemoryEntry.from_episode(ep) for ep in episodes]
        scores = [1.0] * len(entries)
        return QueryResult(entries=entries, scores=scores, total=len(entries),
                          query_time_ms=(time.time() - start) * 1000)

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        return self._entries.get(entry_id)

    def update(self, entry: MemoryEntry) -> bool:
        if entry.id in self._entries:
            self._entries[entry.id] = entry
            return True
        return False

    def delete(self, entry_id: str) -> bool:
        removed = self._memory.forget(entry_id)
        self._entries.pop(entry_id, None)
        return removed

    def clear(self) -> int:
        count = len(self._entries)
        self._memory.clear()
        self._entries.clear()
        return count

    def count(self) -> int:
        return len(self._memory.get_working_memory())

    def recent(self, limit: int = 10) -> List[MemoryEntry]:
        eps = self._memory.get_working_memory()[-limit:]
        return [MemoryEntry.from_episode(ep) for ep in eps]


class DefaultLongTermMemory(LongTermMemoryInterface):
    """Persistent memory backed by SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._persistent = PersistentMemory(db_path)

    def load(self) -> None:
        self._persistent.load()

    def store(self, entry: MemoryEntry, category: str = "episodic") -> str:
        ep = entry.to_episode()
        self._persistent.store(ep, memory_type=category)
        return entry.id

    def search(self, query: str, limit: int = 10, category: Optional[str] = None) -> QueryResult:
        start = time.time()
        episodes = self._persistent.search(query, limit=limit, memory_type=category)
        entries = [MemoryEntry.from_episode(ep) for ep in episodes]
        return QueryResult(entries=entries, scores=[1.0] * len(entries), total=len(entries),
                          query_time_ms=(time.time() - start) * 1000)

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        ep = self._persistent.retrieve(entry_id)
        return MemoryEntry.from_episode(ep) if ep else None

    def update(self, entry: MemoryEntry) -> bool:
        ep = entry.to_episode()
        self._persistent.store(ep)
        return True

    def delete(self, entry_id: str) -> bool:
        return self._persistent.delete(entry_id)

    def list_categories(self) -> List[str]:
        return ["episodic", "semantic", "procedural"]

    def list_by_category(self, category: str, limit: int = 50) -> List[MemoryEntry]:
        episodes = self._persistent.list_all(limit=limit, memory_type=category)
        return [MemoryEntry.from_episode(ep) for ep in episodes]

    def count(self, category: Optional[str] = None) -> int:
        return self._persistent.count(category)

    def clear(self, category: Optional[str] = None) -> int:
        return self._persistent.clear(category)


class DefaultGraphMemory(GraphMemoryInterface):
    """SQLite-backed graph memory with adjacency list storage."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._loaded = False

    def load(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._loaded = True

    def _create_tables(self) -> None:
        assert self._conn
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                labels TEXT DEFAULT '[]',
                properties TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}',
                PRIMARY KEY (source_id, target_id, relation)
            )
        """)
        self._conn.commit()

    def add_node(self, node: GraphNode) -> str:
        assert self._conn
        self._conn.execute(
            "INSERT OR REPLACE INTO graph_nodes (id, content, labels, properties) VALUES (?, ?, ?, ?)",
            (node.id, node.content, json.dumps(node.labels), json.dumps(node.properties)),
        )
        self._conn.commit()
        return node.id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        assert self._conn
        row = self._conn.execute("SELECT * FROM graph_nodes WHERE id = ?", (node_id,)).fetchone()
        if not row:
            return None
        return GraphNode(
            id=row["id"], content=row["content"],
            labels=json.loads(row["labels"]),
            properties=json.loads(row["properties"]),
        )

    def update_node(self, node: GraphNode) -> bool:
        return self.add_node(node) is not None

    def delete_node(self, node_id: str) -> bool:
        assert self._conn
        self._conn.execute("DELETE FROM graph_edges WHERE source_id = ? OR target_id = ?", (node_id, node_id))
        cursor = self._conn.execute("DELETE FROM graph_nodes WHERE id = ?", (node_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def add_edge(self, edge: GraphEdge) -> None:
        assert self._conn
        self._conn.execute(
            "INSERT OR REPLACE INTO graph_edges (source_id, target_id, relation, weight, metadata) VALUES (?, ?, ?, ?, ?)",
            (edge.source_id, edge.target_id, edge.relation, edge.weight, json.dumps(edge.metadata)),
        )
        self._conn.commit()

    def delete_edge(self, source_id: str, target_id: str, relation: str) -> bool:
        assert self._conn
        cursor = self._conn.execute(
            "DELETE FROM graph_edges WHERE source_id = ? AND target_id = ? AND relation = ?",
            (source_id, target_id, relation),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[GraphNode]:
        assert self._conn
        if relation:
            rows = self._conn.execute(
                """SELECT n.* FROM graph_nodes n
                   JOIN graph_edges e ON n.id = e.target_id
                   WHERE e.source_id = ? AND e.relation = ?""",
                (node_id, relation),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT n.* FROM graph_nodes n
                   JOIN graph_edges e ON n.id = e.target_id
                   WHERE e.source_id = ?""",
                (node_id,),
            ).fetchall()
        return [GraphNode(id=r["id"], content=r["content"], labels=json.loads(r["labels"]),
                          properties=json.loads(r["properties"])) for r in rows]

    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        assert self._conn
        paths = []
        queue = [(source_id, [source_id])]
        visited = {source_id}

        for _ in range(max_depth):
            next_queue = []
            for current, path in queue:
                rows = self._conn.execute(
                    "SELECT target_id FROM graph_edges WHERE source_id = ?", (current,)
                ).fetchall()
                for row in rows:
                    neighbor = row["target_id"]
                    if neighbor == target_id:
                        paths.append(path + [neighbor])
                    elif neighbor not in visited:
                        visited.add(neighbor)
                        next_queue.append((neighbor, path + [neighbor]))
            queue = next_queue
            if paths:
                break

        return paths

    def query(self, query_text: str, limit: int = 10) -> QueryResult:
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM graph_nodes WHERE content LIKE ? LIMIT ?",
            (f"%{query_text}%", limit),
        ).fetchall()
        entries = [MemoryEntry(id=r["id"], content=r["content"],
                               metadata=json.loads(r["properties"])) for r in rows]
        return QueryResult(entries=entries, scores=[1.0] * len(entries))

    def get_edges(self, node_id: str) -> List[GraphEdge]:
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM graph_edges WHERE source_id = ? OR target_id = ?", (node_id, node_id)
        ).fetchall()
        return [GraphEdge(source_id=r["source_id"], target_id=r["target_id"],
                          relation=r["relation"], weight=r["weight"],
                          metadata=json.loads(r["metadata"])) for r in rows]

    def node_count(self) -> int:
        assert self._conn
        row = self._conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()
        return row[0] if row else 0

    def edge_count(self) -> int:
        assert self._conn
        row = self._conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        assert self._conn
        self._conn.execute("DELETE FROM graph_edges")
        self._conn.execute("DELETE FROM graph_nodes")
        self._conn.commit()


class DefaultVectorMemory(VectorMemoryInterface):
    """SQLite-backed vector memory with brute-force cosine similarity."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._loaded = False

    def load(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._loaded = True

    def _create_tables(self) -> None:
        assert self._conn
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS vector_memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                importance INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    def store(self, entry: MemoryEntry) -> str:
        assert self._conn
        if not entry.embedding:
            raise ValueError("Entry must have embedding set for vector memory")
        self._conn.execute(
            """INSERT OR REPLACE INTO vector_memories
               (id, content, embedding, tags, importance, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry.id, entry.content, json.dumps(entry.embedding),
             json.dumps(entry.tags), entry.importance, json.dumps(entry.metadata),
             entry.created_at.timestamp()),
        )
        self._conn.commit()
        return entry.id

    def store_batch(self, entries: List[MemoryEntry]) -> List[str]:
        assert self._conn
        ids = []
        for entry in entries:
            ids.append(self.store(entry))
        return ids

    def search_similar(self, embedding: List[float], limit: int = 10,
                       threshold: float = 0.0) -> QueryResult:
        assert self._conn
        start = time.time()
        rows = self._conn.execute("SELECT * FROM vector_memories").fetchall()
        scored = []
        for row in rows:
            stored_emb = json.loads(row["embedding"])
            score = self._cosine_similarity(embedding, stored_emb)
            if score >= threshold:
                entry = MemoryEntry(
                    id=row["id"], content=row["content"],
                    embedding=stored_emb, tags=json.loads(row["tags"]),
                    importance=row["importance"],
                    metadata=json.loads(row["metadata"]),
                )
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [e for _, e in scored[:limit]]
        scores = [s for s, _ in scored[:limit]]
        return QueryResult(entries=results, scores=scores, total=len(results),
                          query_time_ms=(time.time() - start) * 1000)

    def search_text(self, query: str, limit: int = 10) -> QueryResult:
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM vector_memories WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        entries = [MemoryEntry(
            id=row["id"], content=row["content"],
            embedding=json.loads(row["embedding"]),
            tags=json.loads(row["tags"]),
            importance=row["importance"],
            metadata=json.loads(row["metadata"]),
        ) for row in rows]
        return QueryResult(entries=entries, scores=[1.0] * len(entries))

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        assert self._conn
        row = self._conn.execute("SELECT * FROM vector_memories WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            return None
        return MemoryEntry(
            id=row["id"], content=row["content"],
            embedding=json.loads(row["embedding"]),
            tags=json.loads(row["tags"]),
            importance=row["importance"],
            metadata=json.loads(row["metadata"]),
        )

    def update(self, entry: MemoryEntry) -> bool:
        if not entry.embedding:
            return False
        return self.store(entry) is not None

    def delete(self, entry_id: str) -> bool:
        assert self._conn
        cursor = self._conn.execute("DELETE FROM vector_memories WHERE id = ?", (entry_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        assert self._conn
        row = self._conn.execute("SELECT COUNT(*) FROM vector_memories").fetchone()
        return row[0] if row else 0

    def dimension(self) -> int:
        assert self._conn
        row = self._conn.execute("SELECT embedding FROM vector_memories LIMIT 1").fetchone()
        if row:
            return len(json.loads(row["embedding"]))
        return 0

    def clear(self) -> int:
        assert self._conn
        cursor = self._conn.execute("DELETE FROM vector_memories")
        self._conn.commit()
        return cursor.rowcount

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class DefaultMemoryRuntime(MemoryRuntimeInterface):
    """Default implementation coordinating all memory types."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._working = DefaultWorkingMemory()
        self._long_term = DefaultLongTermMemory(db_path)
        self._graph = DefaultGraphMemory(db_path)
        self._vector = DefaultVectorMemory(db_path)
        self._loaded = False

    @property
    def working(self) -> WorkingMemoryInterface:
        return self._working

    @property
    def long_term(self) -> LongTermMemoryInterface:
        return self._long_term

    @property
    def graph(self) -> GraphMemoryInterface:
        return self._graph

    @property
    def vector(self) -> VectorMemoryInterface:
        return self._vector

    def store(self, content: str, memory_type: MemoryType = MemoryType.WORKING,
              tags: Optional[List[str]] = None, importance: int = 0, **kwargs) -> str:
        entry = MemoryEntry(content=content, memory_type=memory_type, tags=tags or [], importance=importance)

        if memory_type == MemoryType.WORKING:
            return self._working.store(entry)
        elif memory_type == MemoryType.LONG_TERM:
            category = kwargs.get("category", "episodic")
            return self._long_term.store(entry, category=category)
        elif memory_type == MemoryType.GRAPH:
            node = GraphNode(id=entry.id, content=entry.content, labels=tags or [])
            return self._graph.add_node(node)
        elif memory_type == MemoryType.VECTOR:
            entry.embedding = kwargs.get("embedding")
            return self._vector.store(entry)
        return entry.id

    def recall(self, query: str, memory_types: Optional[List[MemoryType]] = None,
               limit: int = 10) -> QueryResult:
        types = memory_types or list(MemoryType)
        all_entries = []
        all_scores = []

        for mt in types:
            if mt == MemoryType.WORKING:
                result = self._working.recall(query, limit=limit)
            elif mt == MemoryType.LONG_TERM:
                result = self._long_term.search(query, limit=limit)
            elif mt == MemoryType.GRAPH:
                result = self._graph.query(query, limit=limit)
            elif mt == MemoryType.VECTOR:
                result = self._vector.search_text(query, limit=limit)
            else:
                continue
            all_entries.extend(result.entries)
            all_scores.extend(result.scores)

        # Sort by score descending, take top limit
        paired = sorted(zip(all_scores, all_entries), key=lambda x: x[0], reverse=True)
        entries = [e for _, e in paired[:limit]]
        scores = [s for s, _ in paired[:limit]]

        return QueryResult(entries=entries, scores=scores, total=len(entries))

    def load(self) -> None:
        self._working.load()
        self._long_term.load()
        self._graph.load()
        self._vector.load()
        self._loaded = True
        logger.info("MemoryRuntime loaded")

    def shutdown(self) -> None:
        self._loaded = False

    def stats(self) -> Dict[str, Any]:
        return {
            "working_count": self._working.count(),
            "long_term_count": self._long_term.count(),
            "graph_nodes": self._graph.node_count(),
            "graph_edges": self._graph.edge_count(),
            "vector_count": self._vector.count(),
        }