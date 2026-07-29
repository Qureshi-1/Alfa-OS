"""Alfa COS Runtime — complete cognitive system composition root.

The AlfaRuntime wires together all cognitive subsystems:
- Kernel (built-in commands)
- CognitionRuntime (primary cognition pipeline)
- ModelHub (universal model registry + router)
- Executive Controller (goal management)
- Planner (task decomposition)
- Memory Manager (working + persistent)
- Decision Engine (action selection)
- Reflection Engine (quality evaluation)
- Learning Engine (insight storage)
- Provider (legacy AI reasoning backend)
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

# Cognition pipeline
from prototype.cognition import CognitionRuntime

# ModelHub — universal model backend
from prototype.modelhub import (
    ModelRegistry,
    ModelRouter,
    ModelDetector,
    GenerateRequest,
    get_model_registry,
    get_model_router,
    get_model_detector,
)
from prototype.modelhub.base import ProviderType

# New modules
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

        # Cognitive Core (legacy)
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

        # Planning (legacy)
        self.planner = Planner()

        # Legacy Provider
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

        # ModelHub — universal model registry + router
        self.model_registry = ModelRegistry(event_bus=self.event_bus)
        self.model_router = ModelRouter(registry=self.model_registry)
        self.model_detector = ModelDetector()

        # CognitionRuntime — primary cognition pipeline
        self.cognition = CognitionRuntime(
            event_bus=self.event_bus,
            memory_manager=self.memory_manager,
            tool_manager=self.tool_manager,
            agent_runtime=self.agent_runtime,
            worker_manager=self.worker_manager,
            diagnostics=None,  # Set after Diagnostics is created
        )

        # Service Registry — internal module discovery
        self.service_registry = ServiceRegistry()

        # Diagnostics — health & metrics
        self.diagnostics = Diagnostics()

        # MissionRuntime — mission lifecycle & task graphs
        from prototype.mission.mission_runtime import MissionRuntime
        self.mission_runtime = MissionRuntime(
            event_bus=self.event_bus,
            memory_manager=self.memory_manager,
            cognition_runtime=self.cognition,
            worker_manager=self.worker_manager,
            diagnostics=self.diagnostics,
        )

        # VoiceRuntime — speech, STT, TTS, wake word & streaming voice session
        from prototype.voice.voice_runtime import VoiceRuntime
        self.voice_runtime = VoiceRuntime(
            event_bus=self.event_bus,
            cognition_runtime=self.cognition,
        )

        # APEX v2.0 Modules — Local Engine, Passive Daemon, Self-Healing, Swarm & Proactive Assistant
        from prototype.cognition.local_engine import LocalCognitionEngine
        from prototype.voice.passive_daemon import PassiveVoiceVisionDaemon
        from prototype.daemon.self_healing import SelfHealingDaemon
        from prototype.agent.swarm_orchestrator import SwarmOrchestrator
        from prototype.executive.proactive_assistant import ProactiveExecutiveAssistant

        self.local_engine = LocalCognitionEngine(event_bus=self.event_bus)
        self.passive_daemon = PassiveVoiceVisionDaemon(event_bus=self.event_bus)
        self.self_healing = SelfHealingDaemon(event_bus=self.event_bus)
        self.swarm_orchestrator = SwarmOrchestrator(registry=self.agent_runtime.registry, event_bus=self.event_bus)
        self.proactive_assistant = ProactiveExecutiveAssistant(event_bus=self.event_bus)

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
            self.mission_runtime,
            self.voice_runtime,
            self.local_engine,
            self.passive_daemon,
            self.self_healing,
            self.proactive_assistant,
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

    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Initialize all components and wire dependencies."""
        if self._loaded:
            return

        for component in self._components:
            component.load()

        # Load agent runtime (depends on tool_manager being loaded)
        self.agent_runtime.load()

        # Load ModelHub
        self.model_registry.load()
        self._register_modelhub_providers()
        self.model_router.load()

        # Load CognitionRuntime and wire handlers
        self.cognition.load()
        self._wire_cognition_handlers()

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
        self.service_registry.register(
            "cognition", description="Cognition pipeline",
            health_fn=lambda: self.cognition.is_loaded(),
        )
        self.service_registry.register(
            "modelhub", description="Universal model hub",
            health_fn=lambda: len(self.model_registry.list_providers()) >= 0,
        )

        # Register health checks for diagnostics
        self.diagnostics.register_health_check(
            "runtime",
            lambda: self._health_check("runtime"),
        )

        # Wire kernel dependencies (backwards compatible for built-in commands)
        self.kernel.set_dependencies(
            planner=self.planner,
            memory=self.working_memory,
            provider=self.provider,
        )

        self._loaded = True

        self.event_bus.publish(Event(
            event_type="RuntimeStarted",
            payload={"provider": self.provider_name},
            source="runtime",
        ))

        logger.info(
            "Runtime loaded: provider=%s components=%d cognition=%s modelhub_providers=%d",
            self.provider_name,
            len(self._components),
            self.cognition.is_loaded(),
            len(self.model_registry.list_providers()),
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

        Pipeline:
        1. Kernel handles built-in commands (remember, recall, help, etc.)
        2. CognitionRuntime handles everything else via full cognition pipeline:
           Input → Perception → Planning → Reasoning → Execution → Reflection
        3. Executive tracks execution lifecycle
        4. Reflection evaluates quality and feeds Learning
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

        # 4. Try Kernel first for built-in commands (remember, recall, help, etc.)
        #    If the Kernel returns a built-in result, use it.
        #    Otherwise, route to CognitionRuntime for full cognition.
        result = self._process_through_pipeline(user_input, context)

        latency_ms = (time.time() - start) * 1000

        # 5. Record diagnostics
        self.diagnostics.record("runtime.latency_ms", latency_ms)
        self.diagnostics.increment("runtime.process_count")
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

    def _process_through_pipeline(
        self, user_input: str, context: Context,
    ) -> EngineResult:
        """Route input: built-in commands → Kernel, everything else → CognitionRuntime."""
        from prototype.kernel.goal_interpreter import GoalInterpreter
        interpreter = GoalInterpreter()
        goal = interpreter.interpret(user_input)

        # Built-in commands bypass cognition — they go through the fast Kernel path
        builtin_goals = {
            "EMPTY", "EXIT", "REMEMBER", "RECALL", "LIST",
            "FORGET", "CLEAR", "HISTORY", "HELP",
        }
        if goal.name in builtin_goals:
            return self.kernel.process(user_input, context)

        # Everything else goes through the full CognitionRuntime pipeline
        try:
            return self.cognition.process(
                user_input,
                context={
                    "provider_name": self.provider_name,
                    "model_name": self._settings.get_model(),
                },
            )
        except Exception as exc:
            logger.warning("CognitionRuntime failed, falling back to Kernel: %s", exc)
            return self.kernel.process(user_input, context)

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
            "cognition": self.cognition.get_stats(),
            "modelhub": self.model_registry.get_stats(),
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

        # Shutdown cognition and modelhub first
        self.cognition.shutdown()
        self.model_router.shutdown()
        self.model_registry.shutdown()

        # Shutdown new modules
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

    # ── ModelHub wiring ───────────────────────────────────────────────────

    def _register_modelhub_providers(self) -> None:
        """Register ModelHub providers based on available configurations."""
        # Register Ollama provider (local)
        try:
            from prototype.modelhub.providers.ollama import OllamaProvider as MHOllama
            ollama_config = {
                "base_url": self._settings.get("ollama_base_url", "http://localhost:11434"),
                "timeout": self._settings.get("ollama_timeout", 60),
            }
            self.model_registry.register_provider(MHOllama(config=ollama_config))
        except Exception as exc:
            logger.debug("Ollama ModelHub provider not available: %s", exc)

        # Register NVIDIA provider (cloud)
        try:
            api_key = self._settings.get("api_key", "")
            if api_key:
                from prototype.modelhub.providers.nvidia import NvidiaProvider as MHNvidia
                self.model_registry.register_provider(MHNvidia(config={"api_key": api_key}))
        except Exception as exc:
            logger.debug("NVIDIA ModelHub provider not available: %s", exc)

        # Register OpenRouter provider (cloud)
        try:
            or_key = self._settings.get("openrouter_api_key", "")
            if or_key:
                from prototype.modelhub.providers.openrouter import OpenRouterProvider as MHOpenRouter
                self.model_registry.register_provider(MHOpenRouter(config={"api_key": or_key}))
        except Exception as exc:
            logger.debug("OpenRouter ModelHub provider not available: %s", exc)

        logger.info(
            "ModelHub providers registered: %d",
            len(self.model_registry.list_providers()),
        )

    # ── CognitionRuntime wiring ───────────────────────────────────────────

    def _wire_cognition_handlers(self) -> None:
        """Wire real tool/agent/worker handlers into CognitionRuntime.

        This replaces placeholder execution with production implementations.
        """
        # Register all tools from ToolManager into CognitionRuntime
        for tool_info in self.tool_manager.list_tools():
            tool_name = tool_info.get("name", "")
            if tool_name:
                self.cognition.register_tool(
                    name=tool_name,
                    capabilities=[tool_info.get("description", tool_name)],
                    handler=self._make_tool_handler(tool_name),
                )

        # Register LLM inference as a tool (the default execution for conversation)
        # Capabilities must match ALL planner action types: respond, reason, generate,
        # parse, verify, gather, tool_select, analyze, execute
        self.cognition.register_tool(
            name="llm_inference",
            capabilities=[
                "generate", "chat", "conversation", "query", "answer",
                "reason", "analyze", "explain", "write", "create",
                "respond", "parse", "verify", "gather", "tool_select",
                "execute", "report", "process",
            ],
            handler=self._llm_inference_handler,
        )

        # Register memory operations
        self.cognition.register_tool(
            name="memory_recall",
            capabilities=["recall", "remember", "search", "retrieve", "memory"],
            handler=self._memory_recall_handler,
        )
        self.cognition.register_tool(
            name="memory_store",
            capabilities=["store", "save", "persist", "memorize"],
            handler=self._memory_store_handler,
        )

        logger.info(
            "CognitionRuntime wired: %d tool handlers",
            len(self.cognition.executor._tool_handlers),
        )

    def _make_tool_handler(self, tool_name: str):
        """Create a handler closure for a ToolManager tool."""
        def handler(params):
            result = self.tool_manager.execute(tool_name, params)
            if result.success:
                return result.result
            raise RuntimeError(result.error or f"Tool '{tool_name}' failed")
        return handler

    def _llm_inference_handler(self, params: dict):
        """Handle LLM inference through ModelHub or legacy provider."""
        prompt = params.get("prompt", params.get("input", params.get("query", "")))
        if not prompt:
            # Fallback: use any string value we can find
            for v in params.values():
                if isinstance(v, str) and len(v) > 0:
                    prompt = v
                    break

        # Try ModelHub first
        if self.model_registry.list_providers():
            try:
                request = GenerateRequest(
                    prompt=prompt,
                    system_prompt=(
                        "You are Alfa COS, a concise and helpful personal AI assistant. "
                        "Use the remembered facts when they are relevant. If the memory "
                        "does not contain the answer, say so rather than inventing one."
                    ),
                    model=self._settings.get_model(),
                    temperature=self._settings.get("temperature", 0.7),
                    max_tokens=self._settings.get("max_tokens", 4096),
                )
                response = self.model_router.generate(request)
                if response.success:
                    self.diagnostics.increment("modelhub.inference_count")
                    return response.content
            except Exception as exc:
                logger.debug("ModelHub inference failed, falling back: %s", exc)

        # Fallback to legacy provider
        result = self.provider.generate(prompt)
        return result.content

    def _memory_recall_handler(self, params: dict):
        """Handle memory recall through MemoryManager."""
        query = params.get("query", params.get("input", ""))
        results = self.memory_manager.recall(query, limit=5)
        if not results:
            return "No relevant memories found."
        return "\n".join(f"- {r.content}" for r in results)

    def _memory_store_handler(self, params: dict):
        """Handle memory storage through MemoryManager."""
        content = params.get("content", params.get("input", ""))
        if content:
            ep = self.memory_manager.remember(content, persist=True)
            return f"Stored memory: {ep.id[:8]}"
        return "Nothing to store."
