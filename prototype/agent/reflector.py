"""Agent Reflector — self-evaluation of agent performance and plan execution."""

import logging
from typing import Any, Dict, List, Optional

from prototype.agent.base_agent import AgentResult, Plan, ReflectionRecord

logger = logging.getLogger("alfa.agent.reflector")


class AgentReflector:
    """Evaluates agent execution quality and generates improvement recommendations.

    The reflector analyzes:
    - Plan execution success/failure rates
    - Tool usage efficiency
    - Error patterns
    - Response quality heuristics
    """

    def __init__(self) -> None:
        self._history: List[ReflectionRecord] = []
        self._max_history = 100

    def reflect(self, result: AgentResult, plan: Optional[Plan] = None,
                context: Optional[Dict[str, Any]] = None) -> ReflectionRecord:
        """Reflect on an agent's execution result.

        Args:
            result: The agent's execution result.
            plan: The plan that was executed (if any).
            context: Additional context for evaluation.

        Returns:
            A ReflectionRecord with quality score and recommendations.
        """
        ctx = context or {}
        issues: List[str] = []
        recommendations: List[str] = []
        score = 1.0

        # Check execution status
        if not result.success:
            score -= 0.4
            issues.append(f"Execution failed: {result.error}")

        # Check for errors
        if result.error:
            score -= 0.2
            issues.append(f"Error reported: {result.error}")

        # Check tool call efficiency
        if result.tool_calls:
            failed_calls = [tc for tc in result.tool_calls if not tc.get("success", True)]
            if failed_calls:
                score -= 0.1 * len(failed_calls)
                issues.append(f"{len(failed_calls)} tool calls failed")
                recommendations.append("Review tool arguments and permissions")

        # Check plan execution
        if plan:
            plan_issues = self._evaluate_plan(plan)
            issues.extend(plan_issues["issues"])
            recommendations.extend(plan_issues["recommendations"])
            score -= plan_issues["score_deduction"]

        # Check latency
        latency_ms = ctx.get("latency_ms", result.execution_time_ms)
        if latency_ms > 10000:
            score -= 0.1
            recommendations.append("Consider breaking into smaller steps for faster execution")

        # Check if output is empty
        if not result.output and not result.tool_calls:
            score -= 0.1
            recommendations.append("Agent produced no output — review reasoning")

        score = max(0.0, min(1.0, score))

        record = ReflectionRecord(
            task_id=result.task_id,
            agent_id=result.agent_id,
            plan=plan,
            quality_score=score,
            issues=issues,
            recommendations=recommendations,
            metadata={"latency_ms": latency_ms, **ctx},
        )

        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        logger.info(
            "Reflection: agent=%s score=%.2f issues=%d recs=%d",
            result.agent_id, score, len(issues), len(recommendations),
        )
        return record

    def _evaluate_plan(self, plan: Plan) -> Dict[str, Any]:
        """Evaluate plan execution quality."""
        issues: List[str] = []
        recommendations: List[str] = []
        score_deduction = 0.0

        total = len(plan.steps)
        if total == 0:
            return {"issues": issues, "recommendations": recommendations, "score_deduction": 0.0}

        completed = sum(1 for s in plan.steps if s.status == "completed")
        failed = sum(1 for s in plan.steps if s.status == "failed")

        if failed > 0:
            score_deduction += 0.1 * failed
            issues.append(f"{failed}/{total} plan steps failed")
            recommendations.append("Investigate failed steps for systematic issues")

        if completed < total:
            score_deduction += 0.05 * (total - completed)
            issues.append(f"{total - completed}/{total} steps incomplete")

        return {"issues": issues, "recommendations": recommendations, "score_deduction": score_deduction}

    def get_history(self, limit: int = 10) -> List[ReflectionRecord]:
        return self._history[-limit:]

    def get_average_score(self, limit: int = 20) -> float:
        recent = self._history[-limit:]
        if not recent:
            return 0.0
        return sum(r.quality_score for r in recent) / len(recent)

    def get_common_issues(self, limit: int = 20) -> Dict[str, int]:
        issues: Dict[str, int] = {}
        for record in self._history[-limit:]:
            for issue in record.issues:
                issues[issue] = issues.get(issue, 0) + 1
        return dict(sorted(issues.items(), key=lambda x: x[1], reverse=True))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_reflections": len(self._history),
            "average_score": self.get_average_score(),
            "common_issues": self.get_common_issues(5),
        }

    def clear(self) -> None:
        self._history.clear()
