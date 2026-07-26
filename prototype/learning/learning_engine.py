"""Learning Engine — stores lessons and insights from reflections.

This is the Phase 2 foundation. It stores lessons derived from
reflection records. Future phases will use these lessons to
optimize prompts, memory, tool selection, and provider choice.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.learning")


@dataclass
class Lesson:
    """A single learned insight."""
    lesson_id: str = field(default_factory=lambda: str(uuid4()))
    lesson: str = ""
    source: str = "reflection"
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LearningEngine:
    """Foundation learning engine for Alfa COS.

    Phase 2 capabilities:
    - Store lessons from reflections
    - Retrieve relevant lessons
    - Track learning statistics

    Future capabilities (Phase 3+):
    - Prompt optimization
    - Memory optimization
    - Tool preference learning
    - Provider preference learning
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._loaded = False
        self._event_bus = event_bus
        self._lessons: List[Lesson] = []
        self._max_lessons = 500

    def load(self) -> None:
        """Initialize the Learning Engine."""
        self._loaded = True
        logger.info("Learning Engine loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def learn(
        self,
        lesson_text: str,
        source: str = "reflection",
        confidence: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Lesson:
        """Store a new lesson.

        Args:
            lesson_text: The insight or lesson learned.
            source: Where this lesson came from.
            confidence: How confident we are in this lesson (0.0 to 1.0).
            metadata: Additional context.

        Returns:
            The stored Lesson object.
        """
        lesson = Lesson(
            lesson=lesson_text,
            source=source,
            confidence=min(1.0, max(0.0, confidence)),
            metadata=metadata or {},
        )
        self._lessons.append(lesson)

        if len(self._lessons) > self._max_lessons:
            self._lessons = self._lessons[-self._max_lessons:]

        logger.info(
            "Lesson stored: source=%s confidence=%.2f",
            source,
            confidence,
        )

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="LearningCompleted",
                payload={
                    "lesson_id": lesson.lesson_id,
                    "source": source,
                    "confidence": confidence,
                },
                source="learning",
            ))

        return lesson

    def get_lessons(self, limit: int = 20) -> List[Lesson]:
        """Return recent lessons."""
        return self._lessons[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Return learning statistics."""
        if not self._lessons:
            return {"total_lessons": 0, "avg_confidence": 0.0, "sources": {}}

        sources: Dict[str, int] = {}
        for lesson in self._lessons:
            sources[lesson.source] = sources.get(lesson.source, 0) + 1

        return {
            "total_lessons": len(self._lessons),
            "avg_confidence": sum(l.confidence for l in self._lessons) / len(self._lessons),
            "sources": sources,
        }

    def shutdown(self) -> None:
        """Shutdown the Learning Engine."""
        self._loaded = False
        logger.info("Learning Engine shutdown")
