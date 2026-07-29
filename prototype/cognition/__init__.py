"""Cognition Engine — the central brain of ALFA COS.

Pipeline: Input → Perception → Intent → Planning → Reasoning → Tool Selection → Execution → Reflection → Memory → Response
"""

from .perception import PerceptionEngine, PerceptionResult
from .planner import TaskPlanner, TaskPlan
from .reasoner import Reasoner, ReasoningResult
from .executor import CognitionExecutor, ExecutionResult
from .reflector import CognitionReflector, ReflectionOutput
from .probabilistic_reasoning import (
    ProbabilisticReasoningEngine,
    BayesianInferenceEngine,
    UncertaintyEstimator,
    ConfidencePropagator,
    Hypothesis,
    UncertaintyMetrics,
)
from .cognition_runtime import CognitionRuntime

from .hypervisor import (
    CognitiveHypervisor,
    SnapshotManager,
    ReasoningSandbox,
    HypothesisEnvironment,
    SpeculativeExecutor,
    StateSnapshot,
)

from .local_engine import LocalCognitionEngine, LocalInferenceResult

__all__ = [
    "PerceptionEngine", "PerceptionResult",
    "TaskPlanner", "TaskPlan",
    "Reasoner", "ReasoningResult",
    "CognitionExecutor", "ExecutionResult",
    "CognitionReflector", "ReflectionOutput",
    "CognitionRuntime",
    "ProbabilisticReasoningEngine",
    "BayesianInferenceEngine",
    "UncertaintyEstimator",
    "ConfidencePropagator",
    "Hypothesis",
    "UncertaintyMetrics",
    "CognitiveHypervisor",
    "SnapshotManager",
    "ReasoningSandbox",
    "HypothesisEnvironment",
    "SpeculativeExecutor",
    "StateSnapshot",
    "LocalCognitionEngine",
    "LocalInferenceResult",
]
