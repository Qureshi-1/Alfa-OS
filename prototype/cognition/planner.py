"""Task Planner — decomposes perceived intents into executable task plans.

Stage 2 of the cognition pipeline. Takes a PerceptionResult and produces
a TaskPlan with ordered steps, dependencies, and resource requirements.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.cognition.planner")


@dataclass
class TaskStep:
    """A single step in a task plan."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    requires_tool: Optional[str] = None
    requires_agent: Optional[str] = None
    requires_worker: Optional[str] = None
    estimated_cost: float = 0.0
    priority: int = 0
    status: str = "pending"
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskPlan:
    """Ordered plan of steps to accomplish a goal."""
    id: str = field(default_factory=lambda: str(uuid4()))
    goal: str = ""
    steps: List[TaskStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    estimated_total_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"
    latency_ms: float = 0.0

    @property
    def pending_steps(self) -> List[TaskStep]:
        return [s for s in self.steps if s.status == "pending"]

    @property
    def completed_steps(self) -> List[TaskStep]:
        return [s for s in self.steps if s.status == "completed"]

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("completed", "skipped") for s in self.steps)

    @property
    def has_failures(self) -> bool:
        return any(s.status == "failed" for s in self.steps)

    def next_ready(self) -> Optional[TaskStep]:
        """Get the next step whose dependencies are all satisfied."""
        completed_ids = {s.id for s in self.steps if s.status in ("completed", "skipped")}
        for step in self.pending_steps:
            if all(dep in completed_ids for dep in step.dependencies):
                return step
        return None


class TaskPlannerPlugin:
    """Base class for planner stage plugins.

    Plugins can:
    - Override plan creation for specific intents
    - Add steps to a plan
    - Reorder or filter steps
    - Validate plans before execution
    """

    def should_handle(self, intents: List[Dict[str, Any]],
                      context: Dict[str, Any]) -> bool:
        """Return True if this plugin wants to handle planning for these intents."""
        return False

    def create_plan(self, goal: str, intents: List[Dict[str, Any]],
                    entities: Dict[str, List[str]],
                    context: Dict[str, Any]) -> Optional[TaskPlan]:
        """Create a custom plan. Return None to fall back to default."""
        return None

    def refine_plan(self, plan: TaskPlan,
                    context: Dict[str, Any]) -> TaskPlan:
        """Post-process a plan: add/remove/reorder steps."""
        return plan

    def validate_plan(self, plan: TaskPlan,
                      context: Dict[str, Any]) -> List[str]:
        """Validate a plan. Return list of issues (empty = valid)."""
        return []


