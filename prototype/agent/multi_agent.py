"""Multi-Agent Coordinator — orchestrates collaboration between multiple agents."""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from prototype.agent.base_agent import (
    AgentContext, AgentMessage, AgentResult, AgentStatus,
    BaseAgent, Plan, PlanStep,
)
from prototype.agent.agent_registry import AgentRegistry
from prototype.agent.tool_executor import ToolExecutor
from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.agent.multi")


class MultiAgentCoordinator:
    """Orchestrates multi-agent collaboration patterns.

    Supported patterns:
    - Sequential: agents run in order, each getting previous output
    - Parallel: agents run concurrently on the same input
    - Debate: agents argue and a judge decides
    - Pipeline: output of one agent feeds the next
    """

    def __init__(self, registry: AgentRegistry, tool_executor: ToolExecutor,
                 event_bus: Optional[EventBus] = None) -> None:
        self._registry = registry
        self._tool_executor = tool_executor
        self._event_bus = event_bus
        self._patterns: Dict[str, Callable] = {
            "sequential": self._run_sequential,
            "parallel": self._run_parallel,
            "debate": self._run_debate,
            "pipeline": self._run_pipeline,
            "advisor_orchestrator": self._run_advisor_orchestrator,
        }

    def run(self, agent_ids: List[str], context: AgentContext,
            pattern: str = "sequential") -> Dict[str, AgentResult]:
        """Run multiple agents using the specified collaboration pattern.

        Args:
            agent_ids: IDs of agents to coordinate.
            context: Shared execution context.
            pattern: Collaboration pattern name.

        Returns:
            Dict mapping agent_id to their result.
        """
        agents = []
        for aid in agent_ids:
            agent = self._registry.get_agent(aid)
            if agent and self._registry.is_enabled(aid):
                agents.append(agent)
            else:
                logger.warning("Agent '%s' not found or disabled — skipping", aid)

        if not agents:
            logger.error("No valid agents for coordination")
            return {}

        pattern_fn = self._patterns.get(pattern, self._run_sequential)

        self._publish_event("MultiAgentStarted", {
            "agent_ids": [a.agent_id for a in agents],
            "pattern": pattern,
            "task_id": context.task_id,
        })

        results = pattern_fn(agents, context)

        self._publish_event("MultiAgentCompleted", {
            "agent_ids": [a.agent_id for a in agents],
            "pattern": pattern,
            "task_id": context.task_id,
            "results": {aid: r.success for aid, r in results.items()},
        })

        return results

    def _run_sequential(self, agents: List[BaseAgent],
                        context: AgentContext) -> Dict[str, AgentResult]:
        """Run agents in sequence, each getting previous output."""
        results: Dict[str, AgentResult] = {}
        current_context = context

        for agent in agents:
            agent.on_task_start(current_context)
            start = time.time()
            result = agent.run(current_context)
            result.execution_time_ms = round((time.time() - start) * 1000, 2)
            agent.on_task_complete(result)
            results[agent.agent_id] = result

            # Feed output as next agent's input
            if result.output:
                msg = AgentMessage(
                    role="assistant",
                    content=str(result.output),
                    agent_id=agent.agent_id,
                )
                current_context = AgentContext(
                    task_id=current_context.task_id,
                    goal=current_context.goal,
                    messages=current_context.messages + [msg],
                    available_tools=current_context.available_tools,
                    parameters={**current_context.parameters, "previous_agent": agent.agent_id},
                )

        return results

    def _run_parallel(self, agents: List[BaseAgent],
                      context: AgentContext) -> Dict[str, AgentResult]:
        """Run agents concurrently on the same input."""
        import threading

        results: Dict[str, AgentResult] = {}
        lock = threading.Lock()

        def _run_one(agent: BaseAgent) -> None:
            agent.on_task_start(context)
            start = time.time()
            result = agent.run(context)
            result.execution_time_ms = round((time.time() - start) * 1000, 2)
            agent.on_task_complete(result)
            with lock:
                results[agent.agent_id] = result

        threads = [threading.Thread(target=_run_one, args=(a,)) for a in agents]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        return results

    def _run_debate(self, agents: List[BaseAgent],
                    context: AgentContext) -> Dict[str, AgentResult]:
        """Agents debate a topic, then a judge picks the best response."""
        if len(agents) < 2:
            return self._run_sequential(agents, context)

        # Each agent argues
        arguments: List[str] = []
        results: Dict[str, AgentResult] = {}
        for agent in agents:
            agent.on_task_start(context)
            start = time.time()
            result = agent.run(context)
            result.execution_time_ms = round((time.time() - start) * 1000, 2)
            agent.on_task_complete(result)
            results[agent.agent_id] = result
            if result.output:
                arguments.append(str(result.output))

        # Synthesize: last agent or first agent acts as judge
        if len(agents) >= 2:
            judge = agents[-1]
            debate_context = AgentContext(
                task_id=context.task_id,
                goal=f"Judge this debate on: {context.goal}",
                messages=[
                    AgentMessage(role=f"debater_{i}", content=arg)
                    for i, arg in enumerate(arguments)
                ],
                available_tools=context.available_tools,
                parameters={"role": "judge"},
            )
            judge.on_task_start(debate_context)
            start = time.time()
            judge_result = judge.run(debate_context)
            judge_result.execution_time_ms = round((time.time() - start) * 1000, 2)
            judge.on_task_complete(judge_result)
            results[judge.agent_id] = judge_result

        return results

    def _run_pipeline(self, agents: List[BaseAgent],
                      context: AgentContext) -> Dict[str, AgentResult]:
        """Pipeline: each agent transforms the output of the previous."""
        return self._run_sequential(agents, context)

    def _run_advisor_orchestrator(self, agents: List[BaseAgent],
                                  context: AgentContext) -> Dict[str, AgentResult]:
        """Advisor-Orchestrator-Worker three-tier pattern."""
        from prototype.agent.advisor_orchestrator import AdvisorOrchestratorCoordinator
        coord = AdvisorOrchestratorCoordinator(
            event_bus=self._event_bus,
            agent_registry=self._registry,
        )
        res_pipeline = coord.run_three_tier_pipeline(context.goal or "3-Tier Delegation Task")
        
        # Format into Dict[str, AgentResult] for backward compatibility
        results: Dict[str, AgentResult] = {}
        for agent in agents:
            is_success = res_pipeline.get("success", False)
            results[agent.agent_id] = AgentResult(
                agent_id=agent.agent_id,
                task_id=context.task_id,
                status=AgentStatus.COMPLETED if is_success else AgentStatus.FAILED,
                output=res_pipeline.get("deliverable", ""),
                execution_time_ms=res_pipeline.get("total_time_ms", 0.0),
            )
        return results

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="multi_agent",
            ))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "registered_agents": self._registry.count(),
            "enabled_agents": len(self._registry.list_enabled()),
            "available_patterns": list(self._patterns.keys()),
        }
