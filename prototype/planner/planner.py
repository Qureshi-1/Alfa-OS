from prototype.common import Goal, Context, Plan


class Planner:
    def __init__(self):
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def plan(self, goal: Goal, context: Context) -> Plan:
        action = self._classify(goal.name)
        return Plan(
            goal=goal,
            steps=[{"action": action, "description": f"Handle {action} request"}]
        )

    def _classify(self, goal_name: str) -> str:
        if goal_name in ("REMEMBER", "RECALL", "LIST", "FORGET", "CLEAR", "HISTORY"):
            return "memory"
        if goal_name in ("EXIT", "EMPTY"):
            return "control"
        return "conversation"

    def shutdown(self) -> None:
        self._loaded = False