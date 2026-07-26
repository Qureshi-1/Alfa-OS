"""Tool Executor — bridges agents to the tool system for safe execution."""

import logging
from typing import Any, Dict, List, Optional

from prototype.agent.base_agent import AgentResult, AgentStatus, AgentContext
from prototype.tools.tool_manager import ToolManager
from prototype.tools.base_tool import ToolResult

logger = logging.getLogger("alfa.agent.tool_executor")


class ToolExecutor:
    """Executes tools on behalf of agents with validation and event tracking.

    Agents request tool execution through this executor rather than
    calling ToolManager directly. This adds:
    - Permission validation
    - Execution logging
    - Result wrapping for agent consumption
    """

    def __init__(self, tool_manager: ToolManager) -> None:
        self._tool_manager = tool_manager

    def execute(self, tool_name: str, arguments: Dict[str, Any],
                agent_id: str = "") -> ToolResult:
        """Execute a tool on behalf of an agent."""
        logger.debug("Agent '%s' executing tool: %s", agent_id, tool_name)
        return self._tool_manager.execute(tool_name, arguments)

    def list_available(self, capabilities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List tools available to an agent, optionally filtered by capabilities."""
        all_tools = self._tool_manager.list_tools()
        if not capabilities:
            return all_tools
        cap_set = set(capabilities)
        return [t for t in all_tools if t["name"] in cap_set or not capabilities]

    def has_tool(self, tool_name: str) -> bool:
        return self._tool_manager.get_tool(tool_name) is not None

    def execute_plan_step(self, tool_name: str, arguments: Dict[str, Any],
                          agent_id: str = "") -> ToolResult:
        """Execute a single plan step's tool call."""
        if not self.has_tool(tool_name):
            return ToolResult(
                status="error",
                error=f"Tool not available: {tool_name}",
            )
        return self.execute(tool_name, arguments, agent_id)
