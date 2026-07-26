"""Unit tests for the Alfa COS Worker Framework."""

import unittest
from prototype.common import EventBus
from prototype.worker import (
    BaseWorker,
    EchoWorker,
    WorkerContext,
    WorkerLifecycle,
    WorkerManager,
    WorkerRegistry,
    WorkerResult,
    WorkerScheduler,
    WorkerStatus,
)


class TestWorkerFramework(unittest.TestCase):

    def setUp(self) -> None:
        self.bus = EventBus()
        self.manager = WorkerManager(event_bus=self.bus)
        self.manager.load()

    def test_echo_worker_execution(self) -> None:
        result = self.manager.execute_worker("echo_worker", {"message": "hello worker"})
        self.assertTrue(result.success)
        self.assertEqual(result.status, WorkerStatus.COMPLETED)
        self.assertEqual(result.output["echo"], "hello worker")

    def test_worker_not_found(self) -> None:
        result = self.manager.execute_worker("unknown_worker")
        self.assertFalse(result.success)
        self.assertEqual(result.status, WorkerStatus.FAILED)
        self.assertIn("not found", result.error)

    def test_worker_registry(self) -> None:
        registry = WorkerRegistry()
        echo = EchoWorker()
        registry.register(echo)
        self.assertIn("echo_worker", registry.get_worker_names())
        self.assertEqual(registry.get_worker("echo_worker"), echo)

    def test_worker_scheduler_fifo(self) -> None:
        scheduler = WorkerScheduler()
        ctx1 = WorkerContext(parameters={"num": 1})
        ctx2 = WorkerContext(parameters={"num": 2})

        scheduler.enqueue("w1", ctx1)
        scheduler.enqueue("w2", ctx2)

        self.assertEqual(scheduler.size(), 2)

        item1 = scheduler.dequeue()
        self.assertIsNotNone(item1)
        self.assertEqual(item1[0], "w1")

        item2 = scheduler.dequeue()
        self.assertIsNotNone(item2)
        self.assertEqual(item2[0], "w2")

        self.assertEqual(scheduler.size(), 0)

    def test_worker_lifecycle(self) -> None:
        lifecycle = WorkerLifecycle()
        task_id = "test-123"
        lifecycle.transition(task_id, WorkerStatus.QUEUED)
        self.assertEqual(lifecycle.get_status(task_id), WorkerStatus.QUEUED)

        res = WorkerResult(task_id=task_id, worker_name="test", status=WorkerStatus.COMPLETED)
        lifecycle.record_result(res)
        self.assertEqual(lifecycle.get_status(task_id), WorkerStatus.COMPLETED)
        self.assertEqual(len(lifecycle.get_history()), 1)

    def test_worker_events_published(self) -> None:
        events = []
        self.bus.subscribe("WorkerStarted", lambda e: events.append(e))
        self.bus.subscribe("WorkerCompleted", lambda e: events.append(e))

        self.manager.execute_worker("echo_worker", {"test": True})
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "WorkerStarted")
        self.assertEqual(events[1].event_type, "WorkerCompleted")

    def tearDown(self) -> None:
        self.manager.shutdown()


if __name__ == "__main__":
    unittest.main()
