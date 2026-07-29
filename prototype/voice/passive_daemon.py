"""Passive Voice & Vision Daemon — F.R.I.D.A.Y. style continuous passive listener and visual screen observer."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.voice.passive")


@dataclass
class ScreenVisionFrame:
    frame_id: str
    active_window_title: str = "ALFA COS Desktop HUD"
    resolution: str = "1920x1080"
    elements_detected: List[str] = field(default_factory=lambda: ["terminal", "editor", "dashboard_gauges"])
    timestamp: float = field(default_factory=time.time)


class VisionScreenObserver:
    """Observes screen state and active desktop applications."""

    def capture_frame(self) -> ScreenVisionFrame:
        return ScreenVisionFrame(
            frame_id=f"frame_{int(time.time()*1000)}",
            active_window_title="ALFA COS Desktop — Apex Mode",
            resolution="1920x1080",
            elements_detected=["code_editor", "terminal", "swarm_telemetry", "ai_hud"],
        )


class PassiveVoiceVisionDaemon:
    """Continuous passive background listener and visual monitor.

    Simulates F.R.I.D.A.Y. / Ultron style continuous awareness.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self.vision_observer = VisionScreenObserver()
        self.active = False
        self._loaded = False
        self._last_frame: Optional[ScreenVisionFrame] = None

    def load(self) -> None:
        self._loaded = True
        self.active = True
        logger.info("PassiveVoiceVisionDaemon loaded & active")

    def is_loaded(self) -> bool:
        return self._loaded

    def tick(self) -> Dict[str, Any]:
        """Perform a passive monitoring cycle (audio wake phrase check & screen vision capture)."""
        if not self.active:
            return {"active": False}

        self._last_frame = self.vision_observer.capture_frame()

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="PassiveObserverTick",
                payload={
                    "window": self._last_frame.active_window_title,
                    "elements": self._last_frame.elements_detected,
                },
                source="passive_daemon",
            ))

        return {
            "active": True,
            "window": self._last_frame.active_window_title,
            "elements": self._last_frame.elements_detected,
            "timestamp": self._last_frame.timestamp,
        }

    def get_last_vision_frame(self) -> Optional[ScreenVisionFrame]:
        return self._last_frame

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "active": self.active,
            "last_window": self._last_frame.active_window_title if self._last_frame else None,
        }

    def shutdown(self) -> None:
        self.active = False
        self._loaded = False
        logger.info("PassiveVoiceVisionDaemon shutdown")
