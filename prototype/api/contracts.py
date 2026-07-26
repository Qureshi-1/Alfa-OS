"""API Contracts — stable interfaces for Alfa COS runtime APIs.

Defines the public API surface that external consumers (CLI, HTTP, Desktop)
should depend on. Implementation details are hidden behind these contracts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prototype.common import EngineResult
from prototype.modelhub.base import (
    GenerateRequest, GenerateResponse, StreamChunk,
    ModelInfo, ProviderType,
)
from prototype.worker.base_worker import WorkerResult, WorkerStatus


# ── Request/Response DTOs ───────────────────────────────────────────────────

@dataclass
class ChatRequest:
    message: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    content: str
    model: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStoreRequest:
    content: str
    memory_type: str = "working"
    tags: List[str] = field(default_factory=list)
    importance: int = 0
    persist: bool = False


@dataclass
class MemoryRecallRequest:
    query: str
    memory_types: Optional[List[str]] = None
    limit: int = 10


@dataclass
class MemoryRecallResponse:
    entries: List[Dict[str, Any]]
    total: int = 0
    query_time_ms: float = 0.0


@dataclass
class WorkerExecuteRequest:
    worker_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerScheduleRequest:
    worker_name: str
    interval_seconds: float
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemStatusResponse:
    provider: str = ""
    model: str = ""
    uptime_seconds: float = 0.0
    memory: Dict[str, int] = field(default_factory=dict)
    workers: Dict[str, Any] = field(default_factory=dict)
    plugins: List[Dict[str, Any]] = field(default_factory=list)
    models: int = 0


# ── API Contracts (ABCs) ────────────────────────────────────────────────────

class RuntimeAPI(ABC):
    """Core runtime API contract."""

    @abstractmethod
    def load(self) -> None:
        """Initialize the runtime."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the runtime."""

    @abstractmethod
    def status(self) -> SystemStatusResponse:
        """Get system status."""


class ChatAPI(ABC):
    """Chat/conversation API contract."""

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat message and get a response."""

    @abstractmethod
    def chat_stream(self, request: ChatRequest):
        """Stream a chat response. Yields StreamChunk objects."""
        ...

    @abstractmethod
    def switch_model(self, model: str) -> bool:
        """Switch the active model."""


class MemoryAPI(ABC):
    """Memory operations API contract."""

    @abstractmethod
    def store(self, request: MemoryStoreRequest) -> str:
        """Store a memory. Returns entry ID."""

    @abstractmethod
    def recall(self, request: MemoryRecallRequest) -> MemoryRecallResponse:
        """Recall memories matching query."""

    @abstractmethod
    def forget(self, memory_id: str) -> bool:
        """Delete a memory by ID."""

    @abstractmethod
    def list_memories(self, memory_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List memories."""


class WorkerAPI(ABC):
    """Worker operations API contract."""

    @abstractmethod
    def execute(self, request: WorkerExecuteRequest) -> WorkerResult:
        """Execute a worker."""

    @abstractmethod
    def pause(self, task_id: str) -> bool:
        """Pause a running worker."""

    @abstractmethod
    def resume(self, task_id: str) -> bool:
        """Resume a paused worker."""

    @abstractmethod
    def stop(self, task_id: str) -> bool:
        """Stop a worker."""

    @abstractmethod
    def schedule(self, request: WorkerScheduleRequest) -> str:
        """Schedule periodic worker execution. Returns schedule ID."""

    @abstractmethod
    def unschedule(self, schedule_id: str) -> bool:
        """Remove a scheduled worker."""

    @abstractmethod
    def list_workers(self) -> List[Dict[str, Any]]:
        """List registered workers."""

    @abstractmethod
    def list_running(self) -> List[Dict[str, Any]]:
        """List running tasks."""

    @abstractmethod
    def list_scheduled(self) -> List[Dict[str, Any]]:
        """List scheduled tasks."""


class ModelAPI(ABC):
    """Model hub API contract."""

    @abstractmethod
    def list_models(self, provider: Optional[str] = None, local_only: bool = False) -> List[Dict[str, Any]]:
        """List available models."""

    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model info."""

    @abstractmethod
    def search_models(self, query: str) -> List[Dict[str, Any]]:
        """Search models."""

    @abstractmethod
    def list_providers(self) -> List[Dict[str, Any]]:
        """List registered providers."""


class PluginAPI(ABC):
    """Plugin operations API contract."""

    @abstractmethod
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List registered plugins."""

    @abstractmethod
    def load_plugin(self, file_path: str) -> bool:
        """Hot load a plugin from file."""

    @abstractmethod
    def unload_plugin(self, name: str) -> bool:
        """Hot unload a plugin."""

    @abstractmethod
    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin."""

    @abstractmethod
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""

    @abstractmethod
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""


# ── Agent API ──────────────────────────────────────────────────────────────

@dataclass
class AgentRunRequest:
    agent_id: str
    goal: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMultiRequest:
    agent_ids: List[str]
    goal: str
    pattern: str = "sequential"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlanRequest:
    goal: str
    available_tools: Optional[List[str]] = None
    context: Dict[str, Any] = field(default_factory=dict)


class AgentAPI(ABC):
    """Agent operations API contract."""

    @abstractmethod
    def run_agent(self, request: AgentRunRequest):
        """Run a single agent on a goal."""

    @abstractmethod
    def run_multi(self, request: AgentMultiRequest):
        """Run multiple agents with a collaboration pattern."""

    @abstractmethod
    def list_agents(self) -> List[Dict[str, Any]]:
        """List registered agents."""

    @abstractmethod
    def plan(self, request: AgentPlanRequest):
        """Create a plan for a goal."""

    @abstractmethod
    def reflect(self, agent_id: str, task_id: str):
        """Reflect on an agent's execution."""


# ── Diagnostics API ────────────────────────────────────────────────────────

class DiagnosticsAPI(ABC):
    """Diagnostics API contract."""

    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Get system-wide diagnostic information."""

    @abstractmethod
    def get_health_summary(self) -> Dict[str, Any]:
        """Get aggregated health status."""

    @abstractmethod
    def check_all_health(self) -> Dict[str, Any]:
        """Run all health checks."""

    @abstractmethod
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get metric data."""


# ── Service Registry API ───────────────────────────────────────────────────

class ServiceRegistryAPI(ABC):
    """Internal service registry API contract."""

    @abstractmethod
    def list_services(self) -> List[Dict[str, Any]]:
        """List registered services."""

    @abstractmethod
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service info by name."""

    @abstractmethod
    def check_health(self, name: str) -> bool:
        """Check health of a specific service."""

    @abstractmethod
    def check_all_health(self) -> Dict[str, bool]:
        """Check health of all services."""