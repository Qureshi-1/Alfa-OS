"""Tests for Cognitive Scheduler (Milestone 2)."""

import unittest
from prototype.execution import (
    CognitiveScheduler,
    TaskPriority,
    ScheduledTask,
    CognitiveResourceManager,
    AttentionAllocator,
    ExecutionQueue,
)
from prototype.common import EventBus


class TestCognitiveScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.scheduler = CognitiveScheduler(event_bus=self.bus)
        self.scheduler.load()

    def test_priority_queue_ordering(self) -> None:
        q = ExecutionQueue()
        t_low = ScheduledTask(priority=TaskPriority.LOW, created_at=1.0, name="low")
        t_crit = ScheduledTask(priority=TaskPriority.CRITICAL, created_at=2.0, name="crit")
        t_norm = ScheduledTask(priority=TaskPriority.NORMAL, created_at=1.5, name="norm")

        q.push(t_low)
        q.push(t_crit)
        q.push(t_norm)

        popped = q.pop()
        self.assertEqual(popped.name, "crit")

    def test_attention_allocation(self) -> None:
        allocator = AttentionAllocator(total_attention_capacity=100.0)
        allocator.allocate_attention("goal_1", TaskPriority.CRITICAL)
        allocator.allocate_attention("goal_2", TaskPriority.LOW)
        focused = allocator.get_focused_goal()
        self.assertEqual(focused, "goal_1")

    def test_resource_manager(self) -> None:
        rm = CognitiveResourceManager(max_concurrent_tokens=1000)
        self.assertTrue(rm.can_allocate(500))
        rm.allocate(500)
        self.assertFalse(rm.can_allocate(600))
        rm.release(500)
        self.assertTrue(rm.can_allocate(600))

    def test_cognitive_scheduler_pipeline(self) -> None:
        task1 = self.scheduler.submit_task("t1", "Process user goal", priority=TaskPriority.HIGH)
        self.assertEqual(task1.status, "queued")

        executed = self.scheduler.step_execution()
        self.assertIsNotNone(executed)
        self.assertEqual(executed.task_id, task1.task_id)
        self.assertEqual(executed.status, "completed")
        stats = self.scheduler.get_stats()
        self.assertEqual(stats["completed_tasks"], 1)


if __name__ == "__main__":
    unittest.main()
