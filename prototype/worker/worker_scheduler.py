"""Worker Scheduler — simple FIFO queue for scheduling worker tasks."""

import logging
from collections import deque
from typing import Optional, Tuple
from prototype.worker.base_worker import WorkerContext

logger = logging.getLogger("alfa.worker.scheduler")


class WorkerScheduler:
    """Intentionally simple FIFO scheduler for worker execution in v0.3."""

    def __init__(self) -> None:
        self._queue: deque[Tuple[str, WorkerContext]] = deque()

    def enqueue(self, worker_name: str, context: WorkerContext) -> int:
        """Enqueue a task (worker_name, context) for execution.

        Returns:
            Current queue size after enqueueing.
        """
        self._queue.append((worker_name, context))
        logger.debug("Enqueued worker task: worker=%s task_id=%s queue_size=%d",
                     worker_name, context.task_id[:8], len(self._queue))
        return len(self._queue)

    def dequeue(self) -> Optional[Tuple[str, WorkerContext]]:
        """Dequeue the next task in FIFO order."""
        if not self._queue:
            return None
        return self._queue.popleft()

    def peek(self) -> Optional[Tuple[str, WorkerContext]]:
        """Peek at the next item in queue without removing it."""
        if not self._queue:
            return None
        return self._queue[0]

    def size(self) -> int:
        """Return the current queue size."""
        return len(self._queue)

    def clear(self) -> None:
        """Clear all queued tasks."""
        self._queue.clear()
