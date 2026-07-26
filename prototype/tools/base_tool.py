"""Base Tool interface — all tools implement this contract."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("alfa.tools")


@dataclass
class ToolResult:
    """Result of a tool execution."""
    status: str = "success"
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == "success"


class BaseTool(ABC):
    """Abstract base class for all Alfa COS tools.

    Every tool must provide:
    - tool_name: Unique identifier
    - description: Human-readable description
    - execute(): Perform the tool's action
    - metadata(): Return tool capabilities
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Unique name of this tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this tool."""

    @property
    def permissions(self) -> List[str]:
        """Required permissions for this tool. Override in subclasses."""
        return []

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute the tool with the given arguments.

        Args:
            arguments: Tool-specific arguments.

        Returns:
            A ToolResult with the outcome.
        """

    def health(self) -> bool:
        """Check if the tool is available and healthy."""
        return True

    def metadata(self) -> Dict[str, Any]:
        """Return tool metadata for discovery and UI."""
        return {
            "name": self.tool_name,
            "description": self.description,
            "permissions": self.permissions,
            "healthy": self.health(),
        }
