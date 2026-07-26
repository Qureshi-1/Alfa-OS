"""Worker Registry — central directory of available workers."""

import logging
from typing import Any, Dict, List, Optional
from prototype.worker.base_worker import BaseWorker

logger = logging.getLogger("alfa.worker.registry")


class WorkerRegistry:
    """Registry for managing worker registration and lookup."""

    def __init__(self) -> None:
        self._workers: Dict[str, BaseWorker] = {}

    def register(self, worker: BaseWorker) -> None:
        """Register a worker instance."""
        if worker.name in self._workers:
            logger.warning("Worker '%s' already registered — replacing", worker.name)
        self._workers[worker.name] = worker
        logger.info("Worker registered: %s", worker.name)

    def unregister(self, worker_name: str) -> bool:
        """Unregister a worker by name."""
        if worker_name in self._workers:
            del self._workers[worker_name]
            logger.info("Worker unregistered: %s", worker_name)
            return True
        return False

    def get_worker(self, worker_name: str) -> Optional[BaseWorker]:
        """Retrieve worker by name."""
        return self._workers.get(worker_name)

    def list_workers(self) -> List[Dict[str, Any]]:
        """List metadata for all registered workers."""
        return [w.metadata() for w in self._workers.values()]

    def get_worker_names(self) -> List[str]:
        """List all registered worker names."""
        return list(self._workers.keys())

    def clear(self) -> None:
        """Clear all registered workers."""
        self._workers.clear()
