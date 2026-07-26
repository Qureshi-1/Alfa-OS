"""Diagnostics — system health, metrics, and monitoring for Alfa COS."""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("alfa.diagnostics")


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Health status for a component."""
    component: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


class Diagnostics:
    """System diagnostics collector and health monitor.

    Provides:
    - Metrics collection (counters, gauges, histograms)
    - Component health checks
    - System-wide health aggregation
    - Background health monitoring
    """

    def __init__(self) -> None:
        self._metrics: Dict[str, List[MetricPoint]] = {}
        self._health_checks: Dict[str, Callable[[], HealthStatus]] = {}
        self._health_results: Dict[str, HealthStatus] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._health_thread: Optional[threading.Thread] = None
        self._health_running = False
        self._health_interval = 30.0

    # ── Metrics ────────────────────────────────────────────────────────────

    def record(self, name: str, value: float,
               tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric data point."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(MetricPoint(name=name, value=value, tags=tags or {}))
            # Keep last 1000 points per metric
            if len(self._metrics[name]) > 1000:
                self._metrics[name] = self._metrics[name][-1000:]

    def increment(self, name: str, amount: int = 1) -> None:
        """Increment a counter."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def get_metric_history(self, name: str, limit: int = 50) -> List[MetricPoint]:
        with self._lock:
            return self._metrics.get(name, [])[-limit:]

    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """Get min/max/avg/count for a metric."""
        with self._lock:
            points = self._metrics.get(name, [])
        if not points:
            return {"count": 0, "min": 0, "max": 0, "avg": 0}
        values = [p.value for p in points]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    # ── Health Checks ──────────────────────────────────────────────────────

    def register_health_check(self, component: str,
                              check_fn: Callable[[], HealthStatus]) -> None:
        """Register a health check function for a component."""
        self._health_checks[component] = check_fn
        logger.debug("Health check registered: %s", component)

    def unregister_health_check(self, component: str) -> bool:
        if component in self._health_checks:
            del self._health_checks[component]
            self._health_results.pop(component, None)
            return True
        return False

    def check_health(self, component: str) -> Optional[HealthStatus]:
        """Run health check for a specific component."""
        check_fn = self._health_checks.get(component)
        if not check_fn:
            return None

        start = time.time()
        try:
            status = check_fn()
            status.latency_ms = round((time.time() - start) * 1000, 2)
        except Exception as exc:
            status = HealthStatus(
                component=component,
                healthy=False,
                message=str(exc),
                latency_ms=round((time.time() - start) * 1000, 2),
            )

        with self._lock:
            self._health_results[component] = status
        return status

    def check_all(self) -> Dict[str, HealthStatus]:
        """Run all registered health checks."""
        results = {}
        for component in list(self._health_checks.keys()):
            status = self.check_health(component)
            if status:
                results[component] = status
        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """Get aggregated health status."""
        with self._lock:
            results = dict(self._health_results)

        total = len(results)
        healthy = sum(1 for s in results.values() if s.healthy)
        return {
            "total_components": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "overall": healthy == total if total > 0 else True,
            "components": {name: s.to_dict() for name, s in results.items()},
        }

    def start_monitoring(self, interval: float = 30.0) -> None:
        """Start background health monitoring."""
        if self._health_running:
            return
        self._health_interval = interval
        self._health_running = True
        self._health_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._health_thread.start()
        logger.info("Diagnostics monitoring started: interval=%.1fs", interval)

    def stop_monitoring(self) -> None:
        self._health_running = False
        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=2)

    def _monitor_loop(self) -> None:
        while self._health_running:
            time.sleep(self._health_interval)
            self.check_all()

    # ── System Overview ────────────────────────────────────────────────────

    def get_system_info(self) -> Dict[str, Any]:
        """Get system-wide diagnostic information."""
        return {
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "metrics_count": len(self._metrics),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "health_checks": len(self._health_checks),
            "health_summary": self.get_health_summary(),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "total_metrics": sum(len(v) for v in self._metrics.values()),
            "metric_names": list(self._metrics.keys()),
            "counter_names": list(self._counters.keys()),
            "gauge_names": list(self._gauges.keys()),
            "health_check_count": len(self._health_checks),
        }

    def clear(self) -> None:
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._health_results.clear()
