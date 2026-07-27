"""ToolRouter — routes task actions to the correct handler (tool, agent, worker, cognition)."""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("alfa.execution.tool_router")


class ToolRouter:
    """Routes actions to registered handlers by type and name."""

    def __init__(self) -> None:
        self._tool_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._agent_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._worker_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._cognition_handler: Optional[Callable[[Dict[str, Any]], Any]] = None

    def register_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._tool_handlers[name] = handler

    def register_agent(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._agent_handlers[name] = handler

    def register_worker(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._worker_handlers[name] = handler

    def register_cognition(self, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._cognition_handler = handler

    def unregister_tool(self, name: str) -> bool:
        return self._tool_handlers.pop(name, None) is not None

    def unregister_agent(self, name: str) -> bool:
        return self._agent_handlers.pop(name, None) is not None

    def unregister_worker(self, name: str) -> bool:
        return self._worker_handlers.pop(name, None) is not None

    def has_handler(self, handler_type: str, name: str) -> bool:
        if handler_type == "tool":
            return name in self._tool_handlers
        if handler_type == "agent":
            return name in self._agent_handlers
        if handler_type == "worker":
            return name in self._worker_handlers
        if handler_type == "cognition":
            return self._cognition_handler is not None
        return False

    def route(
        self,
        handler_type: str,
        name: str,
        parameters: Dict[str, Any],
    ) -> Any:
        """Dispatch to the correct handler. Raises if not found."""
        handler = self._get_handler(handler_type, name)
        if not handler:
            raise ValueError(f"No handler for type='{handler_type}', name='{name}'")
        return handler(parameters)

    def _get_handler(
        self, handler_type: str, name: str
    ) -> Optional[Callable[[Dict[str, Any]], Any]]:
        if handler_type == "tool":
            return self._tool_handlers.get(name)
        if handler_type == "agent":
            return self._agent_handlers.get(name)
        if handler_type == "worker":
            return self._worker_handlers.get(name)
        if handler_type == "cognition":
            return self._cognition_handler
        return None

    def get_handler_names(self, handler_type: str) -> list:
        if handler_type == "tool":
            return list(self._tool_handlers.keys())
        if handler_type == "agent":
            return list(self._agent_handlers.keys())
        if handler_type == "worker":
            return list(self._worker_handlers.keys())
        return []

    def clear(self) -> None:
        self._tool_handlers.clear()
        self._agent_handlers.clear()
        self._worker_handlers.clear()
        self._cognition_handler = None
