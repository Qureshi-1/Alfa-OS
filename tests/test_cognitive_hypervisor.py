"""Tests for Cognitive Hypervisor (Milestone 7)."""

import unittest
from prototype.cognition import (
    CognitiveHypervisor,
    SnapshotManager,
    ReasoningSandbox,
    HypothesisEnvironment,
    SpeculativeExecutor,
)
from prototype.common import EventBus


class TestCognitiveHypervisor(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.hypervisor = CognitiveHypervisor(event_bus=self.bus)
        self.hypervisor.load()

    def test_snapshot_and_rollback(self) -> None:
        mgr = SnapshotManager()
        state = {"count": 1, "data": "initial"}
        snap = mgr.create_snapshot(state, label="checkpoint_1")
        
        # Mutate state
        state["count"] = 99
        restored = mgr.restore_snapshot(snap.snapshot_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["count"], 1)

    def test_sandbox_isolation(self) -> None:
        sandbox = ReasoningSandbox()
        
        def safe_fn(st):
            st["key"] = "value"
            return "OK"

        ok, out, err = sandbox.run_isolated(safe_fn, {})
        self.assertTrue(ok)
        self.assertEqual(out, "OK")

    def test_speculative_execution(self) -> None:
        trials = {
            "trial_a": lambda st: "output_a",
            "trial_b": lambda st: "output_b",
        }
        res = self.hypervisor.run_speculative_trials(trials, {"init": 1})
        self.assertIn("selected_trial", res)
        self.assertIsNotNone(res["selected_trial"])
        self.assertTrue(res["trial_results"]["trial_a"]["success"])


if __name__ == "__main__":
    unittest.main()
