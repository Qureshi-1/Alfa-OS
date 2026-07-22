"""Core data types for Alfa COS."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from uuid import uuid4


class PolicyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"


@dataclass
class Goal:
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    current_task: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    battery: Optional[int] = None
    internet: bool = True
    active_project: Optional[str] = None
    user_memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    working: List[Any] = field(default_factory=list)
    long_term: List[Any] = field(default_factory=list)
    knowledge: List[Any] = field(default_factory=list)
    experience: List[Any] = field(default_factory=list)
    preference: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    goal: Goal
    steps: List[Dict[str, Any]] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required: bool = False


@dataclass
class Agent:
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    model: Optional[str] = None


@dataclass
class ReflectionResult:
    passed: bool
    reason: str = ""
    confidence: float = 1.0
    issues: List[str] = field(default_factory=list)


@dataclass
class SecurityCheck:
    allowed: bool
    reason: str = ""
    risk_level: str = "low"


@dataclass
class PolicyCheck:
    decision: PolicyDecision
    reason: str = ""
    required_confirmation: Optional[str] = None


@dataclass
class EngineResult:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class Episode:
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    tags: List[str] = field(default_factory=list)
    importance: int = 0