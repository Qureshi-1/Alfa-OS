"""Internal Service Registry — dynamic module discovery and health monitoring."""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("alfa.services")


@dataclass
class ServiceInfo:
    """Metadata for a registered service."""
    service_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    status: str = "registered"
    health_fn: Optional[Callable[[], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_health_check: float = 0.0
    health_ok: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "status": self.status,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
            "last_health_check": self.last_health_check,
            "health_ok": self.health_ok,
        }


class ServiceRegistry:
    """Central registry for internal COS services.

    Services register themselves and their health check functions.
    Other modules discover services by name or capability.
    """

    def __init__(self) -> None:
        self._services: Dict[str, ServiceInfo] = {}
        self._lock = threading.RLock()
        self._health_interval = 30.0
        self._health_thread: Optional[threading.Thread] = None
        self._health_running = False

    def register(self, name: str, version: str = "1.0.0",
                 description: str = "",
                 health_fn: Optional[Callable[[], bool]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a service. Returns service_id."""
        with self._lock:
            service_id = f"svc_{name}_{str(uuid4())[:8]}"
            info = ServiceInfo(
                service_id=service_id,
                name=name,
                version=version,
                description=description,
                health_fn=health_fn,
                metadata=metadata or {},
            )
            self._services[name] = info
            logger.info("Service registered: %s v%s", name, version)
            return service_id

    def unregister(self, name: str) -> bool:
        with self._lock:
            if name in self._services:
                del self._services[name]
                logger.info("Service unregistered: %s", name)
                return True
            return False

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        return self._services.get(name)

    def list_services(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._services.values()]

    def list_healthy(self) -> List[ServiceInfo]:
        return [s for s in self._services.values() if s.health_ok]

    def list_unhealthy(self) -> List[ServiceInfo]:
        return [s for s in self._services.values() if not s.health_ok]

    def check_health(self, name: str) -> bool:
        """Run health check for a specific service."""
        info = self._services.get(name)
        if not info or not info.health_fn:
            return info is not None

        try:
            ok = info.health_fn()
        except Exception:
            ok = False

        with self._lock:
            info.health_ok = ok
            info.last_health_check = time.time()
            info.status = "healthy" if ok else "unhealthy"

        return ok

    def check_all_health(self) -> Dict[str, bool]:
        """Run health checks for all services."""
        results = {}
        for name in list(self._services.keys()):
            results[name] = self.check_health(name)
        return results

    def start_health_monitor(self, interval: float = 30.0) -> None:
        """Start background health check thread."""
        if self._health_running:
            return
        self._health_interval = interval
        self._health_running = True
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()
        logger.info("Health monitor started: interval=%.1fs", interval)

    def stop_health_monitor(self) -> None:
        self._health_running = False
        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=2)

    def _health_loop(self) -> None:
        while self._health_running:
            time.sleep(self._health_interval)
            self.check_all_health()

    def count(self) -> int:
        return len(self._services)

    def clear(self) -> None:
        with self._lock:
            self._services.clear()
