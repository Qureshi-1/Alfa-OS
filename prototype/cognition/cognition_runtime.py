"""Cognition Runtime — central orchestrator for the ALFA COS cognition pipeline.

Wires together: Perception → Intent → Planning → Reasoning → Execution → Reflection → Memory → Response

This is the composition root for the cognition engine. It owns the lifecycle
of all cognition stages and provides the top-level API for processing input.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from prototype.common import Event, EventBus, EngineResult
from prototype.cognition.perception import PerceptionEngine, PerceptionResult, PerceptionPlugin
from prototype.cognition.planner import TaskPlanner, TaskPlan, TaskPlannerPlugin
from prototype.cognition.reasoner import Reasoner, ReasoningResult, ReasonerPlugin
from prototype.cognition.executor import CognitionExecutor, ExecutionResult, ExecutorPlugin
from prototype.cognition.reflector import CognitionReflector, ReflectionOutput, ReflectorPlugin

logger = logging.getLogger("alfa.cognition.runtime")


class CognitionRuntime:
    """Central brain of ALFA COS.

    Orchestrates the full cognition pipeline:
    Input → Perception → Intent → Planning → Reasoning → Tool Selection → Execution → Reflection → Memory → Response

    Integrates with:
    - EventBus (all stage events)
    - Memory (recall + store)
    - Worker system (background tasks)
    - Agent system (autonomous reasoning)
    - ModelHub (AI inference)
    - Diagnostics (metrics + health)
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        memory_manager: Any = None,
        tool_manager: Any = None,
        agent_runtime: Any = None,
        worker_manager: Any = None,
        diagnostics: Any = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._memory = memory_manager
        self._tools = tool_manager
        self._agents = agent_runtime
        self._workers = worker_manager
        self._diagnostics = diagnostics

        # Create stages
        self.perception = PerceptionEngine(event_bus=self._event_bus)
        self.planner = TaskPlanner(event_bus=self._event_bus)
        self.reasoner = Reasoner(event_bus=self._event_bus)
        self.executor = CognitionExecutor(event_bus=self._event_bus)
        self.reflector = CognitionReflector(event_bus=self._event_bus)

        self._loaded = False
        self._process_count = 0

    def load(self) -> None:
        """Initialize all cognition stages."""
        if self._loaded:
            return

        self.perception.load()
        self.planner.load()
        self.reasoner.load()
        self.executor.load()
        self.reflector.load()

        # Register health checks
        if self._diagnostics:
            self._diagnostics.register_health_check(
                "cognition", self._health_check,
            )

        self._loaded = True

        self._event_bus.publish(Event(
            event_type="CognitionStarted",
            payload={"stages": 5},
            source="cognition_runtime",
        ))

        logger.info("CognitionRuntime loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def shutdown(self) -> None:
        """Shutdown the cognition runtime."""
        if not self._loaded:
            return

        self._event_bus.publish(Event(
            event_type="CognitionShutdown",
            payload={"process_count": self._process_count},
            source="cognition_runtime",
        ))

        self._loaded = False
        logger.info("CognitionRuntime shutdown")

    # ── Plugin registration (delegates to stages) ─────────────────────────

    def register_perception_plugin(self, plugin: PerceptionPlugin) -> None:
        self.perception.register_plugin(plugin)

    def register_planner_plugin(self, plugin: TaskPlannerPlugin) -> None:
        self.planner.register_plugin(plugin)

    def register_reasoner_plugin(self, plugin: ReasonerPlugin) -> None:
        self.reasoner.register_plugin(plugin)

    def register_executor_plugin(self, plugin: ExecutorPlugin) -> None:
        self.executor.register_plugin(plugin)

    def register_reflector_plugin(self, plugin: ReflectorPlugin) -> None:
        self.reflector.register_plugin(plugin)

    # ── Registry population ────────────────────────────────────────────────

    def register_tool(self, name: str, capabilities: List[str],
                      handler: Optional[Callable] = None) -> None:
        """Register a tool for the reasoner and optionally a handler for the executor."""
        self.reasoner.register_tool(name, capabilities)
        if handler:
            self.executor.register_tool_handler(name, handler)

    def register_agent(self, name: str, capabilities: List[str],
                       handler: Optional[Callable] = None) -> None:
        """Register an agent for the reasoner and optionally a handler for the executor."""
        self.reasoner.register_agent(name, capabilities)
        if handler:
            self.executor.register_agent_handler(name, handler)

    def register_worker(self, name: str, capabilities: List[str],
                        handler: Optional[Callable] = None) -> None:
        """Register a worker for the reasoner and optionally a handler for the executor."""
        self.reasoner.register_worker(name, capabilities)
        if handler:
            self.executor.register_worker_handler(name, handler)

    # ── Core pipeline ──────────────────────────────────────────────────────

    def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EngineResult:
        """Process user input through the full cognition pipeline.

        Pipeline:
        1. Perception — parse input, detect intent
        2. Planning — decompose into task steps
        3. Reasoning — select tools/agents
        4. Execution — run plan steps
        5. Reflection — evaluate quality, learn

        Args:
            user_input: Raw user input string.
            context: Optional context dict.

        Returns:
            EngineResult with the final output.
        """
        if not self._loaded:
            raise RuntimeError("CognitionRuntime must be loaded before processing")

        ctx = context or {}
        start = time.time()
        self._process_count += 1

        self._emit("CognitionProcessing", {
            "input_length": len(user_input),
            "process_count": self._process_count,
        })

        try:
            # 1. Perception
            perception = self.perception.process(user_input, ctx)

            # Recall relevant memory
            memory_context = self._recall_memory(user_input)

            # Merge context
            full_ctx = {
                **ctx,
                "perception": perception,
                "memory_context": memory_context,
            }

            # 2. Planning
            plan = self.planner.create_plan(
                goal=user_input,
                intents=perception.intents,
                entities=perception.entities,
                context=full_ctx,
            )

            # 3. Reasoning
            reasoning = self.reasoner.reason(plan, full_ctx)

            # 4. Execution
            execution = self.executor.execute(plan, reasoning, full_ctx)

            # 5. Reflection
            reflection = self.reflector.reflect(execution, plan, full_ctx)

            # 6. Memory updates
            self._apply_memory_updates(reflection)

            # Record diagnostics
            latency_ms = (time.time() - start) * 1000
            if self._diagnostics:
                self._diagnostics.record("cognition.latency_ms", latency_ms)
                self._diagnostics.increment("cognition.process_count")
                if execution.success:
                    self._diagnostics.increment("cognition.success_count")
                else:
                    self._diagnostics.increment("cognition.failure_count")

            self._emit("CognitionCompleted", {
                "success": execution.success,
                "overall_score": reflection.overall_score,
                "latency_ms": round(latency_ms, 2),
                "process_count": self._process_count,
            })

            return EngineResult(
                content=str(execution.output) if execution.output else "",
                success=execution.success,
                error=execution.error,
                metadata={
                    "perception_id": perception.id,
                    "plan_id": plan.id,
                    "execution_id": execution.id,
                    "reflection_score": reflection.overall_score,
                    "latency_ms": round(latency_ms, 2),
                },
            )

        except Exception as exc:
            latency_ms = (time.time() - start) * 1000
            self._emit("CognitionFailed", {
                "error": str(exc),
                "latency_ms": round(latency_ms, 2),
            })
            logger.exception("Cognition pipeline failed")
            return EngineResult(
                content="",
                success=False,
                error=str(exc),
                metadata={"latency_ms": round(latency_ms, 2)},
            )

    async def process_async(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EngineResult:
        """Async wrapper around process(). For use in async runtimes."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process, user_input, context)

    # ── Memory integration ─────────────────────────────────────────────────

    def _recall_memory(self, query: str) -> List[Any]:
        """Recall relevant memories for context enrichment."""
        if not self._memory:
            return []
        try:
            if hasattr(self._memory, "recall"):
                return self._memory.recall(query, limit=5)
        except Exception as exc:
            logger.debug("Memory recall failed: %s", exc)
        return []

    def _apply_memory_updates(self, reflection: ReflectionOutput) -> None:
        """Apply memory updates suggested by reflection."""
        if not self._memory:
            return
        for update in reflection.memory_updates:
            try:
                if hasattr(self._memory, "remember"):
                    self._memory.remember(
                        content=update.content,
                        tags=update.tags,
                        importance=update.importance,
                    )
            except Exception as exc:
                logger.debug("Memory update failed: %s", exc)

    # ── Health & stats ─────────────────────────────────────────────────────

    def _health_check(self) -> Any:
        """Cognition health check."""
        from prototype.diagnostics.diagnostics import HealthStatus
        return HealthStatus(
            component="cognition",
            healthy=self._loaded,
            message="Cognition runtime operational" if self._loaded else "Not loaded",
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cognition runtime statistics."""
        return {
            "loaded": self._loaded,
            "process_count": self._process_count,
            "perception": {"loaded": self.perception.is_loaded()},
            "planner": {"loaded": self.planner.is_loaded()},
            "reasoner": {"loaded": self.reasoner.is_loaded()},
            "executor": {"loaded": self.executor.is_loaded()},
            "reflector": {
                "loaded": self.reflector.is_loaded(),
                **self.reflector.get_stats(),
            },
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(Event(
            event_type=event_type, payload=payload, source="cognition_runtime",
        ))
