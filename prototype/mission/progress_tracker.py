"""ProgressTracker — calculates and tracks mission progress metrics."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("alfa.mission.progress")


@dataclass
class ProgressSnapshot:
    """Point-in-time snapshot of mission progress."""
    mission_id: str = ""
    goal_completion: float = 0.0
    task_completion: float = 0.0
    overall_progress: float = 0.0
    total_goals: int = 0
    completed_goals: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_tasks: int = 0
    pending_tasks: int = 0
    blocked_tasks: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker:
    """Calculates and tracks progress across missions.

    Maintains a history of progress snapshots and provides
    real-time progress calculation from goal tree and task graph state.
    """

    def __init__(self) -> None:
        self._snapshots: Dict[str, List[ProgressSnapshot]] = {}
        self._start_times: Dict[str, float] = {}

    def start_tracking(self, mission_id: str) -> None:
        """Begin tracking a mission's progress."""
        self._start_times[mission_id] = time.time()
        self._snapshots.setdefault(mission_id, [])

    def stop_tracking(self, mission_id: str) -> None:
        """Stop tracking a mission."""
        self._start_times.pop(mission_id, None)

    def record_snapshot(self, snapshot: ProgressSnapshot) -> None:
        """Record a progress snapshot."""
        self._snapshots.setdefault(snapshot.mission_id, []).append(snapshot)

    def calculate_progress(
        self,
        mission_id: str,
        goal_completion: float,
        task_stats: Dict[str, int],
    ) -> ProgressSnapshot:
        """Calculate current progress from goal and task state.

        Args:
            mission_id: The mission being tracked.
            goal_completion: Goal tree completion ratio (0.0 - 1.0).
            task_stats: Dict with keys: total, completed, failed, active, pending, blocked.

        Returns:
            A ProgressSnapshot with computed metrics.
        """
        total = task_stats.get("total", 0)
        completed = task_stats.get("completed", 0)
        failed = task_stats.get("failed", 0)
        active = task_stats.get("active", 0)
        pending = task_stats.get("pending", 0)
        blocked = task_stats.get("blocked", 0)

        task_completion = completed / total if total > 0 else 0.0
        overall = (goal_completion * 0.4 + task_completion * 0.6) if total > 0 else goal_completion

        elapsed = time.time() - self._start_times.get(mission_id, time.time())

        # Estimate remaining time based on throughput
        estimated_remaining = None
        if completed > 0 and elapsed > 0 and total > completed:
            rate = completed / elapsed
            remaining_tasks = total - completed
            estimated_remaining = remaining_tasks / rate

        snapshot = ProgressSnapshot(
            mission_id=mission_id,
            goal_completion=goal_completion,
            task_completion=task_completion,
            overall_progress=round(overall, 4),
            total_goals=0,
            completed_goals=0,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            active_tasks=active,
            pending_tasks=pending,
            blocked_tasks=blocked,
            elapsed_seconds=round(elapsed, 2),
            estimated_remaining=round(estimated_remaining, 2) if estimated_remaining else None,
        )

        self.record_snapshot(snapshot)
        return snapshot

    def get_latest_snapshot(self, mission_id: str) -> Optional[ProgressSnapshot]:
        snapshots = self._snapshots.get(mission_id, [])
        return snapshots[-1] if snapshots else None

    def get_history(self, mission_id: str, limit: int = 50) -> List[ProgressSnapshot]:
        return self._snapshots.get(mission_id, [])[-limit:]

    def get_mission_ids(self) -> List[str]:
        return list(self._snapshots.keys())

    def clear(self, mission_id: Optional[str] = None) -> None:
        if mission_id:
            self._snapshots.pop(mission_id, None)
            self._start_times.pop(mission_id, None)
        else:
            self._snapshots.clear()
            self._start_times.clear()
