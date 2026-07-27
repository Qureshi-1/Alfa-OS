"""TaskGraph — directed acyclic graph of tasks with dependency resolution."""

import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger("alfa.mission.task_graph")


class TaskStatus:
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """A single task in the dependency graph."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    status: str = TaskStatus.PENDING
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    goal_id: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self, completed_ids: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        if self.status != TaskStatus.PENDING:
            return False
        return all(dep in completed_ids for dep in self.dependencies)


class TaskGraph:
    """Directed acyclic graph for task dependency management.

    Supports adding tasks with dependencies, topological ordering,
    ready-task discovery, and completion tracking.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskNode] = {}
        self._lock = threading.Lock()

    # ── Mutation ───────────────────────────────────────────────────────────

    def add_task(
        self,
        name: str,
        action: str = "",
        dependencies: Optional[List[str]] = None,
        goal_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskNode:
        """Add a task to the graph. Returns the created node."""
        node = TaskNode(
            name=name,
            action=action,
            dependencies=dependencies or [],
            goal_id=goal_id,
            parameters=parameters or {},
            description=description,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[node.id] = node
            # Register this task as a dependent of its dependencies
            for dep_id in node.dependencies:
                if dep_id in self._tasks:
                    self._tasks[dep_id].dependents.append(node.id)
        return node

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        with self._lock:
            return self._tasks.get(task_id)

    def remove_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            node = self._tasks.pop(task_id)
            # Clean up references from dependencies and dependents
            for dep_id in node.dependencies:
                if dep_id in self._tasks:
                    self._tasks[dep_id].dependents = [
                        d for d in self._tasks[dep_id].dependents if d != task_id
                    ]
            for dep_id in node.dependents:
                if dep_id in self._tasks:
                    self._tasks[dep_id].dependencies = [
                        d for d in self._tasks[dep_id].dependencies if d != task_id
                    ]
            return True

    def update_status(self, task_id: str, status: str) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            self._tasks[task_id].status = status
            return True

    # ── Graph queries ──────────────────────────────────────────────────────

    def get_ready_tasks(self) -> List[TaskNode]:
        """Return all tasks whose dependencies are satisfied."""
        with self._lock:
            completed = {
                nid for nid, n in self._tasks.items()
                if n.status == TaskStatus.COMPLETED
            }
            return [
                n for n in self._tasks.values()
                if n.is_ready(completed)
            ]

    def get_tasks_by_status(self, status: str) -> List[TaskNode]:
        with self._lock:
            return [n for n in self._tasks.values() if n.status == status]

    def get_all_tasks(self) -> List[TaskNode]:
        with self._lock:
            return list(self._tasks.values())

    def count(self) -> int:
        with self._lock:
            return len(self._tasks)

    def has_cycle(self) -> bool:
        """Detect cycles using DFS."""
        with self._lock:
            visited: Set[str] = set()
            in_stack: Set[str] = set()

            def dfs(nid: str) -> bool:
                visited.add(nid)
                in_stack.add(nid)
                node = self._tasks.get(nid)
                if node:
                    for dep_id in node.dependents:
                        if dep_id not in visited:
                            if dfs(dep_id):
                                return True
                        elif dep_id in in_stack:
                            return True
                in_stack.discard(nid)
                return False

            for nid in self._tasks:
                if nid not in visited:
                    if dfs(nid):
                        return True
            return False

    def topological_order(self) -> List[str]:
        """Return task IDs in topological order."""
        with self._lock:
            in_degree: Dict[str, int] = {nid: 0 for nid in self._tasks}
            for nid, node in self._tasks.items():
                for dep_id in node.dependencies:
                    if dep_id in in_degree:
                        in_degree[nid] += 1

            queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
            order = []
            while queue:
                nid = queue.popleft()
                order.append(nid)
                node = self._tasks.get(nid)
                if node:
                    for dep_id in node.dependents:
                        if dep_id in in_degree:
                            in_degree[dep_id] -= 1
                            if in_degree[dep_id] == 0:
                                queue.append(dep_id)
            return order

    # ── Completion ─────────────────────────────────────────────────────────

    def get_completion_ratio(self) -> float:
        with self._lock:
            if not self._tasks:
                return 1.0
            completed = sum(1 for n in self._tasks.values() if n.status == TaskStatus.COMPLETED)
            return completed / len(self._tasks)

    def is_complete(self) -> bool:
        with self._lock:
            return all(
                n.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
                for n in self._tasks.values()
            )

    def get_dependents(self, task_id: str) -> List[TaskNode]:
        with self._lock:
            node = self._tasks.get(task_id)
            if not node:
                return []
            return [self._tasks[did] for did in node.dependents if did in self._tasks]

    def get_dependencies(self, task_id: str) -> List[TaskNode]:
        with self._lock:
            node = self._tasks.get(task_id)
            if not node:
                return []
            return [self._tasks[did] for did in node.dependencies if did in self._tasks]

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tasks": {
                    tid: {
                        "id": t.id, "name": t.name, "description": t.description,
                        "status": t.status, "action": t.action,
                        "parameters": t.parameters, "dependencies": list(t.dependencies),
                        "dependents": list(t.dependents), "goal_id": t.goal_id,
                        "result": t.result, "error": t.error, "metadata": t.metadata,
                    } for tid, t in self._tasks.items()
                },
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        graph = cls()
        for tid, td in data.get("tasks", {}).items():
            node = TaskNode(
                id=td["id"], name=td["name"], description=td.get("description", ""),
                status=td.get("status", TaskStatus.PENDING),
                action=td.get("action", ""),
                parameters=td.get("parameters", {}),
                dependencies=td.get("dependencies", []),
                dependents=td.get("dependents", []),
                goal_id=td.get("goal_id"),
                result=td.get("result"),
                error=td.get("error"),
                metadata=td.get("metadata", {}),
            )
            graph._tasks[tid] = node
        return graph
