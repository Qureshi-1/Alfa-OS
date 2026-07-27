"""Knowledge Graph Runtime — Milestone 5 implementation for ALFA COS v1.1.

Components:
- Semantic Graph: GraphEntity, GraphRelation, KnowledgeGraph
- Persistent Graph Store: PersistentGraphStore (SQLite-backed graph storage)
- Graph Traversal: GraphTraversal (BFS/DFS multi-hop pathfinding)
- Relationship Reasoning: KnowledgeGraphRuntime (multi-hop semantic relationship reasoning)
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.memory.kg")


@dataclass
class GraphEntity:
    entity_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    entity_type: str = "concept"
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class GraphRelation:
    relation_id: str = field(default_factory=lambda: str(uuid4()))
    source_id: str = ""
    target_id: str = ""
    relation_type: str = "related_to"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class PersistentGraphStore:
    """SQLite-backed persistent graph store for entities and relations."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    relation_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    properties TEXT NOT NULL,
                    FOREIGN KEY(source_id) REFERENCES entities(entity_id),
                    FOREIGN KEY(target_id) REFERENCES entities(entity_id)
                )
            """)

    def add_entity(self, entity: GraphEntity) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO entities VALUES (?, ?, ?, ?, ?)",
                (entity.entity_id, entity.name, entity.entity_type, json.dumps(entity.properties), entity.created_at),
            )

    def add_relation(self, relation: GraphRelation) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO relations VALUES (?, ?, ?, ?, ?, ?)",
                (relation.relation_id, relation.source_id, relation.target_id, relation.relation_type, relation.weight, json.dumps(relation.properties)),
            )

    def get_entity_by_name(self, name: str) -> Optional[GraphEntity]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT entity_id, name, entity_type, properties, created_at FROM entities WHERE LOWER(name) = ?", (name.lower(),))
        row = cursor.fetchone()
        if row:
            return GraphEntity(entity_id=row[0], name=row[1], entity_type=row[2], properties=json.loads(row[3]), created_at=row[4])
        return None

    def get_outgoing_relations(self, source_id: str) -> List[GraphRelation]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT relation_id, source_id, target_id, relation_type, weight, properties FROM relations WHERE source_id = ?", (source_id,))
        rows = cursor.fetchall()
        return [GraphRelation(relation_id=r[0], source_id=r[1], target_id=r[2], relation_type=r[3], weight=r[4], properties=json.loads(r[5])) for r in rows]


class GraphTraversal:
    """Multi-hop graph traversal engine (BFS / pathfinding)."""

    def __init__(self, store: PersistentGraphStore) -> None:
        self.store = store

    def find_path(self, start_entity_id: str, target_entity_id: str, max_depth: int = 3) -> List[List[str]]:
        """Breadth-first search for multi-hop relation paths."""
        queue: List[Tuple[str, List[str]]] = [(start_entity_id, [start_entity_id])]
        visited: Set[str] = {start_entity_id}
        valid_paths: List[List[str]] = []

        while queue:
            curr_id, path = queue.pop(0)
            if curr_id == target_entity_id:
                valid_paths.append(path)
                continue

            if len(path) >= max_depth:
                continue

            relations = self.store.get_outgoing_relations(curr_id)
            for rel in relations:
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, path + [rel.target_id]))

        return valid_paths


class KnowledgeGraphRuntime:
    """Composition Root for Milestone 5 Knowledge Graph Runtime."""

    def __init__(self, db_path: str = ":memory:", event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()
        self.store = PersistentGraphStore(db_path=db_path)
        self.traversal = GraphTraversal(self.store)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("KnowledgeGraphRuntime loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def add_concept(self, name: str, entity_type: str = "concept", properties: Optional[Dict[str, Any]] = None) -> GraphEntity:
        entity = GraphEntity(name=name, entity_type=entity_type, properties=properties or {})
        self.store.add_entity(entity)
        return entity

    def connect_concepts(self, source_name: str, target_name: str, relation_type: str = "related_to", weight: float = 1.0) -> GraphRelation:
        src = self.store.get_entity_by_name(source_name) or self.add_concept(source_name)
        tgt = self.store.get_entity_by_name(target_name) or self.add_concept(target_name)

        rel = GraphRelation(source_id=src.entity_id, target_id=tgt.entity_id, relation_type=relation_type, weight=weight)
        self.store.add_relation(rel)

        self._event_bus.publish(Event(
            event_type="GraphRelationAdded",
            payload={"source": source_name, "target": target_name, "relation": relation_type},
            source="knowledge_graph",
        ))
        return rel

    def reason_relationship(self, source_name: str, target_name: str) -> Dict[str, Any]:
        src = self.store.get_entity_by_name(source_name)
        tgt = self.store.get_entity_by_name(target_name)

        if not src or not tgt:
            return {"connected": False, "paths": [], "message": "Entities not found"}

        paths = self.traversal.find_path(src.entity_id, tgt.entity_id)
        return {
            "source": source_name,
            "target": target_name,
            "connected": len(paths) > 0,
            "path_count": len(paths),
            "paths": paths,
        }
