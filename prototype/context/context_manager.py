"""Context manager — builds request context for the Kernel pipeline."""

from datetime import datetime
from typing import Any, Dict, Optional

from prototype.common import Context, Goal


class ContextManager:
    """Builds and manages execution context for each user request."""

    def __init__(self) -> None:
        self._loaded = False
        self._current_goal: Optional[Goal] = None
        self._current_project: Optional[str] = None
        self._active_session: Optional[str] = None
        self._internet_available: bool = True
        self._device_state: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._conversation_history: list = []
        self._injected_memories: list = []
        self._tool_schemas: list = []

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def inject_memories(self, memories: list) -> None:
        """Inject retrieved memory episodes into current context."""
        self._injected_memories = memories

    def inject_tool_schemas(self, tools: list) -> None:
        """Inject available tool function schemas into context."""
        self._tool_schemas = tools

    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history with sliding window limit (max 50)."""
        self._conversation_history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(self._conversation_history) > 50:
            self._conversation_history.pop(0)

    def get_conversation_context(self) -> list:
        return list(self._conversation_history)

    def build_context(
        self, goal: Optional[Goal] = None, session: Optional[str] = None
    ) -> Context:
        self._current_goal = goal
        if session:
            self._active_session = session
        now = datetime.now()

        user_input = goal.parameters.get("input", "") if goal else ""
        if user_input:
            self.add_message("user", user_input)

        return Context(
            current_task=goal.name if goal else None,
            time=now.isoformat(),
            active_project=self._current_project,
            internet=self._internet_available,
            user_memory={"injected_memories": self._injected_memories},
            metadata={
                "session": self._active_session,
                "device_state": self._device_state,
                "goal": goal.name if goal else None,
                "user_input": user_input,
                "conversation_history": self.get_conversation_context(),
                "tool_schemas": self._tool_schemas,
                **self._metadata,
            },
        )

    def update_context(self, key: str, value: Any) -> None:
        if key == "current_project":
            self._current_project = value
        elif key == "active_session":
            self._active_session = value
        elif key == "internet_available":
            self._internet_available = bool(value)
        elif key == "device_state":
            self._device_state = value if isinstance(value, dict) else {}
        elif key == "metadata":
            self._metadata = value if isinstance(value, dict) else {}
        elif key == "current_goal":
            self._current_goal = value if isinstance(value, Goal) else None
        else:
            self._metadata[key] = value

    def clear(self) -> None:
        self._current_goal = None
        self._current_project = None
        self._active_session = None
        self._internet_available = True
        self._device_state = {}
        self._metadata = {}
        self._conversation_history.clear()
        self._injected_memories.clear()
        self._tool_schemas.clear()

    def shutdown(self) -> None:
        self.clear()
        self._loaded = False