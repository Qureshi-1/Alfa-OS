"""ExecutionContext — wraps all details needed to execute a single task."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    DEPENDENCY_AWARE = "dependency_aware"


@dataclass
class RetryConfig:
    max_retries: int = 0
    backoff_seconds: float = 1.0
    retry_on: List[str] = field(default_factory=list)  # error patterns


@dataclass
class RollbackConfig:
    enabled: bool = False
    handler_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """All details needed to execute a single task."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: float = 30.0
    retry: RetryConfig = field(default_factory=RetryConfig)
    rollback: RollbackConfig = field(default_factory=RollbackConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    priority: int = 0
    handler_type: str = ""  # "tool", "agent", "worker", "cognition"
    handler_name: str = ""
