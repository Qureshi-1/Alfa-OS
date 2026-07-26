"""Worker Lifecycle — tracks worker execution state, history, and crash recovery."""

import logging
import time
from typing import Dict, List, Optional

from prototype.worker.base_worker import WorkerResult, WorkerStatus

logger = logging.getLogger("alfa.worker.lifecycle")


class WorkerLifecycle:
    """Manages worker state transitions, execution history, and crash recovery."""

    def __init__(self, max_history: int = 100) -> None:
        self._max_history = max_history
        self._states: Dict[str, WorkerStatus] = {}
        self._history: List[WorkerResult] = []
        self._crash_count: Dict[str, int] = {}
        self._last_crash: Dict[str, float] = {}
        self._max_crash_retries: int = 3

    def transition(self, task_id: str, new_status: WorkerStatus) -> WorkerStatus:
        old_status = self._states.get(task_id, WorkerStatus.IDLE)
        self._states[task_id] = new_status
        logger.debug("Task %s: %s -> %s", task_id[:8], old_status.value, new_status.value)
        return new_status

    def get_status(self, task_id: str) -> WorkerStatus:
        return self._states.get(task_id, WorkerStatus.IDLE)

    def record_result(self, result: WorkerResult) -> None:
        self._states[result.task_id] = result.status
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def record_crash(self, task_id: str, worker_name: str) -> int:
        """Record a crash and return the crash count for this worker."""
        self._crash_count[worker_name] = self._crash_count.get(worker_name, 0) + 1
        self._last_crash[worker_name] = time.time()
        count = self._crash_count[worker_name]
        logger.warning("Worker '%s' crashed (count: %d)", worker_name, count)
        return count

    def can_recover(self, worker_name: str) -> bool:
        """Check if a worker is allowed to attempt recovery."""
        return self._crash_count.get(worker_name, 0) < self._max_crash_retries

    def reset_crash_count(self, worker_name: str) -> None:
        """Reset crash count after successful execution."""
        self._crash_count.pop(worker_name, None)
        self._last_crash.pop(worker_name, None)

    def get_crash_info(self, worker_name: str) -> Dict[str, int]:
        return {
            "crash_count": self._crash_count.get(worker_name, 0),
            "max_retries": self._max_crash_retries,
            "last_crash": self._last_crash.get(worker_name, 0),
        }

    def get_history(self, worker_name: Optional[str] = None, limit: int = 50) -> List[WorkerResult]:
        if worker_name:
            results = [r for r in self._history if r.worker_name == worker_name]
        else:
            results = self._history
        return results[-limit:]

    def get_stats(self) -> Dict[str, int]:
        return {
            "total": len(self._history),
            "completed": sum(1 for r in self._history if r.status == WorkerStatus.COMPLETED),
            "failed": sum(1 for r in self._history if r.status == WorkerStatus.FAILED),
            "cancelled": sum(1 for r in self._history if r.status == WorkerStatus.CANCELLED),
        }

    def clear(self) -> None:
        self._states.clear()
        self._history.clear()
        self._crash_count.clear()
        self._last_crash.clear()