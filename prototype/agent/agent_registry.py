"""Agent Registry — discovery, registration, and lifecycle management for agents."""

import logging
from typing import Any, Callable, Dict, List, Optional

from prototype.agent.base_agent import BaseAgent, AgentStatus

logger = logging.getLogger("alfa.agent.registry")


class AgentRegistry:
    """Central registry for agent discovery and lookup.

    Agents register by agent_id. The registry provides lookup by id,
    role, capability, and health status.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._enabled: Dict[str, bool] = {}
        self._health_check: Optional[Callable[[BaseAgent], bool]] = None

    def register(self, agent: BaseAgent) -> bool:
        agent_id = agent.agent_id
        if agent_id in self._agents:
            logger.warning("Agent '%s' already registered — replacing", agent_id)
        self._agents[agent_id] = agent
        self._enabled[agent_id] = True
        logger.info("Agent registered: %s (%s)", agent_id, agent.name)
        return True

    def unregister(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._enabled.pop(agent_id, None)
            logger.info("Agent unregistered: %s", agent_id)
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def enable(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            self._enabled[agent_id] = True
            return True
        return False

    def disable(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            self._enabled[agent_id] = False
            return True
        return False

    def is_enabled(self, agent_id: str) -> bool:
        return self._enabled.get(agent_id, False)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [a.metadata() for a in self._agents.values()]

    def list_enabled(self) -> List[BaseAgent]:
        return [a for aid, a in self._agents.items() if self._enabled.get(aid, False)]

    def get_by_role(self, role: str) -> List[BaseAgent]:
        return [a for a in self._agents.values() if a.role.value == role]

    def get_by_capability(self, capability: str) -> List[BaseAgent]:
        return [a for a in self._agents.values() if capability in a.capabilities]

    def get_healthy(self) -> List[BaseAgent]:
        if self._health_check:
            return [a for a in self._agents.values() if self._health_check(a)]
        return [a for a in self._agents.values() if a.health()]

    def set_health_check(self, check: Callable[[BaseAgent], bool]) -> None:
        self._health_check = check

    def count(self) -> int:
        return len(self._agents)

    def clear(self) -> None:
        self._agents.clear()
        self._enabled.clear()
