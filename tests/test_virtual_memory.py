"""Tests for Cognitive Virtual Memory (Milestone 1)."""

import unittest
from prototype.memory import (
    CognitiveVirtualMemory,
    ContextPageTable,
    KnowledgePageManager,
    CognitiveCacheManager,
    CognitiveRetrievalManager,
    PageState,
)
from prototype.common import EventBus


class TestVirtualMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.vm = CognitiveVirtualMemory(event_bus=self.bus)
        self.vm.load()

    def test_context_paging_and_eviction(self) -> None:
        page_table = ContextPageTable(max_hot_pages=2)
        p1 = page_table.allocate_page("First page context content")
        p2 = page_table.allocate_page("Second page context content")
        self.assertEqual(len(page_table.pages), 2)

        # Allocate 3rd page -> triggers eviction of p1 to swap_space
        p3 = page_table.allocate_page("Third page context content")
        self.assertEqual(len(page_table.pages), 2)
        self.assertIn(p1.page_id, page_table.swap_space)

        # Swap in p1
        page_table.swap_in(p1.page_id)
        self.assertIn(p1.page_id, page_table.pages)

    def test_knowledge_paging(self) -> None:
        km = KnowledgePageManager(capacity=2)
        k1 = km.store_knowledge("python", "Python programming language")
        k2 = km.store_knowledge("alfa", "Alfa COS cognitive system")
        res = km.query_knowledge("Python")
        self.assertEqual(len(res), 1)

    def test_cache_manager(self) -> None:
        cache = CognitiveCacheManager(l1_size=5)
        cache.put("key1", {"data": "test"})
        val = cache.get("key1")
        self.assertEqual(val["data"], "test")

    def test_unified_virtual_memory(self) -> None:
        pid = self.vm.allocate_context_frame("System context frame")
        self.assertIsNotNone(pid)
        kid = self.vm.store_knowledge("architecture", "Three-tier architecture")
        self.assertIsNotNone(kid)
        res = self.vm.query("architecture")
        self.assertIn("results", res)
        stats = self.vm.get_stats()
        self.assertIn("hot_pages", stats)


if __name__ == "__main__":
    unittest.main()
