"""TaskExecutor — executes individual tasks with retry, rollback, timeout, and cancellation."""

import logging
import time
from typing import Any, Callable, Dict, Optional, Set

from prototype.common import Event, EventBus
from prototype.execution.execution_context import ExecutionContext
from prototype.execution.execution_result import TaskExecutionResult, TaskStatus
from prototype.execution.tool_router import ToolRouter

logger = logging.getLogger("alfa.execution.task_executor")


class TaskExecutor:
    """Executes a single task with retry, rollback, timeout, and cancellation support."""

    def __init__(
        self,
        tool_router: ToolRouter,
        event_bus: Optional[EventBus] = None,
        diagnostics: Any = None,
    ) -> None:
        self._router = tool_router
        self._event_bus = event_bus
        self._diagnostics = diagnostics
        self._cancelled: Set[str] = set()
        self._rollback_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_rollback(self, action: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._rollback_handlers[action] = handler

    def cancel(self, task_id: str) -> None:
        self._cancelled.add(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        return task_id in self._cancelled

    def clear_cancel(self, task_id: str) -> None:
        self._cancelled.discard(task_id)

    def execute(self, ctx: ExecutionContext) -> TaskExecutionResult:
        """Execute a task with retry and rollback support."""
        self._emit("StepStarted", {
            "task_id": ctx.task_id, "action": ctx.action,
        })

        result = self._execute_with_retry(ctx)

        status_event = "StepCompleted" if result.success else "StepFailed"
        self._emit(status_event, {
            "task_id": ctx.task_id, "action": ctx.action,
            "success": result.success, "retry_count": result.retry_count,
        })

        if self._diagnostics:
            self._diagnostics.increment(f"execution.{ctx.handler_type or 'task'}.count")
            if result.success:
                self._diagnostics.increment(f"execution.{ctx.handler_type or 'task'}.success")
            else:
                self._diagnostics.increment(f"execution.{ctx.handler_type or 'task'}.failure")
            self._diagnostics.record("execution.task_time_ms", result.execution_time_ms)

        return result

    def _execute_with_retry(self, ctx: ExecutionContext) -> TaskExecutionResult:
        max_retries = ctx.retry.max_retries
        backoff = ctx.retry.backoff_seconds
        last_error = None

        for attempt in range(max_retries + 1):
            if self.is_cancelled(ctx.task_id):
                return TaskExecutionResult(
                    task_id=ctx.task_id, action=ctx.action,
                    status=TaskStatus.CANCELLED, retry_count=attempt,
                )

            start = time.time()
            try:
                output = self._dispatch(ctx)
                elapsed_ms = round((time.time() - start) * 1000, 2)

                return TaskExecutionResult(
                    task_id=ctx.task_id, action=ctx.action,
                    status=TaskStatus.COMPLETED, output=output,
                    handler_used=ctx.handler_name,
                    handler_type=ctx.handler_type,
                    execution_time_ms=elapsed_ms,
                    retry_count=attempt,
                    metadata={"completed_at": time.time()},
                )

            except Exception as exc:
                elapsed_ms = round((time.time() - start) * 1000, 2)
                last_error = str(exc)

                if attempt < max_retries:
                    if self._should_retry(ctx, exc):
                        logger.info(
                            "Task %s retry %d/%d after %.1fs: %s",
                            ctx.task_id[:8], attempt + 1, max_retries, backoff, exc,
                        )
                        self._emit("ExecutionRetrying", {
                            "task_id": ctx.task_id, "attempt": attempt + 1,
                            "error": str(exc),
                        })
                        time.sleep(backoff)  # ponytail: synchronous backoff
                    else:
                        return TaskExecutionResult(
                            task_id=ctx.task_id, action=ctx.action,
                            status=TaskStatus.FAILED, error=last_error,
                            handler_used=ctx.handler_name,
                            handler_type=ctx.handler_type,
                            execution_time_ms=elapsed_ms,
                            retry_count=attempt,
                            rollback_success=self._try_rollback(ctx),
                            metadata={"completed_at": time.time()},
                        )
                else:
                    logger.warning("Task %s failed after %d attempts: %s",
                                   ctx.task_id[:8], max_retries + 1, exc)

        # All retries exhausted — try rollback
        rolled_back = self._try_rollback(ctx)

        return TaskExecutionResult(
            task_id=ctx.task_id, action=ctx.action,
            status=TaskStatus.FAILED, error=last_error,
            handler_used=ctx.handler_name,
            handler_type=ctx.handler_type,
            execution_time_ms=0.0,
            retry_count=max_retries,
            rollback_success=rolled_back,
            metadata={"completed_at": time.time()},
        )

    def _dispatch(self, ctx: ExecutionContext) -> Any:
        """Dispatch to the tool router."""
        handler_type = ctx.handler_type or "tool"
        name = ctx.handler_name or ctx.action
        return self._router.route(handler_type, name, ctx.parameters)

    def _should_retry(self, ctx: ExecutionContext, exc: Exception) -> bool:
        if not ctx.retry.retry_on:
            return True
        error_str = str(exc).lower()
        return any(pattern.lower() in error_str for pattern in ctx.retry.retry_on)

    def _try_rollback(self, ctx: ExecutionContext) -> Optional[bool]:
        if not ctx.rollback.enabled:
            return None
        handler = self._rollback_handlers.get(ctx.action)
        if not handler and ctx.rollback.handler_name:
            handler = self._rollback_handlers.get(ctx.rollback.handler_name)
        if not handler:
            return False
        try:
            handler({**ctx.parameters, **ctx.rollback.parameters})
            self._emit("ExecutionRolledBack", {"task_id": ctx.task_id, "action": ctx.action})
            return True
        except Exception as exc:
            logger.warning("Rollback failed for %s: %s", ctx.task_id[:8], exc)
            return False

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="task_executor",
            ))
