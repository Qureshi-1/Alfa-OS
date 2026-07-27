"""ExecutionScheduler — computes execution order from task dependencies."""

import logging
from collections import deque
from typing import Dict, List, Optional, Set

from prototype.execution.execution_context import ExecutionContext, ExecutionMode

logger = logging.getLogger("alfa.execution.scheduler")


class ExecutionScheduler:
    """Computes execution order respecting dependencies and execution mode."""

    def __init__(self) -> None:
        self._contexts: Dict[str, ExecutionContext] = {}

    def register(self, ctx: ExecutionContext) -> None:
        self._contexts[ctx.task_id] = ctx

    def unregister(self, task_id: str) -> bool:
        removed = self._contexts.pop(task_id, None)
        return removed is not None

    def get_context(self, task_id: str) -> Optional[ExecutionContext]:
        return self._contexts.get(task_id)

    def clear(self) -> None:
        self._contexts.clear()

    def get_execution_order(
        self, mode: ExecutionMode = ExecutionMode.DEPENDENCY_AWARE
    ) -> List[List[str]]:
        """Return execution batches. Each inner list is a batch that can run concurrently."""
        if mode == ExecutionMode.SEQUENTIAL:
            return self._sequential_order()
        if mode == ExecutionMode.PARALLEL:
            return self._parallel_order()
        if mode == ExecutionMode.PIPELINE:
            return self._pipeline_order()
        return self._dependency_aware_order()

    def _sequential_order(self) -> List[List[str]]:
        """One task per batch, in topological order."""
        batches = self._dependency_aware_order()
        return [[tid] for batch in batches for tid in batch]

    def _parallel_order(self) -> List[List[str]]:
        """All tasks in one batch (no dependency checks)."""
        all_ids = list(self._contexts.keys())
        return [all_ids] if all_ids else []

    def _pipeline_order(self) -> List[List[str]]:
        """Stage-based: group by dependency depth."""
        depth = self._compute_depths()
        stages: Dict[int, List[str]] = {}
        for tid, d in depth.items():
            stages.setdefault(d, []).append(tid)
        return [stages[d] for d in sorted(stages.keys())]

    def _dependency_aware_order(self) -> List[List[str]]:
        """Topological sort with batching of independent tasks."""
        ids = set(self._contexts.keys())
        in_degree: Dict[str, int] = {tid: 0 for tid in ids}
        dependents: Dict[str, List[str]] = {tid: [] for tid in ids}

        for tid, ctx in self._contexts.items():
            for dep in ctx.dependencies:
                if dep in ids:
                    dependents[dep].append(tid)
                    in_degree[tid] += 1

        batches = []
        ready = deque(tid for tid, deg in in_degree.items() if deg == 0)

        while ready:
            batch = list(ready)
            batches.append(batch)
            ready.clear()
            for tid in batch:
                for dep_tid in dependents[tid]:
                    in_degree[dep_tid] -= 1
                    if in_degree[dep_tid] == 0:
                        ready.append(dep_tid)

        return batches

    def _compute_depths(self) -> Dict[str, int]:
        """Compute dependency depth for each task."""
        depths: Dict[str, int] = {}
        ids = set(self._contexts.keys())

        def _depth(tid: str) -> int:
            if tid in depths:
                return depths[tid]
            ctx = self._contexts.get(tid)
            if not ctx or not ctx.dependencies:
                depths[tid] = 0
                return 0
            dep_depths = [
                _depth(d) for d in ctx.dependencies if d in ids
            ]
            depths[tid] = (max(dep_depths) + 1) if dep_depths else 0
            return depths[tid]

        for tid in ids:
            _depth(tid)
        return depths

    def validate_dependencies(self) -> List[str]:
        """Return list of errors for invalid dependencies."""
        ids = set(self._contexts.keys())
        errors = []
        for tid, ctx in self._contexts.items():
            for dep in ctx.dependencies:
                if dep not in ids:
                    errors.append(f"Task {tid} depends on unknown task {dep}")
        if self._has_cycle(ids):
            errors.append("Dependency cycle detected")
        return errors

    def _has_cycle(self, ids: Set[str]) -> bool:
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        adj: Dict[str, List[str]] = {tid: [] for tid in ids}
        for tid, ctx in self._contexts.items():
            for dep in ctx.dependencies:
                if dep in ids:
                    adj[dep].append(tid)

        def dfs(nid: str) -> bool:
            visited.add(nid)
            in_stack.add(nid)
            for nxt in adj.get(nid, []):
                if nxt not in visited:
                    if dfs(nxt):
                        return True
                elif nxt in in_stack:
                    return True
            in_stack.discard(nid)
            return False

        for tid in ids:
            if tid not in visited:
                if dfs(tid):
                    return True
        return False
