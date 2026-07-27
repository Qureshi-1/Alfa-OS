"""Cognition Executor — dispatches plan steps to tools, workers, and agents.

Stage 4 of the cognition pipeline. Takes a TaskPlan + ReasoningResult and
executes each step, collecting results and handling failures.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus, EngineResult
from prototype.cognition.planner import TaskPlan, TaskStep
from prototype.cognition.reasoner import ReasoningResult, ToolCandidate

logger = logging.getLogger("alfa.cognition.executor")


@dataclass
class StepResult:
    """Result of executing a single step."""
    step_id: str = ""
    step_name: str = ""
    success: bool = False
    output: Any = None
    error: Optional[str] = None
    tool_used: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Aggregated result of executing a full plan."""
    id: str = field(default_factory=lambda: str(uuid4()))
    plan_id: str = ""
    success: bool = False
    step_results: List[StepResult] = field(default_factory=list)
    output: Any = None
    error: Optional[str] = None
    total_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def failed_steps(self) -> List[StepResult]:
        return [r for r in self.step_results if not r.success]

    @property
    def succeeded_steps(self) -> List[StepResult]:
        return [r for r in self.step_results if r.success]


class ExecutorPlugin:
    """Base class for executor stage plugins.

    Plugins can:
    - Override step execution (custom tool dispatch)
    - Pre/post-process individual steps
    - Handle failures with retry/fallback logic
    - Short-circuit execution
    """

    def pre_execute(self, step: TaskStep, context: Dict[str, Any]) -> Optional[StepResult]:
        """Called before step execution. Return a StepResult to short-circuit."""
        return None

    def execute_step(self, step: TaskStep, candidate: Optional[ToolCandidate],
                     context: Dict[str, Any]) -> Optional[StepResult]:
        """Override step execution. Return None to use default."""
        return None

    def post_execute(self, step: TaskStep, result: StepResult,
                     context: Dict[str, Any]) -> StepResult:
        """Post-process a step result."""
        return result

    def on_failure(self, step: TaskStep, error: str,
                   context: Dict[str, Any]) -> Optional[StepResult]:
        """Handle a step failure. Return a StepResult for recovery, None to propagate."""
        return None


