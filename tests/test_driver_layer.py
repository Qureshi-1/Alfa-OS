"""Tests for Driver Layer (Milestone 8)."""

import unittest
from prototype.services import (
    CognitiveDriverPluginRuntime,
    CognitiveDriverAPI,
    CognitiveDriverRegistry,
    MemoryDriver,
    InferenceDriver,
)
from prototype.common import EventBus


class TestDriverLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.runtime = CognitiveDriverPluginRuntime(event_bus=self.bus)
        self.runtime.load()

    def test_driver_registration_and_capabilities(self) -> None:
        drivers = self.runtime.registry.list_drivers()
        self.assertIn("memory_driver", drivers)
        self.assertIn("inference_driver", drivers)

    def test_execute_driver_capability(self) -> None:
        res = self.runtime.execute_driver_capability("memory_page", {"page_id": "p123"})
        self.assertTrue(res["success"])
        self.assertEqual(res["driver"], "memory_driver")

        res_inf = self.runtime.execute_driver_capability("llm_generate", {"prompt": "hello"})
        self.assertTrue(res_inf["success"])
        self.assertEqual(res_inf["driver"], "inference_driver")

    def test_unknown_capability_fails_gracefully(self) -> None:
        res = self.runtime.execute_driver_capability("unknown_cap")
        self.assertFalse(res["success"])
        self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
