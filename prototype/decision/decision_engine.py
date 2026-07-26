"""Decision Engine — selects the best action for a given cognitive state.

Given the current goal, plan, context, and available resources,
the Decision Engine determines what action to take next.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prototype.common import Goal, Context, Plan

logger = logging.getLogger("alfa.decision")


class DecisionAction(Enum):
    """Possible actions the system can take."""
    RESPOND = "respond"
    EXECUTE_TOOL = "execute_tool"
    STORE_MEMORY = "store_memory"
    RETRIEVE_MEMORY = "retrieve_memory"
    ASK_USER = "ask_user"
    CALL_PROVIDER = "call_provider"
    RETRY = "retry"
    ABORT = "abort"
    CHANGE_PROVIDER = "change_provider"


@dataclass
class Decision:
    """A decision about what action to take next."""
    action: DecisionAction
    confidence: float = 1.0
    reasoning: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[DecisionAction] = field(default_factory=list)


class DecisionEngine:
    """Evaluates cognitive state and selects the optimal action.

    Uses rule-based decision logic for Phase 2. Future phases
    can integrate ML-based decision making.
    """

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        """Initialize the Decision Engine."""
        self._loaded = True
        logger.info("Decision Engine loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def decide(
        self,
        goal: Goal,
        plan: Optional[Plan] = None,
        context: Optional[Context] = None,
        has_memory: bool = False,
        provider_available: bool = True,
    ) -> Decision:
        """Determine the best next action.

        Args:
            goal: The current goal.
            plan: The current plan (if any).
            context: The current execution context.
            has_memory: Whether relevant memories exist.
            provider_available: Whether the AI provider is available.

        Returns:
            A Decision object with the selected action.
        """
        goal_name = goal.name.upper()

        # ── Memory commands → memory action ───────────────────────────────
        if goal_name in ("REMEMBER",):
            return Decision(
                action=DecisionAction.STORE_MEMORY,
                confidence=1.0,
                reasoning="User explicitly requested memory storage",
            )

        if goal_name in ("RECALL", "LIST", "HISTORY"):
            return Decision(
                action=DecisionAction.RETRIEVE_MEMORY,
                confidence=1.0,
                reasoning="User explicitly requested memory retrieval",
            )

        # ── Control commands ──────────────────────────────────────────────
        if goal_name in ("EXIT", "EMPTY", "HELP", "FORGET", "CLEAR"):
            return Decision(
                action=DecisionAction.RESPOND,
                confidence=1.0,
                reasoning="Built-in command — direct response",
            )

        # ── Conversation path ─────────────────────────────────────────────
        if not provider_available:
            return Decision(
                action=DecisionAction.ABORT,
                confidence=0.9,
                reasoning="Provider not available for conversation",
                alternatives=[DecisionAction.CHANGE_PROVIDER],
            )

        # Standard conversation: retrieve memory + call provider + respond
        return Decision(
            action=DecisionAction.CALL_PROVIDER,
            confidence=0.85,
            reasoning="Conversation goal — call provider with memory context",
            parameters={"use_memory": has_memory},
            alternatives=[DecisionAction.RETRIEVE_MEMORY, DecisionAction.RESPOND],
        )

    def shutdown(self) -> None:
        """Shutdown the Decision Engine."""
        self._loaded = False
        logger.info("Decision Engine shutdown")
