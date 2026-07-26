"""Memory Runtime — clean interfaces for all memory types.

Defines contracts for Working Memory, Long Term Memory, Graph Memory,
and Vector Memory. Implementations conform to these interfaces.

No advanced AI logic yet — architecture only.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4

from prototype.common import Episode


class MemoryType(Enum):
    WORKING = "working"
    LONG_TERM = "long_term"
    GRAPH = "graph"
    VECTOR = "vector"


@dataclass
class MemoryEntry:
    """Universal memory entry for all memory types."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.WORKING
    tags: List[str] = field(default_factory=list)
    importance: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: Optional[datetime] = None
    access_count: int = 0
    ttl_seconds: Optional[int] = None

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

    def touch(self) -> None:
        self.accessed_at = datetime.now()
        self.access_count += 1

    def to_episode(self) -> Episode:
        return Episode(
            id=self.id, content=self.content,
            tags=self.tags, importance=self.importance,
            timestamp=self.created_at,
        )

    @classmethod
    def from_episode(cls, ep: Episode, memory_type: MemoryType = MemoryType.WORKING) -> "MemoryEntry":
        return cls(
            id=ep.id, content=ep.content, memory_type=memory_type,
            tags=ep.tags, importance=ep.importance,
            created_at=ep.timestamp,
        )


@dataclass
class QueryResult:
    """Result from a memory query."""
    entries: List[MemoryEntry]
    scores: List[float]
    total: int = 0
    query_time_ms: float = 0.0

    def __iter__(self):
        return zip(self.entries, self.scores)

    def __len__(self):
        return len(self.entries)


@dataclass
class GraphEdge:
    """Edge in a graph memory."""
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphNode:
    """Node in a graph memory."""
    id: str
    content: str
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


class WorkingMemoryInterface(ABC):
    """Fast, short-term memory interface. Recent context."""

    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns entry ID."""

    @abstractmethod
    def recall(self, query: str, limit: int = 10) -> QueryResult:
        """Retrieve memories matching query."""

    @abstractmethod
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID."""

    @abstractmethod
    def update(self, entry: MemoryEntry) -> bool:
        """Update an existing memory."""

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete a memory by ID."""

    @abstractmethod
    def clear(self) -> int:
        """Clear all memories. Returns count cleared."""

    @abstractmethod
    def count(self) -> int:
        """Number of stored memories."""

    @abstractmethod
    def recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get most recently stored memories."""


class LongTermMemoryInterface(ABC):
    """Persistent, searchable long-term memory interface."""

    @abstractmethod
    def store(self, entry: MemoryEntry, category: str = "episodic") -> str:
        """Store with category. Returns entry ID."""

    @abstractmethod
    def search(self, query: str, limit: int = 10, category: Optional[str] = None) -> QueryResult:
        """Search by keyword across categories."""

    @abstractmethod
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID."""

    @abstractmethod
    def update(self, entry: MemoryEntry) -> bool:
        """Update an existing memory."""

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete a memory by ID."""

    @abstractmethod
    def list_categories(self) -> List[str]:
        """List all memory categories."""

    @abstractmethod
    def list_by_category(self, category: str, limit: int = 50) -> List[MemoryEntry]:
        """List memories in a category."""

    @abstractmethod
    def count(self, category: Optional[str] = None) -> int:
        """Count memories, optionally filtered by category."""

    @abstractmethod
    def clear(self, category: Optional[str] = None) -> int:
        """Clear memories, optionally filtered by category."""


class GraphMemoryInterface(ABC):
    """Knowledge graph memory interface. Stores entities and relationships."""

    @abstractmethod
    def add_node(self, node: GraphNode) -> str:
        """Add a node. Returns node ID."""

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""

    @abstractmethod
    def update_node(self, node: GraphNode) -> bool:
        """Update a node."""

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges."""

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        """Add a relationship between nodes."""

    @abstractmethod
    def delete_edge(self, source_id: str, target_id: str, relation: str) -> bool:
        """Delete a specific edge."""

    @abstractmethod
    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[GraphNode]:
        """Get neighboring nodes, optionally filtered by relation."""

    @abstractmethod
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        """Find paths between two nodes."""

    @abstractmethod
    def query(self, query_text: str, limit: int = 10) -> QueryResult:
        """Semantic search over graph nodes."""

    @abstractmethod
    def get_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges for a node."""

    @abstractmethod
    def node_count(self) -> int:
        """Number of nodes."""

    @abstractmethod
    def edge_count(self) -> int:
        """Number of edges."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all nodes and edges."""


class VectorMemoryInterface(ABC):
    """Vector similarity memory interface. Embedding-based retrieval."""

    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        """Store with embedding. Entry should have embedding set."""

    @abstractmethod
    def store_batch(self, entries: List[MemoryEntry]) -> List[str]:
        """Store multiple entries. Returns IDs."""

    @abstractmethod
    def search_similar(self, embedding: List[float], limit: int = 10,
                       threshold: float = 0.0) -> QueryResult:
        """Find similar memories by embedding vector."""

    @abstractmethod
    def search_text(self, query: str, limit: int = 10) -> QueryResult:
        """Search by text (auto-embed query)."""

    @abstractmethod
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID."""

    @abstractmethod
    def update(self, entry: MemoryEntry) -> bool:
        """Update an entry (including its embedding)."""

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Delete an entry."""

    @abstractmethod
    def count(self) -> int:
        """Number of stored vectors."""

    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""

    @abstractmethod
    def clear(self) -> int:
        """Clear all vectors."""


class MemoryRuntimeInterface(ABC):
    """Unified memory runtime coordinating all memory types."""

    @property
    @abstractmethod
    def working(self) -> WorkingMemoryInterface:
        """Access working memory."""

    @property
    @abstractmethod
    def long_term(self) -> LongTermMemoryInterface:
        """Access long-term memory."""

    @property
    @abstractmethod
    def graph(self) -> GraphMemoryInterface:
        """Access graph memory."""

    @property
    @abstractmethod
    def vector(self) -> VectorMemoryInterface:
        """Access vector memory."""

    @abstractmethod
    def store(self, content: str, memory_type: MemoryType = MemoryType.WORKING,
              tags: Optional[List[str]] = None, importance: int = 0,
              **kwargs) -> str:
        """Convenience store across any memory type."""

    @abstractmethod
    def recall(self, query: str, memory_types: Optional[List[MemoryType]] = None,
               limit: int = 10) -> QueryResult:
        """Cross-memory recall with optional type filtering."""

    @abstractmethod
    def load(self) -> None:
        """Initialize all memory subsystems."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown all memory subsystems."""

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Memory statistics across all types."""