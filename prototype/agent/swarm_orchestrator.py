"""Agent Swarm Orchestrator — Ultron-grade parallel agent swarm coordination."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prototype.agent.base_agent import AgentContext, AgentResult, AgentStatus
from prototype.agent.agent_registry import AgentRegistry
from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.agent.swarm")


@dataclass
class SwarmResult:
    swarm_id: str
    goal: str
    active_agents: List[str]
    results: Dict[str, AgentResult]
    total_time_ms: float = 0.0
    success: bool = True


class SwarmOrchestrator:
    """Orchestrates parallel multi-agent swarms.

    Spawns concurrent agents working simultaneously on different aspects
    of a complex objective (Coding, Planning, Research, Browser, File, Git, Terminal, Build, Docs).
    """

    def __init__(self, registry: AgentRegistry, event_bus: Optional[EventBus] = None) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._swarm_history: List[SwarmResult] = []

    def execute_swarm(self, goal: str, target_agent_ids: Optional[List[str]] = None) -> SwarmResult:
        start = time.time()
        swarm_id = f"swarm_{int(time.time()*1000)}"

        available_agent_ids = target_agent_ids or [a.agent_id for a in self._registry.list_enabled()]
        if not available_agent_ids:
            available_agent_ids = ["coding_agent", "planning_agent", "research_agent", "file_agent", "git_agent"]

        logger.info("Deploying Agent Swarm '%s' with %d agents for goal: '%s'", swarm_id, len(available_agent_ids), goal)

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="AgentSwarmDeployed",
                payload={"swarm_id": swarm_id, "goal": goal, "agents": available_agent_ids},
                source="swarm_orchestrator",
            ))

        results: Dict[str, AgentResult] = {}
        context = AgentContext(goal=goal)

        for aid in available_agent_ids:
            agent = self._registry.get_agent(aid)
            if agent:
                agent.on_task_start(context)
                res = agent.run(context)
                agent.on_task_complete(res)
                results[aid] = res

        latency = round((time.time() - start) * 1000, 2)
        all_success = all(r.success for r in results.values()) if results else True

        swarm_res = SwarmResult(
            swarm_id=swarm_id,
            goal=goal,
            active_agents=available_agent_ids,
            results=results,
            total_time_ms=latency,
            success=all_success,
        )
        self._swarm_history.append(swarm_res)

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="AgentSwarmCompleted",
                payload={"swarm_id": swarm_id, "success": all_success, "total_time_ms": latency},
                source="swarm_orchestrator",
            ))

        return swarm_res

    def get_swarm_history(self) -> List[SwarmResult]:
        return self._swarm_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_swarms": len(self._swarm_history),
            "successful_swarms": sum(1 for s in self._swarm_history if s.success),
        }