class TaskPlanner:
    """Stage 2: decomposes intents into executable task plans.

    Supports plugin-based extension for custom planning strategies.
    Emits: PlanStarted, PlanCreated
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._plugins: List[TaskPlannerPlugin] = []
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("TaskPlanner loaded: %d plugins", len(self._plugins))

    def is_loaded(self) -> bool:
        return self._loaded

    def register_plugin(self, plugin: TaskPlannerPlugin) -> None:
        self._plugins.append(plugin)

    def unregister_plugin(self, plugin: TaskPlannerPlugin) -> bool:
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def create_plan(
        self,
        goal: str,
        intents: List[Dict[str, Any]],
        entities: Optional[Dict[str, List[str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskPlan:
        """Create a task plan from perceived intents and entities.

        Args:
            goal: The high-level goal description.
            intents: Detected intents from perception.
            entities: Extracted entities.
            context: Additional context.

        Returns:
            TaskPlan with ordered steps.
        """
        ctx = context or {}
        ents = entities or {}
        start = time.time()

        self._emit("PlanStarted", {"goal": goal, "intent_count": len(intents)})

        # Let plugins try to create a plan first
        plan = None
        for plugin in self._plugins:
            if plugin.should_handle(intents, ctx):
                plan = plugin.create_plan(goal, intents, ents, ctx)
                if plan:
                    break

        # Default planning if no plugin handled it
        if not plan:
            plan = self._default_plan(goal, intents, ents, ctx)

        # Let plugins refine the plan
        for plugin in self._plugins:
            plan = plugin.refine_plan(plan, ctx)

        plan.context = ctx
        plan.estimated_total_cost = sum(s.estimated_cost for s in plan.steps)
        plan.latency_ms = round((time.time() - start) * 1000, 2)
        plan.status = "ready"

        self._emit("PlanCreated", {
            "plan_id": plan.id,
            "step_count": len(plan.steps),
            "estimated_cost": plan.estimated_total_cost,
            "latency_ms": plan.latency_ms,
        })

        return plan

    def _default_plan(
        self, goal: str, intents: List[Dict[str, Any]],
        entities: Dict[str, List[str]], context: Dict[str, Any],
    ) -> TaskPlan:
        """Create a default plan based on detected intents."""
        steps = []
        primary_intent = intents[0]["name"] if intents else "query"

        if primary_intent == "query":
            steps.append(TaskStep(
                name="search_memory", action="memory_recall",
                description=f"Search memory for: {goal}",
                parameters={"query": goal},
            ))
            steps.append(TaskStep(
                name="reason", action="reason",
                description=f"Reason about: {goal}",
                parameters={"goal": goal},
                dependencies=[steps[0].id] if steps else [],
            ))
            steps.append(TaskStep(
                name="respond", action="respond",
                description="Generate response",
                parameters={"goal": goal},
                dependencies=[steps[-1].id] if steps else [],
            ))

        elif primary_intent == "command":
            steps.append(TaskStep(
                name="parse_command", action="parse",
                description=f"Parse command: {goal}",
                parameters={"goal": goal},
            ))
            steps.append(TaskStep(
                name="select_tool", action="tool_select",
                description="Select appropriate tool",
                parameters={"goal": goal},
                dependencies=[steps[0].id] if steps else [],
            ))
            steps.append(TaskStep(
                name="execute", action="execute",
                description="Execute the command",
                parameters={"goal": goal},
                dependencies=[steps[-1].id] if steps else [],
            ))
            steps.append(TaskStep(
                name="verify", action="verify",
                description="Verify execution result",
                dependencies=[steps[-1].id] if steps else [],
            ))

        elif primary_intent == "analysis":
            steps.append(TaskStep(
                name="gather_data", action="gather",
                description=f"Gather data for analysis: {goal}",
                parameters={"goal": goal},
            ))
            steps.append(TaskStep(
                name="analyze", action="analyze",
                description="Perform analysis",
                dependencies=[steps[0].id] if steps else [],
            ))
            steps.append(TaskStep(
                name="report", action="respond",
                description="Report findings",
                dependencies=[steps[-1].id] if steps else [],
            ))

        elif primary_intent == "generation":
            steps.append(TaskStep(
                name="understand Requirements", action="parse",
                description=f"Understand requirements: {goal}",
                parameters={"goal": goal},
            ))
            steps.append(TaskStep(
                name="generate", action="generate",
                description="Generate content",
                dependencies=[steps[0].id] if steps else [],
            ))
            steps.append(TaskStep(
                name="review", action="verify",
                description="Review generated output",
                dependencies=[steps[-1].id] if steps else [],
            ))

        else:
            # Generic fallback
            steps.append(TaskStep(
                name="process", action="reason",
                description=f"Process: {goal}",
                parameters={"goal": goal},
            ))
            steps.append(TaskStep(
                name="respond", action="respond",
                description="Generate response",
                dependencies=[steps[0].id] if steps else [],
            ))

        return TaskPlan(goal=goal, steps=steps)

    def replan(self, plan: TaskPlan, failed_step: TaskStep,
               reason: str) -> TaskPlan:
        """Create a revised plan after a step failure.

        Skips steps that depend on the failed step.
        """
        failed_id = failed_step.id
        for step in plan.steps:
            if failed_id in step.dependencies:
                step.status = "skipped"
                step.metadata["skip_reason"] = f"Dependency {failed_id} failed: {reason}"
        plan.status = "replanned"
        return plan

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="planner",
            ))
