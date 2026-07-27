"""Cognition Reflector — evaluates execution quality and drives learning.

Stage 5 of the cognition pipeline. Takes execution results and produces
reflection output with quality scores, lessons learned, and memory updates.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus
from prototype.cognition.executor import ExecutionResult, StepResult
from prototype.cognition.planner import TaskPlan

logger = logging.getLogger("alfa.cognition.reflector")


@dataclass
class QualityAssessment:
    """Assessment of execution quality for a single dimension."""
    dimension: str = ""
    score: float = 0.0  # 0.0 - 1.0
    reason: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Lesson:
    """A learned lesson from execution."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    category: str = ""  # "success_pattern", "failure_pattern", "optimization"
    confidence: float = 0.0
    source_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryUpdate:
    """A suggested memory update from reflection."""
    content: str = ""
    memory_type: str = "working"  # working, long_term, semantic
    tags: List[str] = field(default_factory=list)
    importance: int = 0


@dataclass
class ReflectionOutput:
    """Output of the reflection stage."""
    id: str = field(default_factory=lambda: str(uuid4()))
    execution_id: str = ""
    plan_id: str = ""
    overall_score: float = 0.0
    assessments: List[QualityAssessment] = field(default_factory=list)
    lessons: List[Lesson] = field(default_factory=list)
    memory_updates: List[MemoryUpdate] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReflectorPlugin:
    """Base class for reflector stage plugins.

    Plugins can:
    - Add custom quality dimensions
    - Override scoring logic
    - Generate domain-specific lessons
    - Customize memory update suggestions
    """

    def assess_quality(
        self, execution: ExecutionResult, plan: TaskPlan,
        context: Dict[str, Any],
    ) -> Optional[QualityAssessment]:
        """Custom quality assessment. Return None to skip."""
        return None

    def generate_lessons(
        self, execution: ExecutionResult, plan: TaskPlan,
        assessments: List[QualityAssessment],
        context: Dict[str, Any],
    ) -> List[Lesson]:
        """Generate domain-specific lessons."""
        return []

    def suggest_memory_updates(
        self, execution: ExecutionResult, plan: TaskPlan,
        context: Dict[str, Any],
    ) -> List[MemoryUpdate]:
        """Suggest memory updates."""
        return []


