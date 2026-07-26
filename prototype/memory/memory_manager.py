"""Memory Manager — single interface for all memory operations.

All memory access must go through this manager. No module may
access the working memory or persistent storage directly.
"""

import logging
from typing import Any, Dict, List, Optional

from prototype.common import Episode, Event, EventBus
from prototype.memory.memory import Memory as WorkingMemory
from prototype.memory.persistent_memory import PersistentMemory

logger = logging.getLogger("alfa.memory.manager")


class MemoryManager:
    """Unified interface for working and persistent memory.

    Provides:
    - remember() — store to working memory, optionally persist
    - recall() — search working + persistent memory
    - forget() — remove from working or persistent memory
    - list_memories() — list all memories
    - clear() — clear working and/or persistent memory
    - search() — keyword search across all memory
    - promote() — move from working to persistent memory
    """

    def __init__(
        self,
        working_memory: Optional[WorkingMemory] = None,
        persistent_memory: Optional[PersistentMemory] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._working = working_memory or WorkingMemory()
        self._persistent = persistent_memory or PersistentMemory()
        self._event_bus = event_bus
        self._loaded = False

    def load(self) -> None:
        """Initialize both memory systems."""
        self._working.load()
        self._persistent.load()
        self._loaded = True
        logger.info("Memory Manager loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Core operations ───────────────────────────────────────────────────

    def remember(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: int = 0,
        persist: bool = False,
        memory_type: str = "episodic",
    ) -> Episode:
        """Store a memory.

        Args:
            content: The text to remember.
            tags: Optional tags for categorization.
            importance: Importance score (0-10).
            persist: If True, also store in persistent (SQLite) memory.
            memory_type: Type of memory (episodic, semantic, etc.).

        Returns:
            The created Episode.
        """
        episode = self._working.remember(content, tags=tags, importance=importance)

        if persist:
            self._persistent.store(episode, memory_type=memory_type)

        logger.info(
            "Memory stored: id=%s persist=%s type=%s",
            episode.id[:8],
            persist,
            memory_type,
        )

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="MemoryStored",
                payload={
                    "memory_id": episode.id,
                    "content_length": len(content),
                    "persisted": persist,
                },
                source="memory_manager",
            ))

        return episode

    def recall(self, query: str = "", limit: int = 10) -> List[Episode]:
        """Search memories by keyword across working and persistent memory.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching Episodes.
        """
        # Search working memory first
        working_results = self._working.recall(query, limit=limit)

        # Also search persistent memory
        persistent_results = self._persistent.search(query, limit=limit)

        # Merge results, working memory first, deduplicate by ID
        seen_ids = {ep.id for ep in working_results}
        combined = list(working_results)
        for ep in persistent_results:
            if ep.id not in seen_ids:
                combined.append(ep)
                seen_ids.add(ep.id)

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="MemoryRetrieved",
                payload={"query": query, "results": len(combined)},
                source="memory_manager",
            ))

        return combined[:limit]

    def forget(self, memory_id: str) -> bool:
        """Remove a memory from working and/or persistent memory.

        Args:
            memory_id: Full or prefix ID of the memory to remove.

        Returns:
            True if a memory was removed.
        """
        working_removed = self._working.forget(memory_id)
        persistent_removed = self._persistent.delete(memory_id)
        return working_removed or persistent_removed

    def list_memories(self, limit: int = 50) -> List[Episode]:
        """List all working memories."""
        return self._working.get_working_memory()

    def get_working_memory(self) -> List[Episode]:
        """Get all working memory episodes."""
        return self._working.get_working_memory()

    def get_persistent_memories(self, limit: int = 50,
                                 memory_type: Optional[str] = None) -> List[Episode]:
        """List persistent memories."""
        return self._persistent.list_all(limit=limit, memory_type=memory_type)

    def clear(self, persistent: bool = False) -> None:
        """Clear working memory and optionally persistent memory.

        Args:
            persistent: If True, also clear persistent memory.
        """
        self._working.clear()
        if persistent:
            self._persistent.clear()
        logger.info("Memory cleared: persistent=%s", persistent)

    def search(self, query: str, limit: int = 10) -> List[Episode]:
        """Alias for recall()."""
        return self.recall(query, limit=limit)

    def promote(self, episode: Episode, memory_type: str = "semantic") -> None:
        """Move an episode from working to persistent memory.

        Args:
            episode: The episode to promote.
            memory_type: Type of persistent memory.
        """
        self._working.promote_to_long_term(episode)
        self._persistent.store(episode, memory_type=memory_type)
        logger.info("Memory promoted: id=%s type=%s", episode.id[:8], memory_type)

    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        return {
            "working_count": len(self._working.get_working_memory()),
            "persistent_count": self._persistent.count(),
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Shutdown both memory systems."""
        self._working.shutdown()
        self._persistent.shutdown()
        self._loaded = False
        logger.info("Memory Manager shutdown")
