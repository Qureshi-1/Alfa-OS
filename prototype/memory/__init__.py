"""Memory subsystem for Alfa COS.

Working + persistent + manager + runtime interfaces.
"""

from .memory import Memory
from .persistent_memory import PersistentMemory
from .memory_manager import MemoryManager
from .memory_runtime import MemoryRuntimeInterface
from .memory_runtime_impl import DefaultMemoryRuntime
from .virtual_memory import (
    CognitiveVirtualMemory,
    ContextPageTable,
    KnowledgePageManager,
    CognitiveCacheManager,
    CognitiveRetrievalManager,
    PageState,
)

__all__ = [
    "Memory", "PersistentMemory", "MemoryManager",
    "MemoryEntry", "MemoryType", "QueryResult",
    "GraphNode", "GraphEdge",
    "WorkingMemoryInterface", "LongTermMemoryInterface",
    "GraphMemoryInterface", "VectorMemoryInterface",
    "MemoryRuntimeInterface", "DefaultMemoryRuntime",
]