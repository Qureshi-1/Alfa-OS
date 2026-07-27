"""Mission — core data model for mission lifecycle management."""

import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.mission")


class MissionStatus(Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class MissionContext:
    """Runtime context for a mission."""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    paused_tasks: int = 0


@dataclass
class Mission:
    """Core mission data model.

    A mission is a high-level objective composed of a goal tree and task graph.
    It tracks lifecycle from creation through completion or failure.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    status: MissionStatus = MissionStatus.CREATED
    priority: MissionPriority = MissionPriority.NORMAL
    context: MissionContext = field(default_factory=MissionContext)
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── Lifecycle operations ───────────────────────────────────────────────

    def activate(self) -> None:
        """Transition mission to active state."""
        if self.status not in (MissionStatus.CREATED, MissionStatus.PAUSED):
            raise ValueError(f"Cannot activate mission in {self.status.value} state")
        self.status = MissionStatus.ACTIVE
        self.context.updated_at = time.time()

    def pause(self) -> None:
        """Pause an active mission."""
        if self.status != MissionStatus.ACTIVE:
            raise ValueError(f"Cannot pause mission in {self.status.value} state")
        self.status = MissionStatus.PAUSED
        self.context.updated_at = time.time()

    def resume(self) -> None:
        """Resume a paused mission."""
        if self.status != MissionStatus.PAUSED:
            raise ValueError(f"Cannot resume mission in {self.status.value} state")
        self.status = MissionStatus.ACTIVE
        self.context.updated_at = time.time()

    def complete(self) -> None:
        """Mark mission as completed."""
        if self.status != MissionStatus.ACTIVE:
            raise ValueError(f"Cannot complete mission in {self.status.value} state")
        self.status = MissionStatus.COMPLETED
        self.context.completed_at = time.time()
        self.context.updated_at = time.time()

    def fail(self, reason: str = "") -> None:
        """Mark mission as failed."""
        if self.status in (MissionStatus.COMPLETED, MissionStatus.CANCELLED):
            raise ValueError(f"Cannot fail mission in {self.status.value} state")
        self.status = MissionStatus.FAILED
        self.metadata["failure_reason"] = reason
        self.context.updated_at = time.time()

    def cancel(self) -> None:
        """Cancel a mission."""
        if self.status == MissionStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed mission")
        self.status = MissionStatus.CANCELLED
        self.context.updated_at = time.time()

    # ── Task accounting ────────────────────────────────────────────────────

    def record_task_completed(self) -> None:
        self.context.completed_tasks += 1
        self.context.updated_at = time.time()

    def record_task_failed(self) -> None:
        self.context.failed_tasks += 1
        self.context.updated_at = time.time()

    def record_task_paused(self) -> None:
        self.context.paused_tasks += 1
        self.context.updated_at = time.time()

    def set_total_tasks(self, count: int) -> None:
        self.context.total_tasks = count
        self.context.updated_at = time.time()

    # ── Serialization ──────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "context": {
                "created_at": self.context.created_at,
                "updated_at": self.context.updated_at,
                "completed_at": self.context.completed_at,
                "total_tasks": self.context.total_tasks,
                "completed_tasks": self.context.completed_tasks,
                "failed_tasks": self.context.failed_tasks,
                "paused_tasks": self.context.paused_tasks,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mission":
        ctx = MissionContext(
            metadata=data.get("context", {}).get("metadata", {}),
            created_at=data.get("context", {}).get("created_at", time.time()),
            updated_at=data.get("context", {}).get("updated_at", time.time()),
            completed_at=data.get("context", {}).get("completed_at"),
            total_tasks=data.get("context", {}).get("total_tasks", 0),
            completed_tasks=data.get("context", {}).get("completed_tasks", 0),
            failed_tasks=data.get("context", {}).get("failed_tasks", 0),
            paused_tasks=data.get("context", {}).get("paused_tasks", 0),
        )
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=MissionStatus(data.get("status", "created")),
            priority=MissionPriority(data.get("priority", 1)),
            context=ctx,
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {}),
        )
