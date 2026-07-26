"""EchoWorker — validation worker for Worker Framework testing."""

import time
from typing import Any, Dict
from prototype.worker.base_worker import (
    BaseWorker,
    WorkerContext,
    WorkerResult,
    WorkerStatus,
)


class EchoWorker(BaseWorker):
    """Validation worker that echoes back the parameters received."""

    @property
    def name(self) -> str:
        return "echo_worker"

    @property
    def description(self) -> str:
        return "Validation worker that returns its input parameters"

    def execute(self, context: WorkerContext) -> WorkerResult:
        start_time = time.time()
        text = context.parameters.get("message", context.parameters.get("input", "echo"))
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return WorkerResult(
            task_id=context.task_id,
            worker_name=self.name,
            status=WorkerStatus.COMPLETED,
            output={"echo": text, "received_params": context.parameters},
            execution_time_ms=execution_time_ms,
        )
