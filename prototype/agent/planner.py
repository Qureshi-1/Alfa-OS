"""Agent Planner — goal decomposition into executable plan steps."""

import logging
from typing import Any, Dict, List, Optional

from prototype.agent.base_agent import Plan, PlanStep

logger = logging.getLogger("alfa.agent.planner")


class AgentPlanner:
    """Decomposes goals into ordered plan steps.

    The planner uses a rule-based approach to break down goals
    into steps that agents can execute with available tools.
    """

    def __init__(self) -> None:
        self._strategies: Dict[str, callable] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._strategies["tool_chain"] = self._plan_tool_chain
        self._strategies["single_step"] = self._plan_single_step

    def plan(self, goal: str, available_tools: List[str],
             context: Optional[Dict[str, Any]] = None) -> Plan:
        """Create a plan for achieving a goal.

        Args:
            goal: The goal description.
            available_tools: Tools the executing agent has access to.
            context: Optional additional context.

        Returns:
            A Plan with ordered steps.
        """
        ctx = context or {}
        strategy = ctx.get("strategy", "auto")
        plan = Plan(goal=goal, metadata=ctx)

        if strategy == "auto":
            plan = self._plan_auto(goal, available_tools, ctx)
        elif strategy in self._strategies:
            plan = self._strategies[strategy](goal, available_tools, ctx)
        else:
            plan = self._plan_single_step(goal, available_tools, ctx)

        logger.info("Plan created: %d steps for goal '%s'", len(plan.steps), goal[:50])
        return plan

    def _plan_auto(self, goal: str, tools: List[str],
                   context: Dict[str, Any]) -> Plan:
        """Auto-select strategy based on goal complexity."""
        # Custom steps provided — use them directly
        if context.get("steps"):
            return self._plan_tool_chain(goal, tools, context)

        goal_lower = goal.lower()

        # Multi-step patterns
        if any(kw in goal_lower for kw in [" and then ", " after that ", " step ", " first "]):
            return self._plan_tool_chain(goal, tools, context)

        return self._plan_single_step(goal, tools, context)

    def _plan_single_step(self, goal: str, tools: List[str],
                          context: Dict[str, Any]) -> Plan:
        """Plan with a single step — the agent reasons and acts."""
        plan = Plan(goal=goal, metadata=context)
        plan.steps.append(PlanStep(
            description=f"Execute: {goal}",
            tool_name=None,  # Agent decides the tool
            arguments={"goal": goal, "tools": tools},
        ))
        return plan

    def _plan_tool_chain(self, goal: str, tools: List[str],
                         context: Dict[str, Any]) -> Plan:
        """Plan as a chain of tool calls."""
        plan = Plan(goal=goal, metadata=context)
        steps_data = context.get("steps", [])

        if steps_data:
            for i, step in enumerate(steps_data):
                plan.steps.append(PlanStep(
                    description=step.get("description", f"Step {i+1}"),
                    tool_name=step.get("tool"),
                    arguments=step.get("arguments", {}),
                    dependencies=step.get("dependencies", []),
                ))
        else:
            # Single fallback step
            plan.steps.append(PlanStep(
                description=f"Execute: {goal}",
                arguments={"goal": goal, "tools": tools},
            ))
        return plan

    def replan(self, original_plan: Plan, failed_step: PlanStep,
               error: str) -> Plan:
        """Create a new plan after a step failure.

        Skips the failed step's dependents and attempts recovery.
        """
        new_plan = Plan(
            goal=original_plan.goal,
            metadata={**original_plan.metadata, "replan": True, "original_plan_id": original_plan.plan_id},
        )

        failed_deps = {failed_step.step_id}
        for step in original_plan.steps:
            if step.step_id == failed_step.step_id:
                continue
            if any(d in failed_deps for d in step.dependencies):
                continue  # Skip dependents of failed step
            new_plan.steps.append(PlanStep(
                description=step.description,
                tool_name=step.tool_name,
                arguments=step.arguments,
                dependencies=step.dependencies,
            ))

        logger.info("Replan: %d steps (was %d)", len(new_plan.steps), len(original_plan.steps))
        return new_plan

    def register_strategy(self, name: str, strategy: callable) -> None:
        self._strategies[name] = strategy