class CognitionReflector:
    """Stage 5: evaluates execution quality and drives learning.

    Supports plugin-based extension for custom quality dimensions.
    Emits: ReflectionStarted, ReflectionCompleted, LessonLearned
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._plugins: List[ReflectorPlugin] = []
        self._history: List[ReflectionOutput] = []
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("CognitionReflector loaded: %d plugins", len(self._plugins))

    def is_loaded(self) -> bool:
        return self._loaded

    def register_plugin(self, plugin: ReflectorPlugin) -> None:
        self._plugins.append(plugin)

    def unregister_plugin(self, plugin: ReflectorPlugin) -> bool:
        if plugin in self._plugins:
            self._plugins.remove(plugin)
            return True
        return False

    def reflect(
        self,
        execution: ExecutionResult,
        plan: TaskPlan,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReflectionOutput:
        """Reflect on an execution result.

        Args:
            execution: The execution result to reflect on.
            plan: The original plan.
            context: Additional context.

        Returns:
            ReflectionOutput with quality scores, lessons, and memory updates.
        """
        ctx = context or {}
        start = time.time()

        self._emit("ReflectionStarted", {
            "execution_id": execution.id,
            "plan_id": plan.id,
            "success": execution.success,
        })

        # Quality assessments
        assessments = self._assess_quality(execution, plan, ctx)

        # Plugin assessments
        for plugin in self._plugins:
            plugin_assessment = plugin.assess_quality(execution, plan, ctx)
            if plugin_assessment:
                assessments.append(plugin_assessment)

        # Overall score
        overall = self._compute_overall_score(assessments)

        # Generate lessons
        lessons = self._generate_lessons(execution, plan, assessments, ctx)

        # Plugin lessons
        for plugin in self._plugins:
            plugin_lessons = plugin.generate_lessons(execution, plan, assessments, ctx)
            lessons.extend(plugin_lessons)

        # Memory updates
        memory_updates = self._suggest_memory_updates(execution, plan, ctx)

        for plugin in self._plugins:
            plugin_updates = plugin.suggest_memory_updates(execution, plan, ctx)
            memory_updates.extend(plugin_updates)

        # Recommendations
        recommendations = self._generate_recommendations(assessments, lessons)

        result = ReflectionOutput(
            execution_id=execution.id,
            plan_id=plan.id,
            overall_score=overall,
            assessments=assessments,
            lessons=lessons,
            memory_updates=memory_updates,
            recommendations=recommendations,
            latency_ms=round((time.time() - start) * 1000, 2),
        )

        # Store in history
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        self._emit("ReflectionCompleted", {
            "execution_id": execution.id,
            "overall_score": overall,
            "lesson_count": len(lessons),
            "recommendation_count": len(recommendations),
            "latency_ms": result.latency_ms,
        })

        for lesson in lessons:
            self._emit("LessonLearned", {
                "lesson_id": lesson.id,
                "category": lesson.category,
                "content": lesson.content[:100],
            })

        return result

    def _assess_quality(self, execution: ExecutionResult, plan: TaskPlan,
                        context: Dict[str, Any]) -> List[QualityAssessment]:
        """Built-in quality assessments."""
        assessments = []

        # Success rate
        total = len(execution.step_results)
        if total > 0:
            success_rate = len(execution.succeeded_steps) / total
            assessments.append(QualityAssessment(
                dimension="success_rate",
                score=success_rate,
                reason=f"{len(execution.succeeded_steps)}/{total} steps succeeded",
            ))

        # Efficiency (time vs estimated)
        if plan.estimated_total_cost > 0 and execution.total_time_ms > 0:
            efficiency = min(plan.estimated_total_cost / max(execution.total_time_ms / 1000, 0.001), 1.0)
            assessments.append(QualityAssessment(
                dimension="efficiency",
                score=round(efficiency, 3),
                reason=f"Execution took {execution.total_time_ms:.0f}ms",
            ))

        # Completeness
        plan_steps = len(plan.steps)
        completed = len(execution.succeeded_steps)
        if plan_steps > 0:
            completeness = completed / plan_steps
            assessments.append(QualityAssessment(
                dimension="completeness",
                score=completeness,
                reason=f"{completed}/{plan_steps} planned steps completed",
            ))

        # Output quality
        has_output = execution.output is not None
        assessments.append(QualityAssessment(
            dimension="output_quality",
            score=1.0 if has_output else 0.0,
            reason="Output generated" if has_output else "No output produced",
        ))

        return assessments

    def _compute_overall_score(self, assessments: List[QualityAssessment]) -> float:
        """Compute weighted overall score from assessments."""
        if not assessments:
            return 0.5
        weights = {
            "success_rate": 0.4,
            "efficiency": 0.15,
            "completeness": 0.3,
            "output_quality": 0.15,
        }
        total_weight = 0
        weighted_sum = 0
        for a in assessments:
            w = weights.get(a.dimension, 0.1)
            weighted_sum += a.score * w
            total_weight += w
        return round(weighted_sum / max(total_weight, 0.001), 3)

    def _generate_lessons(self, execution: ExecutionResult, plan: TaskPlan,
                          assessments: List[QualityAssessment],
                          context: Dict[str, Any]) -> List[Lesson]:
        """Generate lessons from execution analysis."""
        lessons = []

        # Failure patterns
        for sr in execution.failed_steps:
            lessons.append(Lesson(
                content=f"Step '{sr.step_name}' failed: {sr.error}",
                category="failure_pattern",
                confidence=0.9,
                source_step=sr.step_id,
            ))

        # Success patterns
        if execution.success and len(execution.step_results) > 1:
            lessons.append(Lesson(
                content=f"Plan '{plan.goal}' completed successfully in {execution.total_time_ms:.0f}ms",
                category="success_pattern",
                confidence=0.8,
            ))

        # Optimization opportunities
        for a in assessments:
            if a.score < 0.5:
                lessons.append(Lesson(
                    content=f"Low {a.dimension}: {a.reason}",
                    category="optimization",
                    confidence=0.7,
                ))

        return lessons

    def _suggest_memory_updates(self, execution: ExecutionResult, plan: TaskPlan,
                                context: Dict[str, Any]) -> List[MemoryUpdate]:
        """Suggest memory updates based on execution."""
        updates = []

        # Store successful execution patterns
        if execution.success:
            updates.append(MemoryUpdate(
                content=f"Successfully executed: {plan.goal}",
                memory_type="long_term",
                tags=["execution", "success"],
                importance=3,
            ))

        # Store failure patterns for avoidance
        for sr in execution.failed_steps:
            updates.append(MemoryUpdate(
                content=f"Failed: {sr.step_name} - {sr.error}",
                memory_type="long_term",
                tags=["execution", "failure"],
                importance=5,
            ))

        return updates

    def _generate_recommendations(self, assessments: List[QualityAssessment],
                                  lessons: List[Lesson]) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        for a in assessments:
            if a.score < 0.3:
                recs.append(f"Improve {a.dimension}: {a.reason}")
            if a.suggestions:
                recs.extend(a.suggestions)

        failure_count = sum(1 for l in lessons if l.category == "failure_pattern")
        if failure_count > 2:
            recs.append("Multiple failures detected — consider replanning or using different tools")

        return recs

    def get_history(self, limit: int = 10) -> List[ReflectionOutput]:
        """Get recent reflection history."""
        return self._history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        if not self._history:
            return {"total_reflections": 0, "avg_score": 0}
        scores = [r.overall_score for r in self._history]
        return {
            "total_reflections": len(self._history),
            "avg_score": round(sum(scores) / len(scores), 3),
            "min_score": min(scores),
            "max_score": max(scores),
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="reflector",
            ))
