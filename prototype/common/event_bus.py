"""Event Bus — cross-module communication backbone.

Features:
- Pub/sub with named events
- Wildcard subscriptions (*)
- Priority-based dispatch
- Thread-safe operations
- Event history for debugging
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("alfa.event_bus")


@dataclass
class Event:
    event_type: str
    payload: Any = None
    source: str = ""
    target: str = ""
    priority: int = 0
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "target": self.target,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


class EventBus:
    """Thread-safe event bus with wildcard support, priority dispatch, and history."""

    def __init__(self, max_history: int = 1000) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._wildcard_subscribers: List[Callable[[Event], None]] = []
        self._history: List[Event] = []
        self._max_history = max_history
        self._lock = threading.Lock()
        self._event_count: Dict[str, int] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> Callable[[], None]:
        """Subscribe to an event. Use '*' for all events."""
        with self._lock:
            if event_name == "*":
                self._wildcard_subscribers.append(callback)
                def unsub_wildcard():
                    if callback in self._wildcard_subscribers:
                        self._wildcard_subscribers.remove(callback)
                return unsub_wildcard

            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)

            def unsubscribe() -> None:
                with self._lock:
                    if event_name in self._subscribers and callback in self._subscribers[event_name]:
                        self._subscribers[event_name].remove(callback)

            return unsubscribe

    def unsubscribe(self, subscription: Callable[[], None]) -> None:
        subscription()

    def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers."""
        with self._lock:
            self._record_event(event)
            self._event_count[event.event_type] = self._event_count.get(event.event_type, 0) + 1

            # Collect matching handlers
            handlers: List[Callable[[Event], None]] = []
            if event.event_type in self._subscribers:
                handlers.extend(self._subscribers[event.event_type])
            handlers.extend(self._wildcard_subscribers)

        # Dispatch outside lock to avoid deadlocks
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.warning("Event handler error for '%s': %s", event.event_type, exc)

    def _record_event(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, event_type: Optional[str] = None, limit: int = 50) -> List[Event]:
        with self._lock:
            if event_type:
                return [e for e in self._history if e.event_type == event_type][-limit:]
            return self._history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_events": sum(self._event_count.values()),
                "by_type": dict(self._event_count),
                "subscriber_count": sum(len(subs) for subs in self._subscribers.values()) + len(self._wildcard_subscribers),
                "wildcard_subscribers": len(self._wildcard_subscribers),
                "history_size": len(self._history),
            }

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()

    def reset(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._wildcard_subscribers.clear()
            self._history.clear()
            self._event_count.clear()


_global_event_bus: Optional[EventBus] = None
_global_lock = threading.Lock()


def get_event_bus() -> EventBus:
    global _global_event_bus
    with _global_lock:
        if _global_event_bus is None:
            _global_event_bus = EventBus()
        return _global_event_bus


def reset_event_bus() -> None:
    global _global_event_bus
    with _global_lock:
        if _global_event_bus:
            _global_event_bus.reset()
        _global_event_bus = None