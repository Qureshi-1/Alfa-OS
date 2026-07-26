"""Reflection Engine — evaluates execution quality and stores insights.

After every completed task, the Reflection Engine:
- Scores quality (latency, errors, reasoning)
- Identifies improvements
- Stores reflection results for future learning
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import EngineResult, Event, EventBus

logger = logging.getLogger("alfa.reflection")


@dataclass
class ReflectionRecord:
    """Result of reflecting on a single execution."""
    reflection_id: str = field(default_factory=lambda: str(uuid4()))
    execution_id: str = ""
    quality_score: float = 0.0
    latency_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    memory_useful: bool = False
    provider_adequate: bool = True
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReflectionEngine:
    """Self-evaluation engine for the cognitive pipeline.

    Evaluates:
    - Response quality (success, content length, relevance)
    - Performance (latency)
    - Error patterns
    - Memory usefulness
    - Provider adequacy
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._loaded = False
        self._event_bus = event_bus
        self._reflections: List[ReflectionRecord] = []
        self._max_reflections = 200
        # Thresholds for quality scoring
        self._latency_threshold_ms = 5000.0
        self._min_content_length = 5

    def load(self) -> None:
        """Initialize the Reflection Engine."""
        self._loaded = True
        logger.info("Reflection Engine loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Reflect ───────────────────────────────────────────────────────────

    def reflect(
        self,
        execution_id: str,
        result: Optional[EngineResult] = None,
        latency_ms: float = 0.0,
        memory_used: bool = False,
        goal_name: str = "",
    ) -> ReflectionRecord:
        """Evaluate a completed execution and produce a reflection record.

        Args:
            execution_id: The ID of the execution being reflected upon.
            result: The EngineResult from the execution.
            latency_ms: Execution latency in milliseconds.
            memory_used: Whether memory was consulted.
            goal_name: Name of the goal that was executed.

        Returns:
            A ReflectionRecord with quality score and recommendations.
        """
        if result is None:
            result = EngineResult(content="", success=True)

        errors: List[str] = []
        recommendations: List[str] = []

        # ── Score components ──────────────────────────────────────────────
        score = 1.0

        # Success check
        if not result.success:
            score -= 0.4
            errors.append(result.error or "Execution failed")
            recommendations.append("Investigate failure cause")

        # Content quality
        if result.success and len(result.content) < self._min_content_length:
            score -= 0.2
            recommendations.append("Response too short — consider more detail")

        # Latency check
        if latency_ms > self._latency_threshold_ms:
            score -= 0.1
            recommendations.append(
                f"High latency ({latency_ms:.0f}ms) — consider provider optimization"
            )

        # Error presence
        if result.error:
            score -= 0.1
            errors.append(result.error)

        # Memory relevance
        memory_useful = memory_used and result.success

        # Provider adequacy
        provider_adequate = result.success and latency_ms < self._latency_threshold_ms

        # Clamp score
        score = max(0.0, min(1.0, score))

        record = ReflectionRecord(
            execution_id=execution_id,
            quality_score=score,
            latency_ms=latency_ms,
            errors=errors,
            recommendations=recommendations,
            memory_useful=memory_useful,
            provider_adequate=provider_adequate,
            metadata={"goal_name": goal_name},
        )

        self._store_reflection(record)

        logger.info(
            "Reflection: execution=%s score=%.2f latency=%.0fms errors=%d",
            execution_id[:8] if execution_id else "none",
            score,
            latency_ms,
            len(errors),
        )

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="ReflectionCompleted",
                payload={
                    "reflection_id": record.reflection_id,
                    "execution_id": execution_id,
                    "quality_score": score,
                },
                source="reflection",
            ))

        return record

    # ── Query ─────────────────────────────────────────────────────────────

    def get_reflections(self, limit: int = 20) -> List[ReflectionRecord]:
        """Return recent reflection records."""
        return self._reflections[-limit:]

    def get_average_quality(self) -> float:
        """Return average quality score across recent reflections."""
        if not self._reflections:
            return 0.0
        return sum(r.quality_score for r in self._reflections) / len(self._reflections)

    def get_stats(self) -> Dict[str, Any]:
        """Return reflection statistics."""
        if not self._reflections:
            return {
                "total_reflections": 0,
                "avg_quality": 0.0,
                "avg_latency_ms": 0.0,
                "error_rate": 0.0,
            }

        total = len(self._reflections)
        error_count = sum(1 for r in self._reflections if r.errors)
        latencies = [r.latency_ms for r in self._reflections]

        return {
            "total_reflections": total,
            "avg_quality": self.get_average_quality(),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            "error_rate": error_count / total if total else 0.0,
        }

    # ── Internal ──────────────────────────────────────────────────────────

    def _store_reflection(self, record: ReflectionRecord) -> None:
        """Store a reflection record, pruning old entries."""
        self._reflections.append(record)
        if len(self._reflections) > self._max_reflections:
            self._reflections = self._reflections[-self._max_reflections:]

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Shutdown the Reflection Engine."""
        self._loaded = False
        logger.info("Reflection Engine shutdown")
