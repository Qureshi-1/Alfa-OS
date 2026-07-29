"""Tool Manager — registry, discovery, and execution of tools.

The Tool Manager:
- Registers built-in and plugin tools
- Validates tool permissions
- Executes tools safely
- Provides tool metadata for UI and AI
"""

import logging
from typing import Any, Dict, List, Optional

from prototype.common import Event, EventBus
from prototype.tools.base_tool import BaseTool, ToolResult

logger = logging.getLogger("alfa.tools.manager")


class ToolManager:
    """Central registry and executor for all tools.

    Tools are registered by name. Execution goes through the manager
    to ensure permission validation and event publishing.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._loaded = False
        self._event_bus = event_bus
        self._tools: Dict[str, BaseTool] = {}

    def load(self) -> None:
        """Initialize the Tool Manager and register built-in tools."""
        from prototype.tools.builtin_tools import (
            CalculatorTool,
            DateTimeTool,
            SystemInfoTool,
            DesktopControlTool,
            AndroidInteractionTool,
        )

        self.register(CalculatorTool())
        self.register(DateTimeTool())
        self.register(SystemInfoTool())
        self.register(DesktopControlTool())
        self.register(AndroidInteractionTool())


        self._loaded = True
        logger.info(
            "Tool Manager loaded: %d tools registered",
            len(self._tools),
        )

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its name."""
        name = tool.tool_name
        if name in self._tools:
            logger.warning("Tool '%s' already registered — replacing", name)
        self._tools[name] = tool
        logger.debug("Tool registered: %s", name)

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool by name."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug("Tool unregistered: %s", tool_name)
            return True
        return False

    # ── Execution ─────────────────────────────────────────────────────────

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a registered tool.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.

        Returns:
            A ToolResult with the outcome.
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                status="error",
                error=f"Tool not found: {tool_name}",
            )

        if not tool.health():
            return ToolResult(
                status="error",
                error=f"Tool unhealthy: {tool_name}",
            )

        # Destructive action safety confirmation policy
        destructive_actions = {"delete_file", "reset_hard", "publish_release", "send_deliverables", "drop_db"}
        requested_action = str(arguments.get("action", "")).lower()
        if (requested_action in destructive_actions or getattr(tool, "requires_confirmation", False)) and not arguments.get("confirmed", False):
            logger.warning("Tool '%s' requested destructive action '%s' without explicit user confirmation", tool_name, requested_action)
            return ToolResult(
                status="confirmation_required",
                error=f"User confirmation required before executing destructive action '{requested_action}'",
                metadata={"confirmation_required": True, "action": requested_action, "tool": tool_name},
            )

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="ToolStarted",
                payload={"tool": tool_name},
                source="tool_manager",
            ))

        try:
            result = tool.execute(arguments)
        except Exception as exc:
            logger.exception("Tool execution failed: %s", tool_name)
            result = ToolResult(status="error", error=str(exc))

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="ToolFinished",
                payload={"tool": tool_name, "success": result.success},
                source="tool_manager",
            ))

        logger.info(
            "Tool executed: %s success=%s", tool_name, result.success
        )
        return result

    # ── Query ─────────────────────────────────────────────────────────────

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered tools."""
        return [tool.metadata() for tool in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        """Return names of all registered tools."""
        return list(self._tools.keys())

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Shutdown the Tool Manager."""
        self._tools.clear()
        self._loaded = False
        logger.info("Tool Manager shutdown")
