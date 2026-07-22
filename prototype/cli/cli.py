"""CLI module for Alfa COS."""

from typing import Optional

from prototype.common import EngineResult, Context, Goal
from prototype.kernel import Kernel
from prototype.context import ContextManager
from prototype.memory import Memory
from prototype.config import SettingsManager


class CLI:
    """Interactive CLI for the Alfa COS boot sequence."""

    def __init__(self) -> None:
        self._loaded = False
        self._kernel: Optional[Kernel] = None
        self._context_manager: Optional[ContextManager] = None
        self._memory: Optional[Memory] = None
        self._settings: Optional[SettingsManager] = None

    def set_dependencies(
        self,
        kernel: Kernel,
        context_manager: ContextManager,
        memory: Memory,
        settings: Optional[SettingsManager] = None,
    ) -> None:
        self._kernel = kernel
        self._context_manager = context_manager
        self._memory = memory
        self._settings = settings

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def run(self) -> EngineResult:
        """Read one line of input, process, and return the result."""
        print("> ", end="", flush=True)
        user_input = input().strip()

        if not user_input:
            return EngineResult(content="", success=True)

        goal = Goal(name="USER_INPUT", parameters={"input": user_input})
        context = self._context_manager.build_context(goal=goal)

        result = self._kernel.process(user_input, context)
        if result.content:
            print(result.content)
        return result

    def shutdown(self) -> None:
        self._loaded = False