"""Tests for Knowledge Graph Runtime (Milestone 5)."""

import unittest
from prototype.memory import (
    KnowledgeGraphRuntime,
    PersistentGraphStore,
    GraphTraversal,
    GraphEntity,
    GraphRelation,
)
from prototype.common import EventBus


class TestKnowledgeGraphRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.kg = KnowledgeGraphRuntime(db_path=":memory:", event_bus=self.bus)
        self.kg.load()

    def test_store_and_retrieve_entity(self) -> None:
        e = self.kg.add_concept("CognitionRuntime", entity_type="subsystem")
        self.assertEqual(e.name, "CognitionRuntime")
        fetched = self.kg.store.get_entity_by_name("CognitionRuntime")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.entity_id, e.entity_id)

    def test_multi_hop_relation_traversal(self) -> None:
        # A -> B -> C
        self.kg.connect_concepts("ModelHub", "CognitionRuntime", relation_type="serves")
        self.kg.connect_concepts("CognitionRuntime", "ExecutionRuntime", relation_type="dispatches_to")

        res = self.kg.reason_relationship("ModelHub", "ExecutionRuntime")
        self.assertTrue(res["connected"])
        self.assertGreater(res["path_count"], 0)


if __name__ == "__main__":
    unittest.main()
