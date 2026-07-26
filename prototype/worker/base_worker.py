"""Base Worker interface and data contracts for Alfa COS."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("alfa.worker")


class WorkerStatus(Enum):
    """Execution status of a worker."""
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


@dataclass
class WorkerContext:
    """Context provided to a worker during execution."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class WorkerResult:
    """Result returned by a worker after execution."""
    task_id: str
    worker_name: str
    status: WorkerStatus = WorkerStatus.COMPLETED
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == WorkerStatus.COMPLETED


class BaseWorker(ABC):
    """Abstract base class for all Alfa COS workers.

    Workers perform background task execution.
    Only infrastructure is provided in v0.3 — EchoWorker is registered for validation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this worker type."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this worker does."""

    @abstractmethod
    def execute(self, context: WorkerContext) -> WorkerResult:
        """Execute the worker task synchronously or asynchronously.

        Args:
            context: Execution context containing parameters and task_id.

        Returns:
            A WorkerResult indicating success/failure and output data.
        """

    def health(self) -> bool:
        """Check if worker is healthy and ready to run."""
        return True

    def on_pause(self) -> None:
        """Called when worker is paused. Override for cleanup."""

    def on_resume(self) -> None:
        """Called when worker is resumed after pause."""

    def on_stop(self) -> None:
        """Called when worker is stopped. Override for final cleanup."""

    def on_crash(self, error: Exception) -> None:
        """Called when worker crashes. Override for crash-specific recovery."""

    def recover(self, context: WorkerContext) -> Optional[WorkerResult]:
        """Attempt recovery after crash. Returns None to re-raise."""
        return None

    def metadata(self) -> Dict[str, Any]:
        """Return worker metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "healthy": self.health(),
        }
