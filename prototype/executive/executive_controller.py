"""Executive Controller — manages cognitive execution, scheduling, and recovery.

The Executive Controller acts as the operating system scheduler for cognition.
It receives goals from the Kernel, prioritizes them, schedules execution
through the cognitive pipeline, and handles failures/recovery.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import Goal, Context, Plan, EngineResult, Event, EventBus

logger = logging.getLogger("alfa.executive")


class ExecutionStatus(Enum):
    """Possible states for a cognitive execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionPriority(Enum):
    """Priority levels for goal execution."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Execution:
    """Represents a single cognitive execution unit."""
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    goal: Optional[Goal] = None
    plan: Optional[Plan] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    result: Optional[EngineResult] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 2


class ExecutiveController:
    """Manages cognitive execution lifecycle.

    Responsibilities:
    - Receive and prioritize goals
    - Schedule execution through the cognitive pipeline
    - Track execution state
    - Handle failures and recovery
    - Cancel and resume execution
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._loaded = False
        self._event_bus = event_bus
        self._executions: Dict[str, Execution] = {}
        self._execution_history: List[Execution] = []
        self._max_history = 100

    def load(self) -> None:
        """Initialize the Executive Controller."""
        self._loaded = True
        logger.info("Executive Controller loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Goal Execution ────────────────────────────────────────────────────

    def execute_goal(
        self,
        goal: Goal,
        context: Context,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
    ) -> Execution:
        """Create an execution for a goal and start it.

        Args:
            goal: The goal to execute.
            context: Current execution context.
            priority: Execution priority level.

        Returns:
            The created Execution object.
        """
        execution = Execution(
            goal=goal,
            priority=priority,
            metadata={"context_task": context.current_task},
        )
        self._executions[execution.execution_id] = execution
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = time.time()

        logger.info(
            "Execution started: id=%s goal=%s priority=%s",
            execution.execution_id[:8],
            goal.name,
            priority.name,
        )

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="ExecutionStarted",
                payload={
                    "execution_id": execution.execution_id,
                    "goal": goal.name,
                    "priority": priority.name,
                },
                source="executive",
            ))

        return execution

    def complete_execution(
        self, execution_id: str, result: EngineResult
    ) -> None:
        """Mark an execution as completed with a result."""
        execution = self._executions.get(execution_id)
        if not execution:
            logger.warning("Execution not found: %s", execution_id[:8])
            return

        execution.status = ExecutionStatus.COMPLETED
        execution.result = result
        execution.completed_at = time.time()

        latency_ms = (execution.completed_at - (execution.started_at or execution.created_at)) * 1000

        logger.info(
            "Execution completed: id=%s goal=%s latency_ms=%.1f success=%s",
            execution_id[:8],
            execution.goal.name if execution.goal else "unknown",
            latency_ms,
            result.success,
        )

        self._archive_execution(execution)

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="ExecutionCompleted",
                payload={
                    "execution_id": execution_id,
                    "success": result.success,
                    "latency_ms": latency_ms,
                },
                source="executive",
            ))

    def fail_execution(self, execution_id: str, error: str) -> bool:
        """Mark an execution as failed. Returns True if retried."""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.retry_count < execution.max_retries:
            execution.retry_count += 1
            execution.status = ExecutionStatus.PENDING
            logger.warning(
                "Execution retry %d/%d: id=%s error=%s",
                execution.retry_count,
                execution.max_retries,
                execution_id[:8],
                error,
            )
            return True

        execution.status = ExecutionStatus.FAILED
        execution.error = error
        execution.completed_at = time.time()
        logger.error("Execution failed: id=%s error=%s", execution_id[:8], error)
        self._archive_execution(execution)
        return False

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a pending or running execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED):
            return False

        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = time.time()
        logger.info("Execution cancelled: id=%s", execution_id[:8])
        self._archive_execution(execution)
        return True

    # ── Query ─────────────────────────────────────────────────────────────

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get an active execution by ID."""
        return self._executions.get(execution_id)

    def get_active_executions(self) -> List[Execution]:
        """Return all currently active (pending/running) executions."""
        return [
            e for e in self._executions.values()
            if e.status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
        ]

    def get_execution_history(self) -> List[Execution]:
        """Return recent execution history."""
        return self._execution_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Return execution statistics."""
        completed = [e for e in self._execution_history if e.status == ExecutionStatus.COMPLETED]
        failed = [e for e in self._execution_history if e.status == ExecutionStatus.FAILED]
        latencies = []
        for e in completed:
            if e.started_at and e.completed_at:
                latencies.append((e.completed_at - e.started_at) * 1000)

        return {
            "active": len(self.get_active_executions()),
            "completed": len(completed),
            "failed": len(failed),
            "total_history": len(self._execution_history),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        }

    # ── Internal ──────────────────────────────────────────────────────────

    def _archive_execution(self, execution: Execution) -> None:
        """Move a finished execution from active to history."""
        self._executions.pop(execution.execution_id, None)
        self._execution_history.append(execution)
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Shutdown the Executive Controller."""
        # Cancel any active executions
        for execution_id in list(self._executions.keys()):
            self.cancel_execution(execution_id)
        self._loaded = False
        logger.info("Executive Controller shutdown")
