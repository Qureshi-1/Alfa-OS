"""Cognitive Scheduler — Milestone 2 implementation for ALFA COS v1.1.

Components:
- Priority Scheduling: TaskPriority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND), ScheduledTask
- Task Scheduling: PriorityScheduler (manages prioritized task execution)
- Attention Allocation: AttentionAllocator (allocates compute bandwidth & attention frames to active goals)
- Execution Queues: ExecutionQueue (multi-level execution queue manager)
- Resource Manager: CognitiveResourceManager (monitors CPU/Memory/Token resource budgets)
"""

import heapq
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.execution.scheduler")


class TaskPriority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass(order=True)
class ScheduledTask:
    priority: TaskPriority
    created_at: float = field(compare=True)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid4()))
    name: str = field(compare=False, default="")
    goal: str = field(compare=False, default="")
    payload: Dict[str, Any] = field(compare=False, default_factory=dict)
    attention_weight: float = field(compare=False, default=1.0)
    deadline: Optional[float] = field(compare=False, default=None)
    status: str = field(compare=False, default="queued")


class CognitiveResourceManager:
    """Monitors resource constraints (CPU budget, Memory limit, Token concurrency)."""

    def __init__(self, max_concurrent_tokens: int = 8192, max_memory_mb: int = 2048) -> None:
        self.max_concurrent_tokens = max_concurrent_tokens
        self.max_memory_mb = max_memory_mb
        self.active_tokens_used = 0
        self.active_memory_used_mb = 0

    def can_allocate(self, estimated_tokens: int, estimated_memory_mb: int = 100) -> bool:
        tokens_ok = (self.active_tokens_used + estimated_tokens) <= self.max_concurrent_tokens
        memory_ok = (self.active_memory_used_mb + estimated_memory_mb) <= self.max_memory_mb
        return tokens_ok and memory_ok

    def allocate(self, tokens: int, memory_mb: int = 100) -> None:
        self.active_tokens_used += tokens
        self.active_memory_used_mb += memory_mb

    def release(self, tokens: int, memory_mb: int = 100) -> None:
        self.active_tokens_used = max(0, self.active_tokens_used - tokens)
        self.active_memory_used_mb = max(0, self.active_memory_used_mb - memory_mb)

    def get_utilization(self) -> Dict[str, float]:
        return {
            "token_utilization": round(self.active_tokens_used / self.max_concurrent_tokens, 2),
            "memory_utilization": round(self.active_memory_used_mb / self.max_memory_mb, 2),
        }


class AttentionAllocator:
    """Allocates attention focus frames to active goals based on priority and urgency."""

    def __init__(self, total_attention_capacity: float = 100.0) -> None:
        self.capacity = total_attention_capacity
        self.active_focus: Dict[str, float] = {}

    def allocate_attention(self, goal_id: str, priority: TaskPriority) -> float:
        # Base weight inversely proportional to priority enum value
        weight = (6 - int(priority)) * 20.0
        self.active_focus[goal_id] = min(self.capacity, weight)
        self._normalize_attention()
        return self.active_focus.get(goal_id, 0.0)

    def release_attention(self, goal_id: str) -> None:
        if goal_id in self.active_focus:
            del self.active_focus[goal_id]
            self._normalize_attention()

    def _normalize_attention(self) -> None:
        total = sum(self.active_focus.values())
        if total > self.capacity and total > 0:
            scale = self.capacity / total
            for gid in self.active_focus:
                self.active_focus[gid] = round(self.active_focus[gid] * scale, 2)

    def get_focused_goal(self) -> Optional[str]:
        if not self.active_focus:
            return None
        return max(self.active_focus, key=self.active_focus.get)


class ExecutionQueue:
    """Multi-level priority execution queue."""

    def __init__(self) -> None:
        self._queue: List[ScheduledTask] = []

    def push(self, task: ScheduledTask) -> None:
        heapq.heappush(self._queue, task)

    def pop(self) -> Optional[ScheduledTask]:
        if self._queue:
            return heapq.heappop(self._queue)
        return None

    def peek(self) -> Optional[ScheduledTask]:
        if self._queue:
            return self._queue[0]
        return None

    def __len__(self) -> int:
        return len(self._queue)


class CognitiveScheduler:
    """Composition Root for Milestone 2 Cognitive Scheduler."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()
        self.resource_manager = CognitiveResourceManager()
        self.attention_allocator = AttentionAllocator()
        self.queue = ExecutionQueue()
        self.completed_tasks: List[ScheduledTask] = []
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("CognitiveScheduler loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def submit_task(
        self,
        name: str,
        goal: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        payload: Optional[Dict[str, Any]] = None,
        estimated_tokens: int = 500,
    ) -> ScheduledTask:
        now = time.time()
        task = ScheduledTask(
            priority=priority,
            created_at=now,
            name=name,
            goal=goal,
            payload=payload or {},
        )

        # Attention allocation
        self.attention_allocator.allocate_attention(task.task_id, priority)
        self.queue.push(task)

        self._event_bus.publish(Event(
            event_type="CognitiveTaskSubmitted",
            payload={"task_id": task.task_id, "name": name, "priority": priority.name},
            source="cognitive_scheduler",
        ))
        return task

    def step_execution(self) -> Optional[ScheduledTask]:
        task = self.queue.pop()
        if not task:
            return None

        estimated_tokens = task.payload.get("estimated_tokens", 500)
        if not self.resource_manager.can_allocate(estimated_tokens):
            # Re-queue task if resources unavailable
            self.queue.push(task)
            logger.debug("Requeued task %s due to resource constraint", task.task_id[:8])
            return None

        self.resource_manager.allocate(estimated_tokens)
        task.status = "executing"
        
        # Simulate completion & release
        task.status = "completed"
        self.resource_manager.release(estimated_tokens)
        self.attention_allocator.release_attention(task.task_id)
        self.completed_tasks.append(task)

        self._event_bus.publish(Event(
            event_type="CognitiveTaskCompleted",
            payload={"task_id": task.task_id, "name": task.name},
            source="cognitive_scheduler",
        ))
        return task

    def time_slice(self, time_budget_ms: float = 100.0) -> List[ScheduledTask]:
        """Execute task steps within a given cognitive time slice budget."""
        start = time.time()
        executed: List[ScheduledTask] = []
        while (time.time() - start) * 1000.0 < time_budget_ms:
            t = self.step_execution()
            if not t:
                break
            executed.append(t)
        return executed

    def get_stats(self) -> Dict[str, Any]:
        return {
            "queued_tasks": len(self.queue),
            "completed_tasks": len(self.completed_tasks),
            "resources": self.resource_manager.get_utilization(),
            "focused_goal": self.attention_allocator.get_focused_goal(),
        }


class BackgroundTaskScheduler:
    """Scheduler for low-priority asynchronous background tasks."""

    def __init__(self, scheduler: CognitiveScheduler) -> None:
        self.scheduler = scheduler
        self.background_tasks: List[ScheduledTask] = []

    def schedule_background(self, name: str, goal: str, payload: Optional[Dict[str, Any]] = None) -> ScheduledTask:
        task = self.scheduler.submit_task(
            name=name,
            goal=goal,
            priority=TaskPriority.BACKGROUND,
            payload=payload,
        )
        self.background_tasks.append(task)
        return task

