"""Alfa COS Runtime — complete cognitive system composition root.

The AlfaRuntime wires together all cognitive subsystems:
- Kernel (orchestration)
- Executive Controller (goal management)
- Planner (task decomposition)
- Memory Manager (working + persistent)
- Decision Engine (action selection)
- Reflection Engine (quality evaluation)
- Learning Engine (insight storage)
- Provider (AI reasoning backend)
- Tool Manager (external capabilities)
- Plugin Manager (extensions)
- Worker Manager (background execution)
- Agent Runtime (autonomous reasoning)
- Service Registry (module discovery)
- Diagnostics (health & metrics)
- Event Bus (inter-module communication)
- Settings Manager (configuration)
"""

import logging
import time
from typing import Optional

from prototype.common import Context, EngineResult, Goal, EventBus, Event
from prototype.config import SettingsManager, get_settings_manager
from prototype.context import ContextManager
from prototype.decision import DecisionEngine
from prototype.executive import ExecutiveController
from prototype.kernel import Kernel
from prototype.learning import LearningEngine
from prototype.memory import Memory, MemoryManager, PersistentMemory
from prototype.planner import Planner
from prototype.plugins import PluginManager
from prototype.provider import (
    MockProvider,
    NVIDIAProvider,
    OllamaProvider,
    OpenRouterProvider,
    Provider,
)
from prototype.reflection import ReflectionEngine
from prototype.tools import ToolManager
from prototype.worker import WorkerManager

# New cognition modules
from prototype.agent.agent_runtime import AgentRuntime
from prototype.services.service_registry import ServiceRegistry
from prototype.diagnostics.diagnostics import Diagnostics

logger = logging.getLogger("alfa.runtime")


