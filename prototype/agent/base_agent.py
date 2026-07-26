"""Base Agent interface and data contracts for Alfa COS Agent Runtime."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("alfa.agent")


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    FAILED = "failed"
    COMPLETED = "completed"


class AgentRole(Enum):
    ASSISTANT = "assistant"
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


@dataclass
class AgentMessage:
    role: str
    content: str
    agent_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentContext:
    task_id: str = field(default_factory=lambda: str(uuid4()))
    goal: str = ""
    messages: List[AgentMessage] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_id: str
    task_id: str
    status: AgentStatus = AgentStatus.COMPLETED
    output: Any = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == AgentStatus.COMPLETED


@dataclass
class PlanStep:
    step_id: str = field(default_factory=lambda: str(uuid4())[:8])
    description: str = ""
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[AgentResult] = None


@dataclass
class Plan:
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    goal: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @property
    def is_complete(self) -> bool:
        return all(s.status == "completed" for s in self.steps)

    @property
    def failed_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.status == "failed"]


@dataclass
class ReflectionRecord:
    task_id: str
    agent_id: str
    plan: Optional[Plan] = None
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class BaseAgent(ABC):
    """Abstract base class for all Alfa COS agents.

    Agents are autonomous reasoning units that can use tools,
    collaborate with other agents, and reflect on their performance.
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent does."""

    @property
    def role(self) -> AgentRole:
        """Agent's role in the system. Override in subclasses."""
        return AgentRole.ASSISTANT

    @property
    def capabilities(self) -> List[str]:
        """Tools/capabilities this agent can use. Override in subclasses."""
        return []

    @abstractmethod
    def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent's task.

        Args:
            context: The execution context with goal, messages, and tools.

        Returns:
            AgentResult with output and any tool calls made.
        """

    def health(self) -> bool:
        """Check if agent is ready to run."""
        return True

    def on_task_start(self, context: AgentContext) -> None:
        """Hook called before task execution."""

    def on_task_complete(self, result: AgentResult) -> None:
        """Hook called after task execution."""

    def metadata(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "healthy": self.health(),
        }