class CognitionExecutor:
    """Stage 4: executes plan steps using selected tools/agents/workers.

    Supports plugin-based extension for custom execution logic.
    Emits: ExecutionStarted, StepStarted, StepCompleted, StepFailed, ExecutionCompleted
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._plugins: List[ExecutorPlugin] = []
        self._tool_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._agent_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._worker_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("CognitionExecutor loaded: %d plugins", len(self._plugins))

    def is_loaded(self) -> bool:
        return self._loaded

    def register_plugin(self, plugin: ExecutorPlugin) -> None:
        self._plugins.append(plugin)

    def unregister_plugin(self, plugin: ExecutorPlugin) -> bool:
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def register_tool_handler(self, name: str,
                              handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a handler function for a tool."""
        self._tool_handlers[name] = handler

    def register_agent_handler(self, name: str,
                               handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a handler function for an agent."""
        self._agent_handlers[name] = handler

    def register_worker_handler(self, name: str,
                                handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a handler function for a worker."""
        self._worker_handlers[name] = handler

    def execute(
        self,
        plan: TaskPlan,
        reasoning: ReasoningResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """Execute a full plan using the reasoning results.

        Args:
            plan: The task plan to execute.
            reasoning: Tool selections from the reasoner.
            context: Additional context.

        Returns:
            ExecutionResult with all step results.
        """
        ctx = context or {}
        start = time.time()

        self._emit("ExecutionStarted", {
            "plan_id": plan.id,
            "step_count": len(plan.steps),
            "strategy": reasoning.strategy,
        })

        step_results: List[StepResult] = []

        if reasoning.strategy == "parallel":
            step_results = self._execute_parallel(plan, reasoning, ctx)
        else:
            step_results = self._execute_sequential(plan, reasoning, ctx)

        total_ms = round((time.time() - start) * 1000, 2)
        all_success = all(r.success for r in step_results)

        # Combine outputs
        outputs = [r.output for r in step_results if r.output is not None]
        combined_output = outputs[-1] if outputs else None

        result = ExecutionResult(
            plan_id=plan.id,
            success=all_success,
            step_results=step_results,
            output=combined_output,
            total_time_ms=total_ms,
        )

        if not all_success:
            failed = [r.step_name for r in step_results if not r.success]
            result.error = f"Failed steps: {', '.join(failed)}"

        self._emit("ExecutionCompleted", {
            "plan_id": plan.id,
            "success": all_success,
            "steps_completed": len([r for r in step_results if r.success]),
            "steps_failed": len([r for r in step_results if not r.success]),
            "total_time_ms": total_ms,
        })

        return result

    def _execute_sequential(self, plan: TaskPlan, reasoning: ReasoningResult,
                            context: Dict[str, Any]) -> List[StepResult]:
        """Execute steps one at a time, respecting dependencies."""
        results = []
        completed_ids = set()

        for step in plan.steps:
            # Check dependencies
            if step.dependencies:
                unmet = [d for d in step.dependencies if d not in completed_ids]
                if unmet:
                    results.append(StepResult(
                        step_id=step.id, step_name=step.name,
                        success=False, error=f"Unmet dependencies: {unmet}",
                    ))
                    continue

            result = self._execute_step(step, reasoning, context)
            results.append(result)

            if result.success:
                completed_ids.add(step.id)
                step.status = "completed"
            else:
                step.status = "failed"

        return results

    def _execute_parallel(self, plan: TaskPlan, reasoning: ReasoningResult,
                          context: Dict[str, Any]) -> List[StepResult]:
        """Execute independent steps concurrently (simulated sequential for safety)."""
        # In a real async runtime this would use asyncio.gather or threads
        # For now, execute in dependency order but mark independent steps
        return self._execute_sequential(plan, reasoning, context)

    def _execute_step(self, step: TaskStep, reasoning: ReasoningResult,
                      context: Dict[str, Any]) -> StepResult:
        """Execute a single step."""
        start = time.time()

        self._emit("StepStarted", {"step_id": step.id, "step_name": step.name})

        candidate = reasoning.selections.get(step.id)

        # Plugin pre-execute (can short-circuit)
        for plugin in self._plugins:
            pre_result = plugin.pre_execute(step, context)
            if pre_result:
                self._emit("StepCompleted", {
                    "step_id": step.id, "success": pre_result.success,
                    "tool_used": "plugin_override",
                })
                return pre_result

        # Plugin execute (can override)
        for plugin in self._plugins:
            plugin_result = plugin.execute_step(step, candidate, context)
            if plugin_result:
                plugin_result.execution_time_ms = round((time.time() - start) * 1000, 2)
                # Plugin post-execute
                for p in self._plugins:
                    plugin_result = p.post_execute(step, plugin_result, context)
                self._emit("StepCompleted", {
                    "step_id": step.id, "success": plugin_result.success,
                    "tool_used": plugin_result.tool_used,
                })
                return plugin_result

        # Default execution
        result = self._default_execute_step(step, candidate, context)

        # Plugin post-execute
        for plugin in self._plugins:
            result = plugin.post_execute(step, result, context)

        result.execution_time_ms = round((time.time() - start) * 1000, 2)

        if not result.success:
            # Plugin failure handling
            for plugin in self._plugins:
                recovery = plugin.on_failure(step, result.error or "", context)
                if recovery:
                    result = recovery
                    break

            self._emit("StepFailed", {
                "step_id": step.id, "error": result.error,
            })

        self._emit("StepCompleted", {
            "step_id": step.id, "success": result.success,
            "tool_used": result.tool_used,
        })

        return result

    def _default_execute_step(self, step: TaskStep,
                              candidate: Optional[ToolCandidate],
                              context: Dict[str, Any]) -> StepResult:
        """Default step execution: dispatch to registered handlers."""
        if not candidate:
            return StepResult(
                step_id=step.id, step_name=step.name,
                success=False, error="No tool/agent/worker selected",
            )

        # Find handler
        handler = None
        if candidate.type == "tool":
            handler = self._tool_handlers.get(candidate.name)
        elif candidate.type == "agent":
            handler = self._agent_handlers.get(candidate.name)
        elif candidate.type == "worker":
            handler = self._worker_handlers.get(candidate.name)

        if not handler:
            # No handler registered — return a placeholder result
            return StepResult(
                step_id=step.id, step_name=step.name,
                success=True, output={"action": step.action, "parameters": step.parameters},
                tool_used=candidate.name,
                metadata={"note": "No handler registered; returned parameters as output"},
            )

        try:
            output = handler({**step.parameters, **context})
            return StepResult(
                step_id=step.id, step_name=step.name,
                success=True, output=output, tool_used=candidate.name,
            )
        except Exception as exc:
            return StepResult(
                step_id=step.id, step_name=step.name,
                success=False, error=str(exc), tool_used=candidate.name,
            )

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="executor",
            ))