class AlfaRuntime:
    """Owns and coordinates all cognitive components.

    Used by the CLI, HTTP API, and Desktop application.
    Business logic remains in the cognitive core — the runtime
    is purely a composition and lifecycle manager.
    """

    def __init__(self, settings: Optional[SettingsManager] = None) -> None:
        self._settings = settings or get_settings_manager()

        # Event Bus — shared communication backbone
        self.event_bus = EventBus()

        # Cognitive Core
        self.kernel = Kernel()
        self.context_manager = ContextManager()
        self.executive = ExecutiveController(event_bus=self.event_bus)
        self.decision = DecisionEngine()
        self.reflection = ReflectionEngine(event_bus=self.event_bus)
        self.learning = LearningEngine(event_bus=self.event_bus)

        # Memory
        self.working_memory = Memory()
        self.persistent_memory = PersistentMemory()
        self.memory_manager = MemoryManager(
            working_memory=self.working_memory,
            persistent_memory=self.persistent_memory,
            event_bus=self.event_bus,
        )

        # Planning
        self.planner = Planner()

        # Provider
        self.provider: Provider = self._create_provider()

        # Tools, Plugins & Workers
        self.tool_manager = ToolManager(event_bus=self.event_bus)
        self.plugin_manager = PluginManager(event_bus=self.event_bus)
        self.worker_manager = WorkerManager(event_bus=self.event_bus)

        # Agent Runtime — autonomous reasoning + multi-agent
        self.agent_runtime = AgentRuntime(
            tool_manager=self.tool_manager,
            event_bus=self.event_bus,
        )

        # Service Registry — internal module discovery
        self.service_registry = ServiceRegistry()

        # Diagnostics — health & metrics
        self.diagnostics = Diagnostics()

        # Component list for lifecycle management (load/shutdown order)
        self._components = [
            self.context_manager,
            self.working_memory,
            self.persistent_memory,
            self.memory_manager,
            self.planner,
            self.provider,
            self.executive,
            self.decision,
            self.reflection,
            self.learning,
            self.tool_manager,
            self.plugin_manager,
            self.worker_manager,
            self.kernel,
        ]
        self._loaded = False

    @property
    def provider_name(self) -> str:
        return self._settings.get_provider()

    def _create_provider(self) -> Provider:
        """Create a provider instance based on current settings."""
        name = self._settings.get_provider()
        if name == "nvidia":
            return NVIDIAProvider(self._settings)
        if name == "openrouter":
            return OpenRouterProvider(self._settings)
        if name == "ollama":
            return OllamaProvider(self._settings)
        return MockProvider()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        """Initialize all components and wire dependencies."""
        if self._loaded:
            return

        for component in self._components:
            component.load()

        # Load agent runtime (depends on tool_manager being loaded)
        self.agent_runtime.load()

        # Register core services
        self.service_registry.register(
            "kernel", description="Central orchestrator",
            health_fn=lambda: self.kernel.is_loaded(),
        )
        self.service_registry.register(
            "memory", description="Memory subsystem",
            health_fn=lambda: self.working_memory is not None,
        )
        self.service_registry.register(
            "provider", description="AI reasoning backend",
            health_fn=lambda: self.provider is not None,
        )
        self.service_registry.register(
            "tools", description="Tool execution system",
            health_fn=lambda: self.tool_manager.is_loaded(),
        )
        self.service_registry.register(
            "plugins", description="Plugin system",
            health_fn=lambda: self.plugin_manager.is_loaded(),
        )
        self.service_registry.register(
            "workers", description="Worker system",
            health_fn=lambda: self.worker_manager.is_loaded(),
        )
        self.service_registry.register(
            "agents", description="Agent runtime",
            health_fn=lambda: self.agent_runtime.is_loaded(),
        )

        # Register health checks for diagnostics
        self.diagnostics.register_health_check(
            "runtime",
            lambda: self._health_check("runtime"),
        )

        # Wire kernel dependencies (backwards compatible with v0.1)
        self.kernel.set_dependencies(
            planner=self.planner,
            memory=self.working_memory,  # Kernel still uses working memory directly
            provider=self.provider,
        )

        self._loaded = True

        self.event_bus.publish(Event(
            event_type="RuntimeStarted",
            payload={"provider": self.provider_name},
            source="runtime",
        ))

        logger.info(
            "Runtime loaded: provider=%s components=%d",
            self.provider_name,
            len(self._components),
        )

    def _health_check(self, component: str):
        """Runtime health check."""
        from prototype.diagnostics.diagnostics import HealthStatus
        return HealthStatus(
            component=component,
            healthy=self._loaded,
            message="Runtime is operational" if self._loaded else "Runtime not loaded",
        )

    def process(self, user_input: str) -> EngineResult:
        """Process user input through the full cognitive pipeline.

        Pipeline: Input → Context → Executive → Decision → Kernel → Reflection
        """
        if not self._loaded:
            raise RuntimeError("AlfaRuntime must be loaded before processing input")

        start = time.time()

        # 1. Build context
        goal = Goal(name="USER_INPUT", parameters={"input": user_input})
        context = self.context_manager.build_context(goal=goal)

        # 2. Executive: create execution
        execution = self.executive.execute_goal(goal, context)

        # 3. Decision: decide what to do
        has_memory = len(self.working_memory.recall(user_input, limit=1)) > 0
        decision = self.decision.decide(
            goal, provider_available=True, has_memory=has_memory
        )

        # 4. Kernel: process through pipeline
        result = self.kernel.process(user_input, context)

        latency_ms = (time.time() - start) * 1000

        # 5. Record diagnostics
        self.diagnostics.record("kernel.latency_ms", latency_ms)
        self.diagnostics.increment("kernel.process_count")

        # 6. Executive: complete execution
        if result.success:
            self.executive.complete_execution(execution.execution_id, result)
        else:
            self.executive.fail_execution(
                execution.execution_id, result.error or "Unknown error"
            )

        # 7. Reflection: evaluate quality
        reflection = self.reflection.reflect(
            execution_id=execution.execution_id,
            result=result,
            latency_ms=latency_ms,
            memory_used=has_memory,
            goal_name=goal.name,
        )

        # 8. Learning: if reflection has recommendations, store lesson
        if reflection.recommendations:
            for rec in reflection.recommendations:
                self.learning.learn(
                    rec,
                    source="reflection",
                    confidence=reflection.quality_score,
                )

        return result

    def switch_provider(self, provider_name: str) -> None:
        """Switch the active provider without restart."""
        self._settings.set_provider(provider_name)
        old_provider = self.provider
        self.provider = self._create_provider()
        self.provider.load()

        # Update kernel's provider
        self.kernel.set_dependencies(
            planner=self.planner,
            memory=self.working_memory,
            provider=self.provider,
        )

        old_provider.shutdown()
        logger.info("Provider switched to: %s", provider_name)

    def get_stats(self) -> dict:
        """Collect system-wide statistics."""
        return {
            "provider": self.provider_name,
            "model": self._settings.get_model(),
            "executive": self.executive.get_stats(),
            "reflection": self.reflection.get_stats(),
            "learning": self.learning.get_stats(),
            "memory": self.memory_manager.get_stats(),
            "tools": self.tool_manager.list_tools(),
            "plugins": self.plugin_manager.list_plugins(),
            "workers": self.worker_manager.get_stats(),
            "agents": self.agent_runtime.get_stats(),
            "services": self.service_registry.list_services(),
            "diagnostics": self.diagnostics.get_stats(),
        }

    def shutdown(self) -> None:
        """Gracefully shutdown all components in reverse order."""
        if not self._loaded:
            return

        self.event_bus.publish(Event(
            event_type="SystemShutdown",
            payload={},
            source="runtime",
        ))

        # Shutdown new modules first
        self.diagnostics.stop_monitoring()
        self.service_registry.stop_health_monitor()
        self.agent_runtime.shutdown()

        for component in reversed(self._components):
            try:
                component.shutdown()
            except Exception as exc:
                logger.warning("Shutdown error: %s", exc)

        self._loaded = False
        logger.info("Runtime shutdown complete")
