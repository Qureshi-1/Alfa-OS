from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Any, Optional
from uuid import uuid4


@dataclass
class Event:
    event_type: str
    payload: Any = None
    source: str = ""
    target: str = ""
    priority: int = 0
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> Callable[[], None]:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

        def unsubscribe() -> None:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

        return unsubscribe

    def unsubscribe(self, subscription: Callable[[], None]) -> None:
        subscription()

    def publish(self, event: Event) -> None:
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                callback(event)


_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus