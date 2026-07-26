"""Built-in tools for Alfa COS."""

import math
import platform
import sys
from datetime import datetime
from typing import Any, Dict

from prototype.tools.base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Performs safe mathematical calculations."""

    @property
    def tool_name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions safely"

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        expression = arguments.get("expression", "")
        if not expression:
            return ToolResult(status="error", error="No expression provided")

        # Safe math evaluation with restricted builtins
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "int": int, "float": float,
            "pi": math.pi, "e": math.e,
            "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "ceil": math.ceil, "floor": math.floor,
        }
        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return ToolResult(status="success", result=result)
        except Exception as exc:
            return ToolResult(status="error", error=str(exc))


class DateTimeTool(BaseTool):
    """Returns current date and time information."""

    @property
    def tool_name(self) -> str:
        return "datetime"

    @property
    def description(self) -> str:
        return "Get current date, time, and timezone information"

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        now = datetime.now()
        return ToolResult(
            status="success",
            result={
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "iso": now.isoformat(),
                "timestamp": now.timestamp(),
                "weekday": now.strftime("%A"),
            },
        )


class SystemInfoTool(BaseTool):
    """Returns system information."""

    @property
    def tool_name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "Get system platform and Python version information"

    @property
    def permissions(self) -> list:
        return ["system.read"]

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        return ToolResult(
            status="success",
            result={
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": sys.version,
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
        )
