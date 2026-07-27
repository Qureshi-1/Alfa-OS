"""Execution results — per-task and aggregated results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    ROLLED_BACK = "rolled_back"
    TIMED_OUT = "timed_out"


@dataclass
class TaskExecutionResult:
    """Result of executing a single task."""
    task_id: str = ""
    action: str = ""
    status: str = TaskStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    handler_used: str = ""
    handler_type: str = ""
    execution_time_ms: float = 0.0
    retry_count: int = 0
    rollback_success: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == TaskStatus.COMPLETED


@dataclass
class ExecutionPlanResult:
    """Aggregated result of executing a full plan of tasks."""
    id: str = field(default_factory=lambda: str(uuid4()))
    task_results: List[TaskExecutionResult] = field(default_factory=list)
    total_time_ms: float = 0.0
    mode: str = "sequential"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return all(r.success for r in self.task_results)

    @property
    def failed_tasks(self) -> List[TaskExecutionResult]:
        return [r for r in self.task_results if not r.success]

    @property
    def succeeded_tasks(self) -> List[TaskExecutionResult]:
        return [r for r in self.task_results if r.success]

    @property
    def output(self) -> Any:
        outputs = [r.output for r in self.task_results if r.output is not None]
        return outputs[-1] if outputs else None
