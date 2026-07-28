"""Cognitive Virtual Memory — Milestone 1 implementation for ALFA COS v1.1.

Components:
- Context Paging: ContextPage, ContextPageTable (virtual memory paging for LLM context frames)
- Knowledge Paging: KnowledgePageManager (LRU-paged domain knowledge chunks)
- Cache Manager: CognitiveCacheManager (L1 in-memory + L2 SQLite + L3 cold cache)
- Retrieval Manager: CognitiveRetrievalManager (federated hybrid retrieval across pages and tiers)
- Memory Hierarchy: CognitiveVirtualMemory (unified virtual memory subsystem composition root)
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from prototype.common import Event, EventBus
from prototype.memory.memory_runtime import MemoryEntry, QueryResult

logger = logging.getLogger("alfa.memory.virtual")


class PageState(Enum):
    HOT = "hot"          # L1 Memory (fast access)
    WARM = "warm"        # L2 Disk / SQLite (persistent)
    COLD = "cold"        # L3 Compressed / Swapped Out
    EVICTED = "evicted"  # Removed from active working set


@dataclass
class ContextPage:
    """A virtual memory page containing a discrete chunk of conversation/context."""
    page_id: str = field(default_factory=lambda: str(uuid4()))
    frame_index: int = 0
    token_count: int = 0
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: PageState = PageState.HOT
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    pin_count: int = 0  # Pinned pages cannot be swapped out


class ContextPageTable:
    """Page table managing virtual context pages with LRU page-swapping."""

    def __init__(self, max_hot_pages: int = 5, page_size_tokens: int = 1024) -> None:
        self.max_hot_pages = max_hot_pages
        self.page_size_tokens = page_size_tokens
        self.pages: Dict[str, ContextPage] = {}
        self.swap_space: Dict[str, ContextPage] = {}

    def allocate_page(self, content: str, frame_index: int = 0, metadata: Optional[Dict[str, Any]] = None) -> ContextPage:
        # Approximate token count (4 chars ~ 1 token)
        token_cnt = max(1, len(content) // 4)
        page = ContextPage(
            frame_index=frame_index,
            token_count=token_cnt,
            content=content,
            metadata=metadata or {},
            state=PageState.HOT,
        )
        self.pages[page.page_id] = page

        # Enforce page swapping if hot capacity exceeded
        self._enforce_paging_limits()
        return page

    def access_page(self, page_id: str) -> Optional[ContextPage]:
        if page_id in self.pages:
            page = self.pages[page_id]
            page.access_count += 1
            page.last_accessed = time.time()
            return page

        # Swap in from swap space if present
        if page_id in self.swap_space:
            return self.swap_in(page_id)

        return None

    def swap_out(self, page_id: str) -> bool:
        if page_id in self.pages:
            page = self.pages[page_id]
            if page.pin_count > 0:
                return False  # Pinned page cannot be swapped out
            page.state = PageState.COLD
            self.swap_space[page_id] = page
            del self.pages[page_id]
            logger.debug("Swapped out context page %s to L3 swap space", page_id[:8])
            return True
        return False

    def swap_in(self, page_id: str) -> Optional[ContextPage]:
        if page_id in self.swap_space:
            page = self.swap_space[page_id]
            page.state = PageState.HOT
            page.last_accessed = time.time()
            page.access_count += 1
            self.pages[page_id] = page
            del self.swap_space[page_id]
            self._enforce_paging_limits()
            logger.debug("Swapped in context page %s from L3 swap space", page_id[:8])
            return page
        return None

    def _enforce_paging_limits(self) -> None:
        hot_pages = [p for p in self.pages.values() if p.state == PageState.HOT and p.pin_count == 0]
        if len(self.pages) > self.max_hot_pages and hot_pages:
            # LRU eviction: sort by last_accessed ascending
            hot_pages.sort(key=lambda p: p.last_accessed)
            victim = hot_pages[0]
            self.swap_out(victim.page_id)

    def get_active_context(self) -> str:
        hot_contents = [p.content for p in self.pages.values() if p.state == PageState.HOT]
        return "\n".join(hot_contents)


class KnowledgePageManager:
    """Virtual knowledge page manager for domain knowledge chunks."""

    def __init__(self, capacity: int = 50) -> None:
        self.capacity = capacity
        self._knowledge_pages: Dict[str, Dict[str, Any]] = {}
        self._access_history: Dict[str, float] = {}

    def store_knowledge(self, topic: str, content: str, tags: Optional[List[str]] = None) -> str:
        kid = f"kp_{uuid4().hex[:8]}"
        page = {
            "id": kid,
            "topic": topic,
            "content": content,
            "tags": tags or [],
            "timestamp": time.time(),
            "access_count": 0,
        }
        self._knowledge_pages[kid] = page
        self._access_history[kid] = time.time()
        self._evict_if_necessary()
        return kid

    def query_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        q_lower = query.lower()
        for kid, page in self._knowledge_pages.items():
            if q_lower in page["topic"].lower() or q_lower in page["content"].lower() or any(q_lower in t.lower() for t in page["tags"]):
                page["access_count"] += 1
                self._access_history[kid] = time.time()
                results.append(page)

        results.sort(key=lambda p: p["access_count"], reverse=True)
        return results[:limit]

    def _evict_if_necessary(self) -> None:
        if len(self._knowledge_pages) > self.capacity:
            lru_kid = min(self._access_history, key=self._access_history.get)
            del self._knowledge_pages[lru_kid]
            del self._access_history[lru_kid]


class CognitiveCacheManager:
    """Multi-tiered cache manager (L1 memory, L2 SQLite, L3 cold)."""

    def __init__(self, l1_size: int = 100, db_path: str = ":memory:") -> None:
        self._l1_cache: Dict[str, Any] = {}
        self._l1_size = l1_size
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS l2_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def put(self, key: str, value: Any) -> None:
        # L1 Cache
        if len(self._l1_cache) >= self._l1_size:
            # Evict first key
            first_key = next(iter(self._l1_cache))
            del self._l1_cache[first_key]
        self._l1_cache[key] = value

        # L2 Cache
        val_json = json.dumps(value)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO l2_cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, val_json, time.time()),
            )

    def get(self, key: str) -> Optional[Any]:
        # L1 Check
        if key in self._l1_cache:
            return self._l1_cache[key]

        # L2 Check
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM l2_cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            val = json.loads(row[0])
            self._l1_cache[key] = val
            return val
        return None

    def clear(self) -> None:
        self._l1_cache.clear()
        with self._conn:
            self._conn.execute("DELETE FROM l2_cache")


class CognitiveRetrievalManager:
    """Federated retrieval manager for hybrid memory search."""

    def __init__(self, page_table: ContextPageTable, knowledge_mgr: KnowledgePageManager, cache_mgr: CognitiveCacheManager) -> None:
        self.page_table = page_table
        self.knowledge_mgr = knowledge_mgr
        self.cache_mgr = cache_mgr

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        cache_hit = self.cache_mgr.get(f"query_{query}")
        if cache_hit:
            return {"source": "l1_l2_cache", "results": cache_hit}

        knowledge_res = self.knowledge_mgr.query_knowledge(query, limit=limit)
        
        active_pages = [
            {"page_id": p.page_id, "content": p.content, "token_count": p.token_count}
            for p in self.page_table.pages.values()
            if query.lower() in p.content.lower()
        ]

        combined = {
            "knowledge": knowledge_res,
            "context_pages": active_pages,
        }
        self.cache_mgr.put(f"query_{query}", combined)
        return {"source": "federated_search", "results": combined}


class MemoryCompressor:
    """Memory compression engine for context framing and page compaction."""

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """Compress text by retaining key segments."""
        if not text:
            return ""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return text
        keep_count = max(1, int(len(lines) * ratio))
        return "\n".join(lines[:keep_count])


class EvictionPolicy:
    """Eviction policy manager (LRU, TTL, Importance)."""

    def should_evict(self, last_accessed: float, ttl_seconds: float = 3600.0, importance: int = 0) -> bool:
        if importance >= 9:
            return False  # Critical items never evict
        age = time.time() - last_accessed
        return age > ttl_seconds


class CognitiveVirtualMemory:
    """Unified Virtual Memory System for ALFA COS v1.1."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()
        self.page_table = ContextPageTable()
        self.knowledge = KnowledgePageManager()
        self.cache = CognitiveCacheManager()
        self.retrieval = CognitiveRetrievalManager(self.page_table, self.knowledge, self.cache)
        self.compressor = MemoryCompressor()
        self.eviction_policy = EvictionPolicy()
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("CognitiveVirtualMemory subsystem initialized")

    def is_loaded(self) -> bool:
        return self._loaded

    def allocate_context_frame(self, content: str) -> str:
        page = self.page_table.allocate_page(content)
        self._event_bus.publish(Event(
            event_type="ContextPageAllocated",
            payload={"page_id": page.page_id, "token_count": page.token_count},
            source="virtual_memory",
        ))
        return page.page_id

    def compress_page(self, page_id: str, ratio: float = 0.5) -> Optional[str]:
        page = self.page_table.access_page(page_id)
        if page:
            page.content = self.compressor.compress(page.content, ratio=ratio)
            page.token_count = max(1, len(page.content) // 4)
            return page.content
        return None

    def store_knowledge(self, topic: str, content: str, tags: Optional[List[str]] = None) -> str:
        return self.knowledge.store_knowledge(topic, content, tags)

    def query(self, query_str: str) -> Dict[str, Any]:
        return self.retrieval.search(query_str)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "hot_pages": len(self.page_table.pages),
            "swapped_pages": len(self.page_table.swap_space),
            "l1_cache_entries": len(self.cache._l1_cache),
        }

