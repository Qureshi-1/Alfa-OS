"""Alfa COS Kernel — central orchestrator for the conversation pipeline.

Pipeline: User → Kernel → Planner → Memory → Provider → Assistant → Logging
"""

import logging
from typing import Optional

from prototype.common import Goal, Context, Plan, EngineResult, Episode
from prototype.planner import Planner
from prototype.memory import Memory
from prototype.provider.api_provider import Provider
from prototype.kernel.goal_interpreter import GoalInterpreter

logger = logging.getLogger("alfa.kernel")


class Kernel:
    """Routes user input through the full COS pipeline."""

    def __init__(self) -> None:
        self._loaded = False
        self._planner: Optional[Planner] = None
        self._memory: Optional[Memory] = None
        self._provider: Optional[Provider] = None
        self._interpreter = GoalInterpreter()

    # ── Wiring ────────────────────────────────────────────────────────────

    def set_dependencies(
        self,
        planner: Planner,
        memory: Memory,
        provider: Provider,
    ) -> None:
        self._planner = planner
        self._memory = memory
        self._provider = provider

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Main pipeline ─────────────────────────────────────────────────────

    def process(self, user_input: str, context: Context) -> EngineResult:
        """Execute the full pipeline for a single user turn."""
        try:
            goal = self._interpreter.interpret(user_input)

            # Fast-path built-in commands (bypass LLM).
            handler = self._builtin_handlers.get(goal.name)
            if handler is not None:
                return handler(self, goal)

            # Standard conversation path → Planner → Memory → Provider.
            return self._conversation(goal, context)

        except Exception as exc:
            logger.exception("Kernel.process failed")
            return EngineResult(
                content="An internal error occurred.",
                success=False,
                error=str(exc),
            )

    # ── Built-in command handlers (bypass LLM) ────────────────────────────

    @staticmethod
    def _handle_empty(_self: "Kernel", goal: Goal) -> EngineResult:
        return EngineResult(content="", success=True)

    @staticmethod
    def _handle_exit(_self: "Kernel", goal: Goal) -> EngineResult:
        return EngineResult(content="exit", success=True)

    @staticmethod
    def _handle_remember(self: "Kernel", goal: Goal) -> EngineResult:
        content = goal.parameters.get("content", "")
        if not content:
            return EngineResult(content="Nothing to remember.", success=False)
        episode = self._memory.remember(content)
        logger.info("Memory stored: id=%s", episode.id[:8])
        return EngineResult(
            content=f"Remembered: {content} (id: {episode.id[:8]})",
            success=True,
        )

    @staticmethod
    def _handle_recall(self: "Kernel", goal: Goal) -> EngineResult:
        query = goal.parameters.get("query", "")
        episodes = self._memory.recall(query)
        if not episodes:
            return EngineResult(content="No memories found.", success=True)
        lines = [f"  {ep.id[:8]} | {ep.content}" for ep in episodes]
        return EngineResult(
            content="Memories:\n" + "\n".join(lines), success=True
        )

    @staticmethod
    def _handle_list(self: "Kernel", goal: Goal) -> EngineResult:
        episodes = self._memory.get_working_memory()
        if not episodes:
            return EngineResult(content="No memories.", success=True)
        lines = [f"  {ep.id[:8]} | {ep.content}" for ep in episodes]
        return EngineResult(
            content="All memories:\n" + "\n".join(lines), success=True
        )

    @staticmethod
    def _handle_forget(self: "Kernel", goal: Goal) -> EngineResult:
        memory_id = goal.parameters.get("memory_id", "")
        if not memory_id:
            return EngineResult(content="Memory ID required.", success=False)
        if self._memory.forget(memory_id):
            logger.info("Memory forgotten: %s", memory_id)
            return EngineResult(content=f"Forgotten: {memory_id}", success=True)
        return EngineResult(content=f"Memory not found: {memory_id}", success=False)

    @staticmethod
    def _handle_clear(self: "Kernel", goal: Goal) -> EngineResult:
        self._memory.clear()
        logger.info("Memory cleared")
        return EngineResult(content="Memory cleared.", success=True)

    @staticmethod
    def _handle_history(self: "Kernel", goal: Goal) -> EngineResult:
        episodes = self._memory.get_working_memory()
        if not episodes:
            return EngineResult(content="No history.", success=True)
        lines = [f"  {ep.id[:8]} | {ep.content}" for ep in episodes]
        return EngineResult(
            content="History:\n" + "\n".join(lines), success=True
        )

    @staticmethod
    def _handle_help(self: "Kernel", goal: Goal) -> EngineResult:
        help_text = (
            "Available commands:\n"
            "  remember <text>  - Save a memory\n"
            "  recall <query>   - Search memories\n"
            "  list             - List all memories\n"
            "  forget <id>      - Delete a memory\n"
            "  clear            - Clear all memories\n"
            "  history          - Show conversation history\n"
            "  help             - Show this help\n"
            "  settings         - Show current configuration\n"
            "  provider [name]  - Show or change provider\n"
            "  model [name]     - Show or change model\n"
            "  apikey <key>     - Set API key for current provider\n"
            "  test             - Test provider connection\n"
            "  exit             - Exit Alfa COS\n"
            "  <anything else>  - Chat with AI"
        )
        return EngineResult(content=help_text, success=True)

    # Dispatch table
    _builtin_handlers = {
        "EMPTY": _handle_empty,
        "EXIT": _handle_exit,
        "REMEMBER": _handle_remember,
        "RECALL": _handle_recall,
        "LIST": _handle_list,
        "FORGET": _handle_forget,
        "CLEAR": _handle_clear,
        "HISTORY": _handle_history,
        "HELP": _handle_help,
    }

    # ── Conversation path (uses LLM) ─────────────────────────────────────

    def _conversation(self, goal: Goal, context: Context) -> EngineResult:
        """Planner → Memory → Provider."""
        # 1. Plan
        plan = self._planner.plan(goal, context)
        logger.debug("Plan: %s", plan.steps)

        # 2. Recall relevant memories
        user_text = goal.parameters.get("input", "")
        memories = self._memory.recall(user_text)
        memory_str = "\n".join(
            f"  {ep.id[:8]} | {ep.content}" for ep in memories
        )

        # 3. Build prompt and call provider
        prompt = (
            "You are Alfa COS, a concise and helpful personal AI assistant. "
            "Use the remembered facts when they are relevant. If the memory "
            "does not contain the answer, say so rather than inventing one.\n\n"
            f"Relevant memory:\n{memory_str or '(none)'}\n\n"
            f"User: {user_text}"
        )

        result = self._provider.generate(prompt)
        logger.info(
            "Provider response: success=%s length=%d",
            result.success,
            len(result.content),
        )
        return result

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._loaded = False
