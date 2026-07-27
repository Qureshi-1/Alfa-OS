"""Tests for Planning Engine (Milestone 3)."""

import unittest
from prototype.planner import (
    PlanningEngine,
    PlanningNode,
    GoalDecomposer,
    AStarPlanner,
    MCTSPlanner,
)
from prototype.common import EventBus


class TestPlanningEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.engine = PlanningEngine(event_bus=self.bus)
        self.engine.load()

    def test_goal_decomposition(self) -> None:
        decomposer = GoalDecomposer()
        subgoals = decomposer.decompose("Deep research on quantum computing")
        self.assertGreater(len(subgoals), 0)
        self.assertEqual(subgoals[0]["action"], "web_search")

    def test_astar_planner(self) -> None:
        astar = AStarPlanner()
        nodes = astar.search({"start": True}, "Research topic", ["search", "summarize", "output"])
        self.assertGreater(len(nodes), 0)
        self.assertEqual(nodes[0].action, "search")

    def test_mcts_planner(self) -> None:
        mcts = MCTSPlanner()
        nodes = mcts.search("Optimize database query execution", iterations=10)
        self.assertGreater(len(nodes), 0)
        best_node = nodes[0]
        self.assertGreater(best_node.visit_count, 0)

    def test_planning_engine_integration(self) -> None:
        plan_res = self.engine.create_advanced_plan("Build software architecture diagram", method="mcts")
        self.assertTrue(plan_res["plan_id"].startswith("plan_"))
        self.assertIn("explored_nodes", plan_res)
        self.assertGreater(len(plan_res["explored_nodes"]), 0)


if __name__ == "__main__":
    unittest.main()
