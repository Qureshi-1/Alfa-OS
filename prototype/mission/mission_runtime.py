"""MissionRuntime — orchestrates mission lifecycle, goal trees, task graphs, and progress."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from prototype.common import Event, EventBus
from prototype.mission.mission import Mission, MissionStatus, MissionPriority
from prototype.mission.goal_tree import GoalNode, GoalTree, GoalStatus
from prototype.mission.task_graph import TaskNode, TaskStatus, TaskGraph
from prototype.mission.progress_tracker import ProgressTracker

logger = logging.getLogger("alfa.mission.runtime")


class MissionRuntime:
    """Central orchestrator for mission management.

    Integrates with:
    - EventBus (all mission events)
    - Memory (mission recall + history)
    - Worker system (background execution)
    - Cognition runtime (mission reflection)
    - Diagnostics (metrics + health)
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        memory_manager: Any = None,
        cognition_runtime: Any = None,
        worker_manager: Any = None,
        diagnostics: Any = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._memory = memory_manager
        self._cognition = cognition_runtime
        self._workers = worker_manager
        self._diagnostics = diagnostics

        # Mission storage
        self._missions: Dict[str, Mission] = {}
        self._goal_trees: Dict[str, GoalTree] = {}
        self._task_graphs: Dict[str, TaskGraph] = {}
        self._progress = ProgressTracker()

        # Active mission tracking
        self._active_mission_id: Optional[str] = None

        # Reflection history
        self._reflections: Dict[str, List[Dict[str, Any]]] = {}

        self._loaded = False

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load(self) -> None:
        if self._loaded:
            return

        if self._diagnostics:
            self._diagnostics.register_health_check(
                "mission", self._health_check,
            )

        self._loaded = True
        self._emit("MissionRuntimeStarted", {"timestamp": time.time()})
        logger.info("MissionRuntime loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def shutdown(self) -> None:
        if not self._loaded:
            return
        self._emit("MissionRuntimeShutdown", {
            "active_mission": self._active_mission_id,
            "total_missions": len(self._missions),
        })
        self._loaded = False
        logger.info("MissionRuntime shutdown")

    # ── Mission CRUD ───────────────────────────────────────────────────────

    def create_mission(
        self,
        name: str,
        description: str = "",
        priority: MissionPriority = MissionPriority.NORMAL,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Mission:
        """Create a new mission with goal tree and task graph."""
        mission = Mission(
            name=name,
            description=description,
            priority=priority,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self._missions[mission.id] = mission
        self._goal_trees[mission.id] = GoalTree()
        self._task_graphs[mission.id] = TaskGraph()
        self._progress.start_tracking(mission.id)
        self._reflections[mission.id] = []

        self._emit("MissionCreated", {
            "mission_id": mission.id,
            "name": name,
            "priority": priority.value,
        })

        if self._diagnostics:
            self._diagnostics.increment("mission.created_count")

        logger.info("Mission created: %s (%s)", name, mission.id[:8])
        return mission

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        return self._missions.get(mission_id)

    def list_missions(self, status: Optional[MissionStatus] = None) -> List[Mission]:
        missions = list(self._missions.values())
        if status:
            missions = [m for m in missions if m.status == status]
        return sorted(missions, key=lambda m: m.priority.value, reverse=True)

    def delete_mission(self, mission_id: str) -> bool:
        mission = self._missions.pop(mission_id, None)
        if not mission:
            return False
        self._goal_trees.pop(mission_id, None)
        self._task_graphs.pop(mission_id, None)
        self._progress.clear(mission_id)
        self._reflections.pop(mission_id, None)
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        self._emit("MissionDeleted", {"mission_id": mission_id})
        return True

    # ── Mission lifecycle ──────────────────────────────────────────────────

    def activate_mission(self, mission_id: str) -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.activate()
        self._active_mission_id = mission_id
        self._emit("MissionUpdated", {
            "mission_id": mission_id,
            "status": "active",
        })
        if self._diagnostics:
            self._diagnostics.increment("mission.activation_count")
        return mission

    start_mission = activate_mission

    def pause_mission(self, mission_id: str) -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.pause()
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        self._emit("MissionUpdated", {
            "mission_id": mission_id,
            "status": "paused",
        })
        return mission

    def resume_mission(self, mission_id: str) -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.resume()
        self._active_mission_id = mission_id
        self._emit("MissionUpdated", {
            "mission_id": mission_id,
            "status": "active",
        })
        return mission

    def complete_mission(self, mission_id: str, outcome: Optional[str] = None) -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.complete()
        if outcome:
            mission.metadata["outcome"] = outcome
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        self._progress.stop_tracking(mission_id)
        self._emit("MissionFinished", {
            "mission_id": mission_id,
            "name": mission.name,
            "completed_at": mission.context.completed_at,
        })
        if self._diagnostics:
            self._diagnostics.increment("mission.completed_count")
        # Store in memory
        self._store_mission_memory(mission)
        return mission

    def fail_mission(self, mission_id: str, reason: str = "") -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.fail(reason)
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        self._emit("MissionFinished", {
            "mission_id": mission_id,
            "name": mission.name,
            "status": "failed",
            "reason": reason,
        })
        if self._diagnostics:
            self._diagnostics.increment("mission.failed_count")
        return mission

    def cancel_mission(self, mission_id: str) -> Mission:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.cancel()
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        self._emit("MissionFinished", {
            "mission_id": mission_id,
            "name": mission.name,
            "status": "cancelled",
        })
        return mission

    # ── Goal tree operations ───────────────────────────────────────────────

    def add_goal(
        self,
        mission_id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: str = "",
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GoalNode:
        tree = self._goal_trees.get(mission_id)
        if not tree:
            raise ValueError(f"No goal tree for mission {mission_id}")
        node = tree.add_goal(name, parent_id=parent_id, description=description,
                             priority=priority, metadata=metadata)
        self._emit("GoalCreated", {
            "mission_id": mission_id,
            "goal_id": node.id,
            "name": name,
        })
        return node

    def complete_goal(self, mission_id: str, goal_id: str) -> bool:
        tree = self._goal_trees.get(mission_id)
        if not tree:
            return False
        result = tree.update_status(goal_id, GoalStatus.COMPLETED)
        if result:
            self._emit("GoalCompleted", {
                "mission_id": mission_id,
                "goal_id": goal_id,
            })
            # Check if all goals complete
            if tree.is_complete(goal_id):
                mission = self._missions.get(mission_id)
                if mission:
                    mission.record_task_completed()
        return result

    def get_goal_tree(self, mission_id: str) -> Optional[GoalTree]:
        return self._goal_trees.get(mission_id)

    def get_goal_completion(self, mission_id: str) -> float:
        tree = self._goal_trees.get(mission_id)
        if not tree:
            return 0.0
        roots = tree.get_root_goals()
        if not roots:
            return 0.0
        return sum(tree.get_completion_ratio(r.id) for r in roots) / len(roots)

    # ── Task graph operations ──────────────────────────────────────────────

    def add_task(
        self,
        mission_id: str,
        name: str,
        action: str = "",
        dependencies: Optional[List[str]] = None,
        goal_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> TaskNode:
        graph = self._task_graphs.get(mission_id)
        if not graph:
            raise ValueError(f"No task graph for mission {mission_id}")
        node = graph.add_task(name, action=action, dependencies=dependencies,
                              goal_id=goal_id, parameters=parameters, description=description)
        # Link task to goal if specified
        if goal_id:
            tree = self._goal_trees.get(mission_id)
            if tree:
                tree.assign_task(goal_id, node.id)
        # Update mission total task count
        mission = self._missions.get(mission_id)
        if mission:
            mission.set_total_tasks(graph.count())
        self._emit("TaskCreated", {
            "mission_id": mission_id,
            "task_id": node.id,
            "name": name,
        })
        return node

    def start_task(self, mission_id: str, task_id: str) -> bool:
        graph = self._task_graphs.get(mission_id)
        if not graph:
            return False
        result = graph.update_status(task_id, TaskStatus.RUNNING)
        if result:
            self._emit("TaskStarted", {
                "mission_id": mission_id,
                "task_id": task_id,
            })
        return result

    def complete_task(self, mission_id: str, task_id: str, result: Any = None) -> bool:
        graph = self._task_graphs.get(mission_id)
        if not graph:
            return False
        task = graph.get_task(task_id)
        if task:
            task.result = result
        success = graph.update_status(task_id, TaskStatus.COMPLETED)
        if success:
            mission = self._missions.get(mission_id)
            if mission:
                mission.record_task_completed()
            self._emit("TaskCompleted", {
                "mission_id": mission_id,
                "task_id": task_id,
            })
        return success

    def fail_task(self, mission_id: str, task_id: str, error: str = "") -> bool:
        graph = self._task_graphs.get(mission_id)
        if not graph:
            return False
        task = graph.get_task(task_id)
        if task:
            task.error = error
        success = graph.update_status(task_id, TaskStatus.FAILED)
        if success:
            mission = self._missions.get(mission_id)
            if mission:
                mission.record_task_failed()
            self._emit("TaskCompleted", {
                "mission_id": mission_id,
                "task_id": task_id,
                "status": "failed",
                "error": error,
            })
        return success

    def get_ready_tasks(self, mission_id: str) -> List[TaskNode]:
        graph = self._task_graphs.get(mission_id)
        return graph.get_ready_tasks() if graph else []

    def get_task_graph(self, mission_id: str) -> Optional[TaskGraph]:
        return self._task_graphs.get(mission_id)

    def next_action(self, mission_id: str) -> Optional[TaskNode]:
        """Return the next recommended task to execute."""
        ready = self.get_ready_tasks(mission_id)
        if not ready:
            return None
        # Priority: highest priority task first, then by dependency count (most constrained first)
        return max(ready, key=lambda t: (t.metadata.get("priority", 0), len(t.dependencies)))

    # ── Progress ───────────────────────────────────────────────────────────

    def get_progress(self, mission_id: str) -> Optional[Dict[str, Any]]:
        graph = self._task_graphs.get(mission_id)
        if not graph:
            return None
        tasks = graph.get_all_tasks()
        stats = {
            "total": len(tasks),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "active": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "blocked": sum(1 for t in tasks if t.status == TaskStatus.BLOCKED),
        }
        goal_comp = self.get_goal_completion(mission_id)
        snapshot = self._progress.calculate_progress(mission_id, goal_comp, stats)
        return {
            "overall_progress": snapshot.overall_progress,
            "goal_completion": snapshot.goal_completion,
            "task_completion": snapshot.task_completion,
            "elapsed_seconds": snapshot.elapsed_seconds,
            "estimated_remaining": snapshot.estimated_remaining,
            "tasks": stats,
        }

    # ── Reflection ─────────────────────────────────────────────────────────

    def reflect(self, mission_id: str) -> Dict[str, Any]:
        """Perform mission reflection: analyze progress and generate insights."""
        mission = self._missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}

        progress = self.get_progress(mission_id) or {}
        goal_tree = self._goal_trees.get(mission_id)
        task_graph = self._task_graphs.get(mission_id)

        # Build reflection
        insights = []
        recommendations = []

        # Analyze task failures
        if task_graph:
            failed = task_graph.get_tasks_by_status(TaskStatus.FAILED)
            if failed:
                insights.append(f"{len(failed)} tasks failed")
                recommendations.append("Review failed tasks and consider replanning")

            ready = task_graph.get_ready_tasks()
            if ready:
                insights.append(f"{len(ready)} tasks ready to execute")

            blocked = task_graph.get_tasks_by_status(TaskStatus.BLOCKED)
            if blocked:
                insights.append(f"{len(blocked)} tasks blocked")
                recommendations.append("Resolve blocking dependencies")

        # Analyze goal completion
        if goal_tree:
            incomplete = goal_tree.get_goals_by_status(GoalStatus.PENDING)
            if incomplete:
                insights.append(f"{len(incomplete)} goals still pending")

        # Overall assessment
        overall = progress.get("overall_progress", 0.0)
        if overall >= 1.0:
            insights.append("Mission is fully complete")
        elif overall >= 0.75:
            insights.append("Mission is nearing completion")
        elif overall == 0.0 and mission.status == MissionStatus.ACTIVE:
            insights.append("Mission just started — no progress yet")

        reflection = {
            "mission_id": mission_id,
            "status": mission.status.value,
            "overall_progress": overall,
            "insights": insights,
            "recommendations": recommendations,
            "timestamp": time.time(),
        }

        self._reflections.setdefault(mission_id, []).append(reflection)
        self._emit("MissionReflection", {
            "mission_id": mission_id,
            "overall_progress": overall,
            "insight_count": len(insights),
        })

        return reflection

    def get_reflections(self, mission_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self._reflections.get(mission_id, [])[-limit:]

    # ── Memory integration ─────────────────────────────────────────────────

    def _store_mission_memory(self, mission: Mission) -> None:
        if not self._memory:
            return
        try:
            if hasattr(self._memory, "remember"):
                self._memory.remember(
                    content=f"Mission '{mission.name}' {mission.status.value}: "
                            f"{mission.context.completed_tasks}/{mission.context.total_tasks} tasks",
                    tags=["mission", mission.status.value],
                    importance=4,
                )
        except Exception as exc:
            logger.debug("Memory store failed: %s", exc)

    def recall_missions(self, query: str = "", limit: int = 10) -> List[Any]:
        if not self._memory:
            return []
        try:
            if hasattr(self._memory, "recall"):
                return self._memory.recall(query, limit=limit)
        except Exception as exc:
            logger.debug("Memory recall failed: %s", exc)
        return []

    # ── Stats & Health ─────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        missions = list(self._missions.values())
        return {
            "loaded": self._loaded,
            "total_missions": len(missions),
            "active_mission": self._active_mission_id,
            "by_status": {
                status.value: sum(1 for m in missions if m.status == status)
                for status in MissionStatus
            },
            "total_goals": sum(len(self._goal_trees.get(m.id, GoalTree()).get_all_goals())
                              for m in missions),
            "total_tasks": sum(len(self._task_graphs.get(m.id, TaskGraph()).get_all_tasks())
                               for m in missions),
        }

    def _health_check(self) -> Any:
        from prototype.diagnostics.diagnostics import HealthStatus
        return HealthStatus(
            component="mission",
            healthy=self._loaded,
            message="Mission runtime operational" if self._loaded else "Not loaded",
        )

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(Event(
            event_type=event_type, payload=payload, source="mission_runtime",
        ))
