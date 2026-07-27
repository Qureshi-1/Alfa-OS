"""ExecutionHistory — stores and queries execution records."""

import threading
import time
from typing import Any, Dict, List, Optional

from prototype.execution.execution_result import TaskExecutionResult


class ExecutionHistory:
    """Stores execution records with query support."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: List[TaskExecutionResult] = []
        self._max_records = max_records
        self._lock = threading.Lock()

    def add_record(self, result: TaskExecutionResult) -> None:
        with self._lock:
            self._records.append(result)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records:]

    def get_task_history(self, task_id: str) -> List[TaskExecutionResult]:
        with self._lock:
            return [r for r in self._records if r.task_id == task_id]

    def get_action_history(self, action: str) -> List[TaskExecutionResult]:
        with self._lock:
            return [r for r in self._records if r.action == action]

    def get_recent(self, limit: int = 50) -> List[TaskExecutionResult]:
        with self._lock:
            return list(self._records[-limit:])

    def get_failed(self) -> List[TaskExecutionResult]:
        with self._lock:
            return [r for r in self._records if not r.success]

    def get_successful(self) -> List[TaskExecutionResult]:
        with self._lock:
            return [r for r in self._records if r.success]

    def query(
        self,
        action: Optional[str] = None,
        status: Optional[str] = None,
        handler_type: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 50,
    ) -> List[TaskExecutionResult]:
        with self._lock:
            results = list(self._records)
        if action:
            results = [r for r in results if r.action == action]
        if status:
            results = [r for r in results if r.status == status]
        if handler_type:
            results = [r for r in results if r.handler_type == handler_type]
        if since:
            results = [r for r in results if r.metadata.get("completed_at", 0) >= since]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            records = list(self._records)
        total = len(records)
        if total == 0:
            return {"total": 0, "successful": 0, "failed": 0, "avg_time_ms": 0.0}
        successful = sum(1 for r in records if r.success)
        avg_time = sum(r.execution_time_ms for r in records) / total
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "avg_time_ms": round(avg_time, 2),
        }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
