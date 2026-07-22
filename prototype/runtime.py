"""Composition root for the Alfa COS MVP runtime."""

from prototype.common import Context, EngineResult, Goal
from prototype.config import SettingsManager, get_settings_manager
from prototype.context import ContextManager
from prototype.kernel import Kernel
from prototype.memory import Memory
from prototype.planner import Planner
from prototype.provider import MockProvider, NVIDIAProvider, OpenRouterProvider, Provider


class AlfaRuntime:
    """Owns the components used by both the CLI and HTTP API."""

    def __init__(self, settings: SettingsManager = None) -> None:
        self._settings = settings or get_settings_manager()
        self.kernel = Kernel()
        self.context_manager = ContextManager()
        self.memory = Memory()
        self.planner = Planner()
        self.provider: Provider = self._create_provider()
        self._components = (
            self.kernel,
            self.context_manager,
            self.memory,
            self.planner,
            self.provider,
        )
        self._loaded = False

    @property
    def provider_name(self) -> str:
        return self._settings.get_provider()

    def _create_provider(self) -> Provider:
        name = self._settings.get_provider()
        if name == "nvidia":
            return NVIDIAProvider(self._settings)
        if name == "openrouter":
            return OpenRouterProvider(self._settings)
        return MockProvider()

    def load(self) -> None:
        if self._loaded:
            return
        for component in self._components:
            component.load()
        self.kernel.set_dependencies(
            planner=self.planner,
            memory=self.memory,
            provider=self.provider,
        )
        self._loaded = True

    def process(self, user_input: str) -> EngineResult:
        if not self._loaded:
            raise RuntimeError("AlfaRuntime must be loaded before processing input")
        context = self.context_manager.build_context(
            goal=Goal(name="USER_INPUT", parameters={"input": user_input})
        )
        return self.kernel.process(user_input, context)

    def shutdown(self) -> None:
        if not self._loaded:
            return
        for component in reversed(self._components):
            component.shutdown()
        self._loaded = False
