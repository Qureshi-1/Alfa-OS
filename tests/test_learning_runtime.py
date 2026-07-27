"""Tests for Learning Runtime (Milestone 6)."""

import unittest
from prototype.learning import (
    LearningRuntime,
    RLLearningLoop,
    RewardEvaluator,
    ExperienceReplayBuffer,
    SelfImprovementMemory,
    ExperienceTuple,
)
from prototype.common import EventBus


class TestLearningRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.runtime = LearningRuntime(db_path=":memory:", event_bus=self.bus)
        self.runtime.load()

    def test_experience_replay_buffer(self) -> None:
        buf = ExperienceReplayBuffer(capacity=3)
        buf.push(ExperienceTuple(action="act1", reward=0.5))
        buf.push(ExperienceTuple(action="act2", reward=0.9))
        self.assertEqual(len(buf), 2)
        samples = buf.sample(1)
        self.assertEqual(len(samples), 1)

    def test_reward_evaluator(self) -> None:
        evaluator = RewardEvaluator()
        r_succ = evaluator.evaluate(True, latency_ms=100.0)
        r_fail = evaluator.evaluate(False, latency_ms=100.0)
        self.assertGreater(r_succ, r_fail)

    def test_learning_runtime_pipeline(self) -> None:
        exp1 = self.runtime.record_experience("tool_a", success=True)
        exp2 = self.runtime.record_experience("tool_b", success=False)
        best = self.runtime.get_preferred_action(["tool_a", "tool_b"])
        self.assertEqual(best, "tool_a")


if __name__ == "__main__":
    unittest.main()
