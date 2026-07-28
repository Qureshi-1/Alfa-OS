"""Learning Runtime — Milestone 6 implementation for ALFA COS v1.1.

Components:
- Experience Replay: ExperienceTuple, ExperienceReplayBuffer
- Reward System: RewardEvaluator (computes scalar rewards for state-action pairs)
- Self Improvement Memory: SelfImprovementMemory (persists learned policies to SQLite)
- Reinforcement Learning Loop: RLLearningLoop (manages state-action-reward-next_state cycles)
- Learning Runtime: LearningRuntime composition root
"""

import json
import logging
import random
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.learning.runtime")


@dataclass
class ExperienceTuple:
    experience_id: str = field(default_factory=lambda: str(uuid4()))
    state: Dict[str, Any] = field(default_factory=dict)
    action: str = ""
    reward: float = 0.0
    next_state: Dict[str, Any] = field(default_factory=dict)
    done: bool = False
    timestamp: float = field(default_factory=time.time)


class ExperienceReplayBuffer:
    """Experience replay buffer for storing and sampling agent transitions."""

    def __init__(self, capacity: int = 500) -> None:
        self.capacity = capacity
        self.buffer: List[ExperienceTuple] = []

    def push(self, experience: ExperienceTuple) -> None:
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(experience)

    def sample(self, batch_size: int = 5) -> List[ExperienceTuple]:
        if not self.buffer:
            return []
        size = min(batch_size, len(self.buffer))
        return random.sample(self.buffer, size)

    def __len__(self) -> int:
        return len(self.buffer)


class RewardEvaluator:
    """Evaluates task execution quality and computes scalar reward values [-1.0 to 1.0]."""

    def evaluate(self, result_success: bool, latency_ms: float, quality_score: float = 1.0) -> float:
        base = 1.0 if result_success else -1.0
        # Latency penalty: reduce reward if latency exceeds 2000ms
        latency_penalty = max(0.0, (latency_ms - 2000.0) / 10000.0)
        reward = (base * quality_score) - latency_penalty
        return round(max(-1.0, min(1.0, reward)), 4)


class SelfImprovementMemory:
    """SQLite-backed memory for storing self-improvement policy updates."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_updates (
                    update_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    avg_reward REAL NOT NULL,
                    usage_count INTEGER NOT NULL,
                    last_updated REAL NOT NULL
                )
            """)

    def record_action_reward(self, action: str, reward: float) -> None:
        cursor = self._conn.cursor()
        cursor.execute("SELECT avg_reward, usage_count FROM policy_updates WHERE action = ?", (action,))
        row = cursor.fetchone()
        if row:
            avg_r, count = row[0], row[1]
            new_count = count + 1
            new_avg = avg_r + ((reward - avg_r) / new_count)
            with self._conn:
                self._conn.execute(
                    "UPDATE policy_updates SET avg_reward = ?, usage_count = ?, last_updated = ? WHERE action = ?",
                    (new_avg, new_count, time.time(), action),
                )
        else:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO policy_updates VALUES (?, ?, ?, ?, ?)",
                    (str(uuid4()), action, reward, 1, time.time()),
                )

    def get_best_action(self, actions: List[str]) -> Optional[str]:
        if not actions:
            return None
        cursor = self._conn.cursor()
        best_act = actions[0]
        best_score = -float("inf")
        for act in actions:
            cursor.execute("SELECT avg_reward FROM policy_updates WHERE action = ?", (act,))
            row = cursor.fetchone()
            score = row[0] if row else 0.0
            if score > best_score:
                best_score = score
                best_act = act
        return best_act


class RLLearningLoop:
    """State-Action-Reward RL cycle manager."""

    def __init__(self, replay_buffer: ExperienceReplayBuffer, reward_evaluator: RewardEvaluator, policy_mem: SelfImprovementMemory) -> None:
        self.buffer = replay_buffer
        self.reward_eval = reward_evaluator
        self.policy_mem = policy_mem

    def step(self, state: Dict[str, Any], action: str, success: bool, latency_ms: float, next_state: Dict[str, Any]) -> ExperienceTuple:
        reward = self.reward_eval.evaluate(success, latency_ms)
        exp = ExperienceTuple(state=state, action=action, reward=reward, next_state=next_state, done=success)
        self.buffer.push(exp)
        self.policy_mem.record_action_reward(action, reward)
        return exp


class SkillImprovementEngine:
    """Monitors reflection and experience metrics to improve skill efficiency."""

    def evaluate_skill_progress(self, action: str, history: List[ExperienceTuple]) -> Dict[str, Any]:
        action_exps = [e for e in history if e.action == action]
        if not action_exps:
            return {"action": action, "avg_reward": 0.0, "status": "untested"}
        avg_r = sum(e.reward for e in action_exps) / len(action_exps)
        return {
            "action": action,
            "count": len(action_exps),
            "avg_reward": round(avg_r, 4),
            "status": "proficient" if avg_r > 0.5 else "improving",
        }


class LearningRuntime:
    """Composition Root for Milestone 6 Learning Runtime."""

    def __init__(self, db_path: str = ":memory:", event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()
        self.buffer = ExperienceReplayBuffer()
        self.reward_eval = RewardEvaluator()
        self.policy_mem = SelfImprovementMemory(db_path=db_path)
        self.rl_loop = RLLearningLoop(self.buffer, self.reward_eval, self.policy_mem)
        self.skill_engine = SkillImprovementEngine()
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("LearningRuntime loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def record_experience(self, action: str, success: bool, latency_ms: float = 100.0) -> ExperienceTuple:
        exp = self.rl_loop.step(
            state={"action": action},
            action=action,
            success=success,
            latency_ms=latency_ms,
            next_state={"done": success},
        )
        self._event_bus.publish(Event(
            event_type="ExperienceRecorded",
            payload={"action": action, "reward": exp.reward},
            source="learning_runtime",
        ))
        return exp

    def get_preferred_action(self, available_actions: List[str]) -> Optional[str]:
        return self.policy_mem.get_best_action(available_actions)

    def adapt_policy(self, context: Dict[str, Any], available_actions: List[str]) -> Dict[str, Any]:
        """Adapt policy choices based on historical experience and rewards."""
        best_action = self.get_preferred_action(available_actions)
        return {
            "recommended_action": best_action or (available_actions[0] if available_actions else None),
            "adaptation_confidence": 0.9 if best_action else 0.5,
        }

    def integrate_with_runtimes(self, memory_mgr: Any = None, planner: Any = None, reasoner: Any = None, agent_runtime: Any = None) -> None:
        """Bind learning engine callbacks into memory, planner, reasoner, and agent runtime."""
        self._memory_mgr = memory_mgr
        self._planner = planner
        self._reasoner = reasoner
        self._agent_runtime = agent_runtime
        logger.info("LearningRuntime integrated with cognitive subsystems")

    def evaluate_skill(self, action: str) -> Dict[str, Any]:
        return self.skill_engine.evaluate_skill_progress(action, self.buffer.buffer)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "buffer_experiences": len(self.buffer),
            "loaded": self._loaded,
        }


