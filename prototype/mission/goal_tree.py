"""GoalTree — hierarchical goal decomposition for missions."""

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger("alfa.mission.goal_tree")


class GoalStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class GoalNode:
    """A single goal in the hierarchy."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    status: str = GoalStatus.PENDING
    priority: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_leaf(self) -> bool:
        return len(self.children_ids) == 0

    def is_root(self) -> bool:
        return self.parent_id is None


class GoalTree:
    """Hierarchical goal tree for mission decomposition.

    Maintains parent-child relationships and provides traversal,
    lookup, and completion status aggregation.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, GoalNode] = {}
        self._root_ids: List[str] = []
        self._lock = threading.Lock()

    # ── Mutation ───────────────────────────────────────────────────────────

    def add_goal(
        self,
        name: str,
        parent_id: Optional[str] = None,
        description: str = "",
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GoalNode:
        """Add a goal to the tree. Returns the created node."""
        node = GoalNode(
            name=name,
            description=description,
            parent_id=parent_id,
            priority=priority,
            metadata=metadata or {},
        )
        with self._lock:
            self._nodes[node.id] = node
            if parent_id and parent_id in self._nodes:
                self._nodes[parent_id].children_ids.append(node.id)
            else:
                node.parent_id = None
                self._root_ids.append(node.id)
        return node

    def get_goal(self, goal_id: str) -> Optional[GoalNode]:
        with self._lock:
            return self._nodes.get(goal_id)

    def remove_goal(self, goal_id: str) -> bool:
        """Remove a goal and all its descendants."""
        with self._lock:
            if goal_id not in self._nodes:
                return False
            node = self._nodes[goal_id]
            # Remove from parent's children list
            if node.parent_id and node.parent_id in self._nodes:
                parent = self._nodes[node.parent_id]
                parent.children_ids = [c for c in parent.children_ids if c != goal_id]
            else:
                self._root_ids = [r for r in self._root_ids if r != goal_id]
            # Recursively remove children
            self._remove_recursive(goal_id)
            return True

    def _remove_recursive(self, goal_id: str) -> None:
        node = self._nodes.pop(goal_id, None)
        if node:
            for child_id in node.children_ids:
                self._remove_recursive(child_id)

    def update_status(self, goal_id: str, status: str) -> bool:
        with self._lock:
            if goal_id not in self._nodes:
                return False
            self._nodes[goal_id].status = status
            return True

    def assign_task(self, goal_id: str, task_id: str) -> bool:
        """Attach a task to a goal."""
        with self._lock:
            if goal_id not in self._nodes:
                return False
            if task_id not in self._nodes[goal_id].task_ids:
                self._nodes[goal_id].task_ids.append(task_id)
            return True

    # ── Queries ────────────────────────────────────────────────────────────

    def get_children(self, goal_id: str) -> List[GoalNode]:
        with self._lock:
            node = self._nodes.get(goal_id)
            if not node:
                return []
            return [self._nodes[cid] for cid in node.children_ids if cid in self._nodes]

    def get_parents(self, goal_id: str) -> List[GoalNode]:
        """Return ancestors from parent up to root."""
        path = []
        with self._lock:
            node = self._nodes.get(goal_id)
            while node and node.parent_id:
                parent = self._nodes.get(node.parent_id)
                if parent:
                    path.append(parent)
                node = parent
        return path

    def get_root_goals(self) -> List[GoalNode]:
        with self._lock:
            return [self._nodes[rid] for rid in self._root_ids if rid in self._nodes]

    def get_all_goals(self) -> List[GoalNode]:
        with self._lock:
            return list(self._nodes.values())

    def get_goals_by_status(self, status: str) -> List[GoalNode]:
        with self._lock:
            return [n for n in self._nodes.values() if n.status == status]

    def count(self) -> int:
        with self._lock:
            return len(self._nodes)

    # ── Completion ─────────────────────────────────────────────────────────

    def get_completion_ratio(self, goal_id: str) -> float:
        """Calculate completion ratio for a goal and its descendants."""
        with self._lock:
            node = self._nodes.get(goal_id)
            if not node:
                return 0.0
            return self._calc_completion(node)

    def _calc_completion(self, node: GoalNode) -> float:
        if not node.children_ids:
            return 1.0 if node.status == GoalStatus.COMPLETED else 0.0
        child_ratios = []
        for cid in node.children_ids:
            child = self._nodes.get(cid)
            if child:
                child_ratios.append(self._calc_completion(child))
        if not child_ratios:
            return 1.0 if node.status == GoalStatus.COMPLETED else 0.0
        return sum(child_ratios) / len(child_ratios)

    def get_all_tasks(self, goal_id: str) -> List[str]:
        """Collect all task IDs under a goal and its descendants."""
        with self._lock:
            tasks = []
            node = self._nodes.get(goal_id)
            if node:
                self._collect_tasks(node, tasks)
            return tasks

    def _collect_tasks(self, node: GoalNode, tasks: List[str]) -> None:
        tasks.extend(node.task_ids)
        for cid in node.children_ids:
            child = self._nodes.get(cid)
            if child:
                self._collect_tasks(child, tasks)

    def is_complete(self, goal_id: str) -> bool:
        """Check if goal and all descendants are completed."""
        return self.get_completion_ratio(goal_id) >= 1.0

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "root_ids": list(self._root_ids),
                "nodes": {nid: {
                    "id": n.id, "name": n.name, "description": n.description,
                    "status": n.status, "priority": n.priority,
                    "parent_id": n.parent_id, "children_ids": list(n.children_ids),
                    "task_ids": list(n.task_ids), "metadata": n.metadata,
                } for nid, n in self._nodes.items()},
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalTree":
        tree = cls()
        for nid, nd in data.get("nodes", {}).items():
            node = GoalNode(
                id=nd["id"], name=nd["name"], description=nd.get("description", ""),
                status=nd.get("status", GoalStatus.PENDING),
                priority=nd.get("priority", 0),
                parent_id=nd.get("parent_id"),
                children_ids=nd.get("children_ids", []),
                task_ids=nd.get("task_ids", []),
                metadata=nd.get("metadata", {}),
            )
            tree._nodes[nid] = node
        tree._root_ids = data.get("root_ids", [])
        return tree
