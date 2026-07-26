"""Worker Manager — coordinator for worker execution, lifecycle, scheduling, and crash recovery."""

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from prototype.common import Event, EventBus
from prototype.worker.base_worker import (
    BaseWorker,
    WorkerContext,
    WorkerResult,
    WorkerStatus,
)
from prototype.worker.worker_lifecycle import WorkerLifecycle
from prototype.worker.worker_registry import WorkerRegistry
from prototype.worker.worker_scheduler import WorkerScheduler
from prototype.worker.echo_worker import EchoWorker

logger = logging.getLogger("alfa.worker.manager")


class WorkerManager:
    """Orchestrates worker execution, lifecycle, scheduling, and crash recovery.

    Lifecycle operations: start, pause, resume, stop
    Scheduling: cron-like periodic execution
    Recovery: automatic retry after crash
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self.registry = WorkerRegistry()
        self.scheduler = WorkerScheduler()
        self.lifecycle = WorkerLifecycle()
        self._event_bus = event_bus
        self._loaded = False

        # Running task tracking
        self._running: Dict[str, WorkerContext] = {}
        self._paused: Dict[str, str] = {}  # task_id -> worker_name
        self._stopped: set = set()

        # Scheduled tasks
        self._schedules: Dict[str, Dict[str, Any]] = {}
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_running = False
        self._scheduler_lock = threading.Lock()

        # Isolation
        self._max_concurrent: int = 4
        self._semaphore = threading.Semaphore(self._max_concurrent)

    def load(self) -> None:
        if self._loaded:
            return
        self.registry.register(EchoWorker())
        self._loaded = True
        self._start_scheduler_thread()
        logger.info("WorkerManager loaded: %d workers", len(self.registry.get_worker_names()))

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Execution ──────────────────────────────────────────────────────────

    def execute_worker(
        self, worker_name: str, parameters: Optional[Dict[str, Any]] = None
    ) -> WorkerResult:
        worker = self.registry.get_worker(worker_name)
        context = WorkerContext(parameters=parameters or {})

        if not worker:
            result = WorkerResult(
                task_id=context.task_id, worker_name=worker_name,
                status=WorkerStatus.FAILED, error=f"Worker '{worker_name}' not found",
            )
            self.lifecycle.record_result(result)
            return result

        self.lifecycle.transition(context.task_id, WorkerStatus.RUNNING)
        self._running[context.task_id] = context

        self._publish_event("WorkerStarted", {"task_id": context.task_id, "worker": worker_name})

        start_time = time.time()
        try:
            self._semaphore.acquire()
            try:
                result = worker.execute(context)
            finally:
                self._semaphore.release()

            result.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            self.lifecycle.record_result(result)
            self._running.pop(context.task_id, None)
            self.lifecycle.reset_crash_count(worker_name)

            logger.info("Worker '%s' completed task_id=%s", worker_name, context.task_id[:8])
            self._publish_event(
                "WorkerCompleted" if result.success else "WorkerFailed",
                {"task_id": context.task_id, "worker": worker_name,
                 "status": result.status.value, "execution_time_ms": result.execution_time_ms},
            )
            return result

        except Exception as exc:
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            self._running.pop(context.task_id, None)

            # Try crash recovery
            if self.lifecycle.can_recover(worker_name):
                crash_count = self.lifecycle.record_crash(context.task_id, worker_name)
                worker.on_crash(exc)
                recovered = worker.recover(context)
                if recovered:
                    recovered.execution_time_ms = execution_time_ms
                    self.lifecycle.record_result(recovered)
                    self.lifecycle.transition(context.task_id, WorkerStatus.RECOVERING)
                    self._publish_event("WorkerRecovered", {
                        "task_id": context.task_id, "worker": worker_name, "attempt": crash_count,
                    })
                    return recovered

            result = WorkerResult(
                task_id=context.task_id, worker_name=worker_name,
                status=WorkerStatus.FAILED, error=str(exc), execution_time_ms=execution_time_ms,
            )
            self.lifecycle.record_result(result)
            logger.error("Worker '%s' failed task_id=%s: %s", worker_name, context.task_id[:8], exc)
            self._publish_event("WorkerFailed", {"task_id": context.task_id, "worker": worker_name, "error": str(exc)})
            return result

    # ── Lifecycle Operations ───────────────────────────────────────────────

    def pause_worker(self, task_id: str) -> bool:
        """Pause a running worker by task_id."""
        context = self._running.get(task_id)
        if not context:
            return False

        worker = self.registry.get_worker(context.worker_name)
        if worker:
            worker.on_pause()

        self.lifecycle.transition(task_id, WorkerStatus.PAUSED)
        self._paused[task_id] = context.worker_name
        self._running.pop(task_id, None)

        self._publish_event("WorkerPaused", {"task_id": task_id, "worker": context.worker_name})
        logger.info("Worker paused: task_id=%s", task_id[:8])
        return True

    def resume_worker(self, task_id: str) -> bool:
        """Resume a paused worker."""
        worker_name = self._paused.pop(task_id, None)
        if not worker_name:
            return False

        worker = self.registry.get_worker(worker_name)
        if worker:
            worker.on_resume()

        self.lifecycle.transition(task_id, WorkerStatus.RUNNING)
        self._running[task_id] = WorkerContext(task_id=task_id, metadata={"resumed": True})

        self._publish_event("WorkerResumed", {"task_id": task_id, "worker": worker_name})
        logger.info("Worker resumed: task_id=%s", task_id[:8])
        return True

    def stop_worker(self, task_id: str) -> bool:
        """Stop a running or paused worker."""
        context = self._running.pop(task_id, None)
        worker_name = self._paused.pop(task_id, None)

        if context:
            worker_name = context.worker_name
        if not worker_name:
            return False

        worker = self.registry.get_worker(worker_name)
        if worker:
            worker.on_stop()

        self.lifecycle.transition(task_id, WorkerStatus.CANCELLED)
        self._stopped.add(task_id)

        self._publish_event("WorkerStopped", {"task_id": task_id, "worker": worker_name})
        logger.info("Worker stopped: task_id=%s", task_id[:8])
        return True

    def get_running_tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": tid, "worker": ctx.worker_name, **ctx.metadata}
                for tid, ctx in self._running.items()]

    def get_paused_tasks(self) -> List[Dict[str, Any]]:
        return [{"task_id": tid, "worker": name} for tid, name in self._paused.items()]

    # ── Scheduling ─────────────────────────────────────────────────────────

    def schedule_worker(
        self, worker_name: str, interval_seconds: float,
        parameters: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Schedule a worker to run periodically."""
        schedule_id = name or f"schedule_{worker_name}_{int(time.time())}"
        with self._scheduler_lock:
            self._schedules[schedule_id] = {
                "worker_name": worker_name,
                "interval": interval_seconds,
                "parameters": parameters or {},
                "last_run": 0.0,
                "enabled": True,
                "run_count": 0,
            }
        self._publish_event("WorkerScheduled", {
            "schedule_id": schedule_id, "worker": worker_name, "interval": interval_seconds,
        })
        logger.info("Worker scheduled: %s every %.1fs", schedule_id, interval_seconds)
        return schedule_id

    def unschedule_worker(self, schedule_id: str) -> bool:
        with self._scheduler_lock:
            removed = self._schedules.pop(schedule_id, None)
        if removed:
            self._publish_event("WorkerUnscheduled", {"schedule_id": schedule_id})
            return True
        return False

    def pause_schedule(self, schedule_id: str) -> bool:
        with self._scheduler_lock:
            schedule = self._schedules.get(schedule_id)
            if schedule:
                schedule["enabled"] = False
                return True
        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        with self._scheduler_lock:
            schedule = self._schedules.get(schedule_id)
            if schedule:
                schedule["enabled"] = True
                return True
        return False

    def list_schedules(self) -> List[Dict[str, Any]]:
        with self._scheduler_lock:
            return [
                {"schedule_id": sid, **sched}
                for sid, sched in self._schedules.items()
            ]

    def _start_scheduler_thread(self) -> None:
        if self._scheduler_running:
            return
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def _scheduler_loop(self) -> None:
        while self._scheduler_running:
            time.sleep(1.0)
            now = time.time()
            with self._scheduler_lock:
                schedules = dict(self._schedules)

            for sid, sched in schedules.items():
                if not sched["enabled"]:
                    continue
                if now - sched["last_run"] >= sched["interval"]:
                    sched["last_run"] = now
                    sched["run_count"] += 1
                    worker_name = sched["worker_name"]
                    if self.registry.get_worker(worker_name):
                        threading.Thread(
                            target=self.execute_worker,
                            args=(worker_name, sched["parameters"]),
                            daemon=True,
                        ).start()

    # ── Events ─────────────────────────────────────────────────────────────

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(event_type=event_type, payload=payload, source="worker_manager"))

    # ── Stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        lifecycle_stats = self.lifecycle.get_stats()
        return {
            "registered_workers": self.registry.get_worker_names(),
            "worker_count": len(self.registry.get_worker_names()),
            "queue_size": self.scheduler.size(),
            "running": len(self._running),
            "paused": len(self._paused),
            "schedules": len(self._schedules),
            **lifecycle_stats,
        }

    def shutdown(self) -> None:
        self._scheduler_running = False
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=2)
        self.scheduler.clear()
        self.lifecycle.clear()
        self.registry.clear()
        self._running.clear()
        self._paused.clear()
        self._stopped.clear()
        self._schedules.clear()
        self._loaded = False
        logger.info("WorkerManager shutdown")