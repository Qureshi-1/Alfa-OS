"""ExecutionRuntime — composition root for the execution engine.

Wires TaskExecutor, ExecutionScheduler, ExecutionHistory, and ToolRouter
into a single runtime that executes tasks from MissionRuntime's TaskGraph.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from prototype.common import Event, EventBus
from prototype.execution.execution_context import ExecutionContext, ExecutionMode
from prototype.execution.execution_history import ExecutionHistory
from prototype.execution.execution_result import (
    ExecutionPlanResult, TaskExecutionResult, TaskStatus,
)
from prototype.execution.execution_scheduler import ExecutionScheduler
from prototype.execution.task_executor import TaskExecutor
from prototype.execution.tool_router import ToolRouter

logger = logging.getLogger("alfa.execution.runtime")


class ExecutionRuntime:
    """Central runtime for task execution.

    Integrates with:
    - EventBus (execution events)
    - MissionRuntime (reads task graphs)
    - CognitionRuntime (cognitive execution)
    - WorkerManager (worker execution)
    - AgentRuntime (agent execution)
    - Diagnostics (metrics + health)
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        mission_runtime: Any = None,
        cognition_runtime: Any = None,
        worker_manager: Any = None,
        agent_runtime: Any = None,
        diagnostics: Any = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._mission = mission_runtime
        self._cognition = cognition_runtime
        self._workers = worker_manager
        self._agents = agent_runtime
        self._diagnostics = diagnostics

        # Core components
        self._router = ToolRouter()
        self._scheduler = ExecutionScheduler()
        self._history = ExecutionHistory()
        self._executor = TaskExecutor(
            tool_router=self._router,
            event_bus=self._event_bus,
            diagnostics=self._diagnostics,
        )

        # Active executions
        self._active: Dict[str, bool] = {}  # task_id -> running

        self._loaded = False
        self._execution_count = 0

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load(self) -> None:
        if self._loaded:
            return

        # Wire handlers from integrated runtimes
        self._wire_handlers()

        if self._diagnostics:
            self._diagnostics.register_health_check(
                "execution", self._health_check,
            )

        self._loaded = True
        self._emit("ExecutionRuntimeStarted", {"timestamp": time.time()})
        logger.info("ExecutionRuntime loaded")

    def _wire_handlers(self) -> None:
        """Wire tool/agent/worker handlers from integrated runtimes."""
        if self._cognition:
            # Wire cognition executor's tool/agent/worker handlers
            executor = getattr(self._cognition, "executor", None)
            if executor:
                for name in getattr(executor, "_tool_handlers", {}):
                    handler = executor._tool_handlers[name]
                    self._router.register_tool(name, handler)
                for name in getattr(executor, "_agent_handlers", {}):
                    handler = executor._agent_handlers[name]
                    self._router.register_agent(name, handler)
                for name in getattr(executor, "_worker_handlers", {}):
                    handler = executor._worker_handlers[name]
                    self._router.register_worker(name, handler)

    def is_loaded(self) -> bool:
        return self._loaded

    def shutdown(self) -> None:
        if not self._loaded:
            return
        self._emit("ExecutionRuntimeShutdown", {
            "execution_count": self._execution_count,
        })
        self._scheduler.clear()
        self._router.clear()
        self._active.clear()
        self._loaded = False
        logger.info("ExecutionRuntime shutdown")

    # ── Handler registration ───────────────────────────────────────────────

    def register_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._router.register_tool(name, handler)

    def register_agent(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._router.register_agent(name, handler)

    def register_worker(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._router.register_worker(name, handler)

    def register_cognition(self, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._router.register_cognition(handler)

    def register_rollback(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._executor.register_rollback(action, handler)

    # ── Single task execution ──────────────────────────────────────────────

    def execute_task(self, ctx: ExecutionContext) -> TaskExecutionResult:
        """Execute a single task."""
        if not self._loaded:
            raise RuntimeError("ExecutionRuntime must be loaded")

        self._active[ctx.task_id] = True
        self._emit("ExecutionStarted", {
            "task_id": ctx.task_id, "action": ctx.action,
        })

        result = self._executor.execute(ctx)

        self._active.pop(ctx.task_id, None)
        self._history.add_record(result)
        self._execution_count += 1

        return result

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id not in self._active:
            return False
        self._executor.cancel(task_id)
        self._emit("ExecutionCancelled", {"task_id": task_id})
        return True

    # ── Batch execution ────────────────────────────────────────────────────

    def execute_batch(
        self,
        contexts: List[ExecutionContext],
        mode: ExecutionMode = ExecutionMode.DEPENDENCY_AWARE,
    ) -> ExecutionPlanResult:
        """Execute a batch of tasks according to the execution mode."""
        if not self._loaded:
            raise RuntimeError("ExecutionRuntime must be loaded")

        start = time.time()

        self._emit("ExecutionBatchStarted", {
            "task_count": len(contexts), "mode": mode.value,
        })

        # Register all contexts
        self._scheduler.clear()
        for ctx in contexts:
            self._scheduler.register(ctx)

        # Validate
        errors = self._scheduler.validate_dependencies()
        if errors:
            self._emit("ExecutionBatchFailed", {"errors": errors})
            return ExecutionPlanResult(
                task_results=[
                    TaskExecutionResult(
                        task_id=ctx.task_id, action=ctx.action,
                        status=TaskStatus.FAILED, error=f"Dependency error: {errors}",
                    ) for ctx in contexts
                ],
                total_time_ms=round((time.time() - start) * 1000, 2),
                mode=mode.value,
            )

        # Get execution batches
        batches = self._scheduler.get_execution_order(mode)

        # Execute
        all_results: List[TaskExecutionResult] = []
        for batch in batches:
            batch_results: List[TaskExecutionResult] = []
            for task_id in batch:
                ctx = self._scheduler.get_context(task_id)
                if not ctx:
                    continue
                result = self._executor.execute(ctx)
                self._history.add_record(result)
                self._execution_count += 1
                batch_results.append(result)
                self._active.pop(task_id, None)
            all_results.extend(batch_results)

            # Stop on first failure in sequential mode
            if mode == ExecutionMode.SEQUENTIAL:
                if any(not r.success for r in batch_results):
                    break

        total_ms = round((time.time() - start) * 1000, 2)

        plan_result = ExecutionPlanResult(
            task_results=all_results,
            total_time_ms=total_ms,
            mode=mode.value,
        )

        status_event = "ExecutionBatchCompleted" if plan_result.success else "ExecutionBatchFailed"
        self._emit(status_event, {
            "task_count": len(all_results),
            "success": plan_result.success,
            "total_time_ms": total_ms,
        })

        return plan_result

    def execute_mission_tasks(
        self,
        mission_id: str,
        mode: ExecutionMode = ExecutionMode.DEPENDENCY_AWARE,
    ) -> ExecutionPlanResult:
        """Pull tasks from MissionRuntime and execute them."""
        if not self._mission:
            raise RuntimeError("No MissionRuntime configured")

        graph = self._mission.get_task_graph(mission_id)
        if not graph:
            return ExecutionPlanResult(
                metadata={"error": f"No task graph for mission {mission_id}"},
            )

        tasks = graph.get_all_tasks()
        contexts = []
        for task in tasks:
            if task.status not in ("pending", "ready"):
                continue
            ctx = ExecutionContext(
                task_id=task.id,
                action=task.action or task.name,
                parameters=task.parameters,
                dependencies=task.dependencies,
            )
            contexts.append(ctx)

        return self.execute_batch(contexts, mode)

    # ── History & stats ────────────────────────────────────────────────────

    def get_history(self) -> ExecutionHistory:
        return self._history

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "execution_count": self._execution_count,
            "active_tasks": len(self._active),
            "history": self._history.get_stats(),
        }

    def _health_check(self) -> Any:
        from prototype.diagnostics.diagnostics import HealthStatus
        return HealthStatus(
            component="execution",
            healthy=self._loaded,
            message="Execution runtime operational" if self._loaded else "Not loaded",
        )

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(Event(
            event_type=event_type, payload=payload, source="execution_runtime",
        ))
