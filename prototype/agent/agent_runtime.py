"""Agent Runtime — runtime coordinator that wires agents, planner, reflector, and tool execution."""

import logging
import time
from typing import Any, Dict, List, Optional

from prototype.agent.agent_registry import AgentRegistry
from prototype.agent.base_agent import (
    AgentContext, AgentMessage, AgentResult, AgentStatus,
    BaseAgent, Plan, ReflectionRecord,
)
from prototype.agent.multi_agent import MultiAgentCoordinator
from prototype.agent.planner import AgentPlanner
from prototype.agent.reflector import AgentReflector
from prototype.agent.tool_executor import ToolExecutor
from prototype.common import Event, EventBus
from prototype.tools.tool_manager import ToolManager

logger = logging.getLogger("alfa.agent.runtime")


class AgentRuntime:
    """Runtime that coordinates all agent subsystems.

    Provides the high-level API for:
    - Running a single agent
    - Multi-agent collaboration
    - Planning and plan execution
    - Reflection and learning
    """

    def __init__(self, tool_manager: ToolManager,
                 event_bus: Optional[EventBus] = None) -> None:
        self.registry = AgentRegistry()
        self.tool_executor = ToolExecutor(tool_manager)
        self.planner = AgentPlanner()
        self.reflector = AgentReflector()
        self.multi_agent = MultiAgentCoordinator(
            self.registry, self.tool_executor, event_bus,
        )
        self._event_bus = event_bus
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        logger.info("AgentRuntime loaded: %d agents", self.registry.count())

    def is_loaded(self) -> bool:
        return self._loaded

    def register_agent(self, agent: BaseAgent) -> bool:
        return self.registry.register(agent)

    def run_agent(self, agent_id: str, goal: str,
                  parameters: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Run a single agent on a goal.

        Args:
            agent_id: ID of the agent to run.
            goal: The goal description.
            parameters: Additional parameters.

        Returns:
            AgentResult from the agent.
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return AgentResult(
                agent_id=agent_id, task_id="",
                status=AgentStatus.FAILED,
                error=f"Agent '{agent_id}' not found",
            )

        if not self.registry.is_enabled(agent_id):
            return AgentResult(
                agent_id=agent_id, task_id="",
                status=AgentStatus.FAILED,
                error=f"Agent '{agent_id}' is disabled",
            )

        available_tools = [t["name"] for t in self.tool_executor.list_available()]
        context = AgentContext(
            goal=goal,
            available_tools=available_tools,
            parameters=parameters or {},
        )

        self._publish_event("AgentStarted", {"agent_id": agent_id, "goal": goal})

        agent.on_task_start(context)
        start = time.time()
        result = agent.run(context)
        result.execution_time_ms = round((time.time() - start) * 1000, 2)
        agent.on_task_complete(result)

        self._publish_event("AgentCompleted", {
            "agent_id": agent_id,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
        })

        return result

    def run_multi(self, agent_ids: List[str], goal: str,
                  pattern: str = "sequential",
                  parameters: Optional[Dict[str, Any]] = None) -> Dict[str, AgentResult]:
        """Run multiple agents with a collaboration pattern."""
        context = AgentContext(
            goal=goal,
            available_tools=[t["name"] for t in self.tool_executor.list_available()],
            parameters=parameters or {},
        )
        return self.multi_agent.run(agent_ids, context, pattern)

    def plan(self, goal: str, available_tools: Optional[List[str]] = None,
             context: Optional[Dict[str, Any]] = None) -> Plan:
        """Create a plan for a goal."""
        tools = available_tools or [t["name"] for t in self.tool_executor.list_available()]
        return self.planner.plan(goal, tools, context)

    def execute_plan(self, plan: Plan, agent_id: str) -> Plan:
        """Execute a plan using a specific agent.

        Returns the plan with updated step statuses.
        """
        for step in plan.steps:
            if step.status != "pending":
                continue

            step.status = "running"
            if step.tool_name:
                result = self.tool_executor.execute_plan_step(
                    step.tool_name, step.arguments, agent_id,
                )
                step.status = "completed" if result.success else "failed"
                step.result = AgentResult(
                    agent_id=agent_id,
                    task_id=plan.plan_id,
                    status=AgentStatus.COMPLETED if result.success else AgentStatus.FAILED,
                    output=result.result,
                    error=result.error,
                )
            else:
                # Agent-reasoned step — run the agent
                agent_result = self.run_agent(agent_id, step.description, step.arguments)
                step.status = "completed" if agent_result.success else "failed"
                step.result = agent_result

        return plan

    def reflect(self, result: AgentResult,
                plan: Optional[Plan] = None) -> ReflectionRecord:
        """Reflect on an agent's execution."""
        return self.reflector.reflect(result, plan)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agents": self.registry.list_agents(),
            "agent_count": self.registry.count(),
            "reflection": self.reflector.get_stats(),
            "multi_agent": self.multi_agent.get_stats(),
        }

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="agent_runtime",
            ))

    def shutdown(self) -> None:
        self.registry.clear()
        self.reflector.clear()
        self._loaded = False
        logger.info("AgentRuntime shutdown")
