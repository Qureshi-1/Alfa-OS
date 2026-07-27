"""Tests for Advisor-Orchestrator-Worker Three-Tier Architecture."""

import unittest

from prototype.agent import (
    AdvisorOrchestratorCoordinator,
    AdvisorConsultation,
    SubtaskBrief,
    WorkerResult,
    ThreeTierTaskFrame,
    SubtaskStatus,
    MultiAgentCoordinator,
    AgentRegistry,
    ToolExecutor,
    BaseAgent,
    AgentContext,
    AgentResult,
)
from prototype.common import EventBus
from prototype.tools import ToolManager


class _DummyAgent(BaseAgent):
    def __init__(self, agent_id: str):
        self._id = agent_id

    @property
    def agent_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._id

    @property
    def description(self) -> str:
        return "Dummy agent for testing"

    def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self._id,
            task_id=context.task_id,
            output=f"Processed by {self._id}",
        )


class TestAdvisorOrchestratorCoordinator(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.coordinator = AdvisorOrchestratorCoordinator(event_bus=self.bus)

    def test_frame_task(self) -> None:
        frame = self.coordinator.frame_task("Build responsive desktop dashboard")
        self.assertIsInstance(frame, ThreeTierTaskFrame)
        self.assertEqual(frame.goal, "Build responsive desktop dashboard")
        self.assertGreater(len(frame.success_criteria), 0)

    def test_decompose_plan(self) -> None:
        frame = self.coordinator.frame_task("Perform code refactoring")
        briefs = self.coordinator.decompose_plan(frame)
        self.assertGreater(len(briefs), 0)
        self.assertIsInstance(briefs[0], SubtaskBrief)
        self.assertIn(briefs[0].subtask_id, self.coordinator._status_board)

    def test_advisor_review_plan(self) -> None:
        frame = self.coordinator.frame_task("Audit database schema")
        briefs = self.coordinator.decompose_plan(frame)
        consult = self.coordinator.advisor_review_plan(frame, briefs)
        self.assertIsInstance(consult, AdvisorConsultation)
        self.assertTrue(consult.approved)
        self.assertEqual(consult.consult_type, "plan_review")

    def test_dispatch_wave_and_verify(self) -> None:
        frame = self.coordinator.frame_task("Execute test tasks")
        briefs = self.coordinator.decompose_plan(frame)
        results = self.coordinator.dispatch_wave(frame, briefs, wave=1)
        self.assertGreater(len(results), 0)
        first_res = list(results.values())[0]
        self.assertIsInstance(first_res, WorkerResult)
        self.assertEqual(first_res.status, SubtaskStatus.PASS)

    def test_advisor_taste_pass(self) -> None:
        frame = self.coordinator.frame_task("Generate documentation")
        deliverable = {"success": True, "deliverable": "Documentation output"}
        consult = self.coordinator.advisor_taste_pass(frame, deliverable)
        self.assertTrue(consult.approved)
        self.assertEqual(consult.consult_type, "taste_pass")

    def test_run_three_tier_pipeline(self) -> None:
        result = self.coordinator.run_three_tier_pipeline("Synthesize project report")
        self.assertTrue(result["success"])
        self.assertIn("deliverable", result)
        self.assertGreater(result["worker_dispatches_used"], 0)
        self.assertGreater(result["advisor_consults_used"], 0)
        self.assertGreater(len(result["status_board"]), 0)
        self.assertEqual(len(result["consultations"]), 2)

    def test_multi_agent_pattern_integration(self) -> None:
        registry = AgentRegistry()
        tool_mgr = ToolManager()
        tool_executor = ToolExecutor(tool_mgr)
        multi_coordinator = MultiAgentCoordinator(registry, tool_executor, self.bus)

        dummy = _DummyAgent("agent_1")
        registry.register(dummy)

        ctx = AgentContext(task_id="t1", goal="Test three-tier pattern")
        results = multi_coordinator.run(["agent_1"], ctx, pattern="advisor_orchestrator")
        self.assertIn("agent_1", results)
        self.assertTrue(results["agent_1"].success)


if __name__ == "__main__":
    unittest.main()
