"""Cognition Engine — the central brain of ALFA COS.

Pipeline: Input → Perception → Intent → Planning → Reasoning → Tool Selection → Execution → Reflection → Memory → Response
"""

from .perception import PerceptionEngine, PerceptionResult
from .planner import TaskPlanner, TaskPlan
from .reasoner import Reasoner, ReasoningResult
from .executor import CognitionExecutor, ExecutionResult
from .reflector import CognitionReflector, ReflectionOutput
from .cognition_runtime import CognitionRuntime

__all__ = [
    "PerceptionEngine", "PerceptionResult",
    "TaskPlanner", "TaskPlan",
    "Reasoner", "ReasoningResult",
    "CognitionExecutor", "ExecutionResult",
    "CognitionReflector", "ReflectionOutput",
    "CognitionRuntime",
]
