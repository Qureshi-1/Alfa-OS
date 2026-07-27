"""Reasoner — selects tools, evaluates strategies, and decides execution approach.

Stage 3 of the cognition pipeline. Takes a TaskPlan and determines the best
tool/agent/worker for each step, considering capabilities, availability, and cost.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from prototype.common import Event, EventBus
from prototype.cognition.planner import TaskPlan, TaskStep

logger = logging.getLogger("alfa.cognition.reasoner")


@dataclass
class ToolCandidate:
    """A candidate tool/agent/worker for a step."""
    name: str
    type: str  # "tool", "agent", "worker"
    score: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    available: bool = True
    estimated_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """Output of the reasoning stage."""
    id: str = field(default_factory=lambda: str(uuid4()))
    plan_id: str = ""
    selections: Dict[str, ToolCandidate] = field(default_factory=dict)
    strategy: str = "sequential"
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasonerPlugin:
    """Base class for reasoner stage plugins.

    Plugins can:
    - Override tool selection for specific steps
    - Provide alternative strategies (parallel, debate, etc.)
    - Score candidate tools differently
    - Post-process reasoning results
    """

    def select_tool(
        self, step: TaskStep, candidates: List[ToolCandidate],
        context: Dict[str, Any],
    ) -> Optional[ToolCandidate]:
        """Override tool selection for a step. Return None to use default."""
        return None

    def score_candidates(
        self, step: TaskStep, candidates: List[ToolCandidate],
        context: Dict[str, Any],
    ) -> List[ToolCandidate]:
        """Override scoring. Return re-scored candidates."""
        return candidates

    def determine_strategy(
        self, plan: TaskPlan, context: Dict[str, Any],
    ) -> str:
        """Override execution strategy. Return strategy name."""
        return ""


class Reasoner:
    """Stage 3: selects tools and strategies for plan execution.

    Supports plugin-based extension for custom selection logic.
    Emits: ReasoningStarted, ReasoningCompleted, ToolSelected
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._plugins: List[ReasonerPlugin] = []
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._worker_registry: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("Reasoner loaded: %d plugins", len(self._plugins))

    def is_loaded(self) -> bool:
        return self._loaded

    def register_plugin(self, plugin: ReasonerPlugin) -> None:
        self._plugins.append(plugin)

    def unregister_plugin(self, plugin: ReasonerPlugin) -> bool:
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def register_tool(self, name: str, capabilities: List[str],
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register an available tool for reasoning."""
        self._tool_registry[name] = {
            "capabilities": capabilities,
            "available": True,
            "metadata": metadata or {},
        }

    def register_agent(self, name: str, capabilities: List[str],
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register an available agent for reasoning."""
        self._agent_registry[name] = {
            "capabilities": capabilities,
            "available": True,
            "metadata": metadata or {},
        }

    def register_worker(self, name: str, capabilities: List[str],
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register an available worker for reasoning."""
        self._worker_registry[name] = {
            "capabilities": capabilities,
            "available": True,
            "metadata": metadata or {},
        }

    def reason(
        self,
        plan: TaskPlan,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReasoningResult:
        """Reason about a plan and select tools/agents for each step.

        Args:
            plan: The task plan to reason about.
            context: Additional context.

        Returns:
            ReasoningResult with tool selections for each step.
        """
        ctx = context or {}
        start = time.time()

        self._emit("ReasoningStarted", {
            "plan_id": plan.id,
            "step_count": len(plan.steps),
        })

        selections: Dict[str, ToolCandidate] = {}
        trace: List[Dict[str, Any]] = []

        for step in plan.steps:
            candidates = self._find_candidates(step)
            self._score_candidates(step, candidates, ctx)

            # Let plugins try to select
            selected = None
            for plugin in self._plugins:
                selected = plugin.select_tool(step, candidates, ctx)
                if selected:
                    break

            # Default selection: highest-scoring available candidate
            if not selected and candidates:
                available = [c for c in candidates if c.available]
                if available:
                    selected = max(available, key=lambda c: c.score)

            if selected:
                selections[step.id] = selected
                self._emit("ToolSelected", {
                    "step_id": step.id,
                    "tool": selected.name,
                    "type": selected.type,
                    "score": selected.score,
                })

            trace.append({
                "step_id": step.id,
                "step_name": step.name,
                "candidates": [{"name": c.name, "type": c.type, "score": c.score} for c in candidates],
                "selected": selected.name if selected else None,
            })

        # Determine strategy
        strategy = self._determine_strategy(plan, ctx)

        result = ReasoningResult(
            plan_id=plan.id,
            selections=selections,
            strategy=strategy,
            reasoning_trace=trace,
            confidence=self._compute_confidence(selections, plan),
            latency_ms=round((time.time() - start) * 1000, 2),
        )

        self._emit("ReasoningCompleted", {
            "plan_id": plan.id,
            "strategy": strategy,
            "selections": len(selections),
            "confidence": result.confidence,
            "latency_ms": result.latency_ms,
        })

        return result

    def _find_candidates(self, step: TaskStep) -> List[ToolCandidate]:
        """Find all tools/agents/workers that could handle a step."""
        candidates = []

        # Check explicit step requirements
        if step.requires_tool:
            if step.requires_tool in self._tool_registry:
                reg = self._tool_registry[step.requires_tool]
                candidates.append(ToolCandidate(
                    name=step.requires_tool, type="tool",
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))
            return candidates

        if step.requires_agent:
            if step.requires_agent in self._agent_registry:
                reg = self._agent_registry[step.requires_agent]
                candidates.append(ToolCandidate(
                    name=step.requires_agent, type="agent",
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))
            return candidates

        if step.requires_worker:
            if step.requires_worker in self._worker_registry:
                reg = self._worker_registry[step.requires_worker]
                candidates.append(ToolCandidate(
                    name=step.requires_worker, type="worker",
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))
            return candidates

        # Match by action type and capabilities
        action = step.action
        for name, reg in self._tool_registry.items():
            score = self._capability_match(action, reg["capabilities"])
            if score > 0:
                candidates.append(ToolCandidate(
                    name=name, type="tool", score=score,
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))

        for name, reg in self._agent_registry.items():
            score = self._capability_match(action, reg["capabilities"])
            if score > 0:
                candidates.append(ToolCandidate(
                    name=name, type="agent", score=score,
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))

        for name, reg in self._worker_registry.items():
            score = self._capability_match(action, reg["capabilities"])
            if score > 0:
                candidates.append(ToolCandidate(
                    name=name, type="worker", score=score,
                    capabilities=reg["capabilities"],
                    available=reg["available"],
                    metadata=reg["metadata"],
                ))

        return candidates

    def _capability_match(self, action: str, capabilities: List[str]) -> float:
        """Score how well capabilities match an action."""
        if not capabilities:
            return 0.1  # baseline for untyped tools
        action_lower = action.lower()
        for cap in capabilities:
            if action_lower in cap.lower() or cap.lower() in action_lower:
                return 1.0
        # Partial matches
        action_words = set(action_lower.split())
        cap_words = set(" ".join(capabilities).lower().split())
        overlap = action_words & cap_words
        if overlap:
            return len(overlap) / max(len(action_words), 1)
        return 0.0

    def _score_candidates(self, step: TaskStep, candidates: List[ToolCandidate],
                          context: Dict[str, Any]) -> None:
        """Score candidates based on multiple factors."""
        # Plugin scoring
        for plugin in self._plugins:
            plugin.score_candidates(step, candidates, context)

        # Default scoring: already done in _find_candidates
        # Adjust by cost if available
        for c in candidates:
            if c.estimated_cost > 0:
                c.score *= max(0.1, 1.0 - c.estimated_cost * 0.1)

    def _determine_strategy(self, plan: TaskPlan, context: Dict[str, Any]) -> str:
        """Determine execution strategy for the plan."""
        # Plugin override
        for plugin in self._plugins:
            strategy = plugin.determine_strategy(plan, context)
            if strategy:
                return strategy

        # Default: sequential for most plans
        # Check if steps can be parallelized (no dependencies)
        has_deps = any(s.dependencies for s in plan.steps)
        if not has_deps and len(plan.steps) > 1:
            return "parallel"
        return "sequential"

    def _compute_confidence(self, selections: Dict[str, ToolCandidate],
                            plan: TaskPlan) -> float:
        """Compute overall reasoning confidence."""
        if not plan.steps:
            return 1.0
        selected_count = len(selections)
        total_steps = len(plan.steps)
        if total_steps == 0:
            return 1.0
        avg_score = (sum(s.score for s in selections.values()) / selected_count) if selections else 0
        coverage = selected_count / total_steps
        return round((coverage * 0.6 + avg_score * 0.4), 3)

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="reasoner",
            ))
