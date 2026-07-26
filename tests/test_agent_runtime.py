"""Tests for Agent Runtime, Service Registry, and Diagnostics modules."""

import tempfile
import os
import time
import unittest

from prototype.common import Event, EventBus


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Runtime — Base Types
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentTypes(unittest.TestCase):
    def test_agent_status_enum(self):
        from prototype.agent.base_agent import AgentStatus
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.THINKING.value == "thinking"
        assert AgentStatus.ACTING.value == "acting"
        assert AgentStatus.WAITING.value == "waiting"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.COMPLETED.value == "completed"

    def test_agent_role_enum(self):
        from prototype.agent.base_agent import AgentRole
        assert AgentRole.ASSISTANT.value == "assistant"
        assert AgentRole.PLANNER.value == "planner"
        assert AgentRole.EXECUTOR.value == "executor"
        assert AgentRole.CRITIC.value == "critic"
        assert AgentRole.COORDINATOR.value == "coordinator"
        assert AgentRole.SPECIALIST.value == "specialist"

    def test_agent_message_creation(self):
        from prototype.agent.base_agent import AgentMessage
        msg = AgentMessage(role="user", content="hello")
        assert msg.content == "hello"
        assert msg.role == "user"
        assert msg.agent_id == ""
        assert msg.timestamp > 0

    def test_agent_context_creation(self):
        from prototype.agent.base_agent import AgentContext
        ctx = AgentContext(goal="test goal")
        assert ctx.goal == "test goal"
        assert ctx.task_id is not None
        assert isinstance(ctx.messages, list)
        assert isinstance(ctx.available_tools, list)

    def test_agent_result_success(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.COMPLETED)
        assert result.success is True

    def test_agent_result_failure(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.FAILED)
        assert result.success is False

    def test_plan_step_creation(self):
        from prototype.agent.base_agent import PlanStep
        step = PlanStep(description="do something", tool_name="calc")
        assert step.description == "do something"
        assert step.tool_name == "calc"
        assert step.status == "pending"
        assert step.step_id is not None

    def test_plan_creation(self):
        from prototype.agent.base_agent import Plan, PlanStep
        plan = Plan(goal="test")
        assert plan.goal == "test"
        assert plan.is_complete is True  # No steps = complete
        assert len(plan.failed_steps) == 0

    def test_plan_not_complete_with_pending(self):
        from prototype.agent.base_agent import Plan, PlanStep
        plan = Plan(goal="test", steps=[PlanStep(description="step1")])
        assert plan.is_complete is False

    def test_plan_failed_steps(self):
        from prototype.agent.base_agent import Plan, PlanStep, AgentStatus
        step1 = PlanStep(description="s1", status="completed")
        step2 = PlanStep(description="s2", status="failed")
        plan = Plan(goal="test", steps=[step1, step2])
        assert len(plan.failed_steps) == 1
        assert plan.failed_steps[0].description == "s2"

    def test_reflection_record_creation(self):
        from prototype.agent.base_agent import ReflectionRecord
        record = ReflectionRecord(task_id="t1", agent_id="a1", quality_score=0.85)
        assert record.quality_score == 0.85
        assert record.task_id == "t1"


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Registry
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentRegistry(unittest.TestCase):
    def setUp(self):
        from prototype.agent.agent_registry import AgentRegistry
        self.registry = AgentRegistry()

    def _make_agent(self, agent_id="a1", name="Agent1", role="assistant"):
        from prototype.agent.base_agent import BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus

        class StubAgent(BaseAgent):
            def __init__(self, _id, _name, _role):
                self._id = _id
                self._name = _name
                self._role = AgentRole(_role)

            @property
            def agent_id(self): return self._id
            @property
            def name(self): return self._name
            @property
            def description(self): return f"Stub {self._name}"
            @property
            def role(self): return self._role
            @property
            def capabilities(self): return ["calc"]
            def run(self, context):
                return AgentResult(agent_id=self._id, task_id=context.task_id,
                                   status=AgentStatus.COMPLETED, output="done")

        return StubAgent(agent_id, name, role)

    def test_register_and_get(self):
        agent = self._make_agent()
        assert self.registry.register(agent) is True
        assert self.registry.get_agent("a1") is not None
        assert self.registry.get_agent("a1").name == "Agent1"

    def test_unregister(self):
        agent = self._make_agent()
        self.registry.register(agent)
        assert self.registry.unregister("a1") is True
        assert self.registry.get_agent("a1") is None

    def test_unregister_nonexistent(self):
        assert self.registry.unregister("nonexistent") is False

    def test_enable_disable(self):
        agent = self._make_agent()
        self.registry.register(agent)
        assert self.registry.is_enabled("a1") is True
        assert self.registry.disable("a1") is True
        assert self.registry.is_enabled("a1") is False
        assert self.registry.enable("a1") is True
        assert self.registry.is_enabled("a1") is True

    def test_list_agents(self):
        self.registry.register(self._make_agent("a1", "A1"))
        self.registry.register(self._make_agent("a2", "A2"))
        agents = self.registry.list_agents()
        assert len(agents) == 2

    def test_list_enabled(self):
        self.registry.register(self._make_agent("a1", "A1"))
        self.registry.register(self._make_agent("a2", "A2"))
        self.registry.disable("a2")
        enabled = self.registry.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].agent_id == "a1"

    def test_get_by_role(self):
        self.registry.register(self._make_agent("a1", "A1", "assistant"))
        self.registry.register(self._make_agent("a2", "A2", "planner"))
        assistants = self.registry.get_by_role("assistant")
        assert len(assistants) == 1
        assert assistants[0].agent_id == "a1"

    def test_get_by_capability(self):
        self.registry.register(self._make_agent("a1", "A1"))
        result = self.registry.get_by_capability("calc")
        assert len(result) == 1

    def test_count(self):
        assert self.registry.count() == 0
        self.registry.register(self._make_agent())
        assert self.registry.count() == 1

    def test_clear(self):
        self.registry.register(self._make_agent())
        self.registry.clear()
        assert self.registry.count() == 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Planner
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentPlanner(unittest.TestCase):
    def setUp(self):
        from prototype.agent.planner import AgentPlanner
        self.planner = AgentPlanner()

    def test_plan_single_step(self):
        plan = self.planner.plan("do something", ["calc"])
        assert plan.goal == "do something"
        assert len(plan.steps) == 1
        assert plan.steps[0].description == "Execute: do something"

    def test_plan_auto_multi_step(self):
        plan = self.planner.plan("first do X and then do Y", ["calc"])
        assert len(plan.steps) >= 1

    def test_plan_tool_chain(self):
        plan = self.planner.plan("multi step", ["calc"], {"strategy": "tool_chain"})
        assert len(plan.steps) >= 1

    def test_plan_custom_steps(self):
        steps = [
            {"description": "Step 1", "tool": "calc", "arguments": {"expr": "1+1"}},
            {"description": "Step 2", "tool": "datetime"},
        ]
        plan = self.planner.plan("complex", ["calc", "datetime"], {"steps": steps})
        assert len(plan.steps) == 2
        assert plan.steps[0].tool_name == "calc"
        assert plan.steps[1].tool_name == "datetime"

    def test_replan_skips_failed(self):
        from prototype.agent.base_agent import Plan, PlanStep
        step1 = PlanStep(description="s1", step_id="s1", status="completed")
        step2 = PlanStep(description="s2", step_id="s2", status="failed")
        step3 = PlanStep(description="s3", step_id="s3", dependencies=["s2"])
        plan = Plan(goal="test", steps=[step1, step2, step3])
        new_plan = self.planner.replan(plan, step2, "error")
        assert len(new_plan.steps) == 1  # s1 kept, s3 skipped
        assert new_plan.steps[0].description == "s1"

    def test_register_strategy(self):
        custom = lambda goal, tools, ctx: None
        self.planner.register_strategy("custom", custom)
        assert "custom" in self.planner._strategies


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Reflector
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentReflector(unittest.TestCase):
    def setUp(self):
        from prototype.agent.reflector import AgentReflector
        self.reflector = AgentReflector()

    def test_reflect_success(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.COMPLETED, output="hi")
        record = self.reflector.reflect(result)
        assert record.quality_score >= 0.8
        assert record.task_id == "t1"

    def test_reflect_failure(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.FAILED, error="oops")
        record = self.reflector.reflect(result)
        assert record.quality_score < 0.7
        assert len(record.issues) > 0

    def test_reflect_with_plan(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus, Plan, PlanStep
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.COMPLETED, output="ok")
        plan = Plan(goal="test", steps=[
            PlanStep(description="s1", status="completed"),
            PlanStep(description="s2", status="failed"),
        ])
        record = self.reflector.reflect(result, plan)
        assert record.quality_score < 1.0

    def test_get_history(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        for i in range(5):
            result = AgentResult(agent_id="a1", task_id=f"t{i}", status=AgentStatus.COMPLETED, output="ok")
            self.reflector.reflect(result)
        history = self.reflector.get_history(3)
        assert len(history) == 3

    def test_get_average_score(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        for i in range(3):
            result = AgentResult(agent_id="a1", task_id=f"t{i}", status=AgentStatus.COMPLETED, output="ok")
            self.reflector.reflect(result)
        avg = self.reflector.get_average_score()
        assert avg > 0.0

    def test_get_common_issues(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        for i in range(3):
            result = AgentResult(agent_id="a1", task_id=f"t{i}", status=AgentStatus.FAILED, error="same error")
            self.reflector.reflect(result)
        issues = self.reflector.get_common_issues()
        assert len(issues) > 0

    def test_stats(self):
        stats = self.reflector.get_stats()
        assert "total_reflections" in stats
        assert "average_score" in stats

    def test_clear(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.COMPLETED, output="ok")
        self.reflector.reflect(result)
        self.reflector.clear()
        assert len(self.reflector.get_history()) == 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Tool Executor
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolExecutor(unittest.TestCase):
    def setUp(self):
        from prototype.tools.tool_manager import ToolManager
        from prototype.agent.tool_executor import ToolExecutor
        self.tool_manager = ToolManager()
        self.tool_manager.load()
        self.executor = ToolExecutor(self.tool_manager)

    def test_has_tool(self):
        assert self.executor.has_tool("calculator") is True
        assert self.executor.has_tool("nonexistent") is False

    def test_list_available(self):
        tools = self.executor.list_available()
        assert len(tools) >= 3

    def test_execute_tool(self):
        result = self.executor.execute("calculator", {"expression": "1+1"})
        assert result.success

    def test_execute_nonexistent_tool(self):
        result = self.executor.execute("nonexistent_tool", {})
        assert not result.success
        assert "not found" in result.error.lower() or "not available" in result.error.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  Multi-Agent Coordinator
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiAgentCoordinator(unittest.TestCase):
    def setUp(self):
        from prototype.agent.agent_registry import AgentRegistry
        from prototype.agent.tool_executor import ToolExecutor
        from prototype.agent.multi_agent import MultiAgentCoordinator
        from prototype.tools.tool_manager import ToolManager
        from prototype.agent.base_agent import (
            BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus
        )

        self.AgentContext = AgentContext
        self.registry = AgentRegistry()
        self.tool_manager = ToolManager()
        self.tool_manager.load()
        self.tool_executor = ToolExecutor(self.tool_manager)
        self.bus = EventBus()
        self.coordinator = MultiAgentCoordinator(self.registry, self.tool_executor, self.bus)

        # Register two stub agents
        class StubAgent(BaseAgent):
            def __init__(self, _id, _name):
                self._id = _id
                self._name = _name

            @property
            def agent_id(self): return self._id
            @property
            def name(self): return self._name
            @property
            def description(self): return f"Stub {self._name}"
            @property
            def role(self): return AgentRole.ASSISTANT
            @property
            def capabilities(self): return ["calc"]
            def run(self, context):
                return AgentResult(agent_id=self._id, task_id=context.task_id,
                                   status=AgentStatus.COMPLETED, output=f"{self._id} output")

        self.registry.register(StubAgent("a1", "Agent1"))
        self.registry.register(StubAgent("a2", "Agent2"))

    def test_sequential(self):
        context = self.AgentContext(goal="test")
        results = self.coordinator.run(["a1", "a2"], context, "sequential")
        assert len(results) == 2
        assert results["a1"].success
        assert results["a2"].success

    def test_parallel(self):
        context = self.AgentContext(goal="test")
        results = self.coordinator.run(["a1", "a2"], context, "parallel")
        assert len(results) == 2

    def test_pipeline(self):
        context = self.AgentContext(goal="test")
        results = self.coordinator.run(["a1", "a2"], context, "pipeline")
        assert len(results) == 2

    def test_debate(self):
        context = self.AgentContext(goal="topic")
        results = self.coordinator.run(["a1", "a2"], context, "debate")
        assert len(results) >= 2

    def test_skip_disabled_agent(self):
        self.registry.disable("a2")
        context = self.AgentContext(goal="test")
        results = self.coordinator.run(["a1", "a2"], context, "sequential")
        assert len(results) == 1

    def test_stats(self):
        stats = self.coordinator.get_stats()
        assert stats["registered_agents"] == 2
        assert "sequential" in stats["available_patterns"]


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Runtime
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentRuntime(unittest.TestCase):
    def setUp(self):
        from prototype.tools.tool_manager import ToolManager
        from prototype.agent.agent_runtime import AgentRuntime
        from prototype.agent.base_agent import (
            BaseAgent, AgentRole, AgentContext, AgentResult, AgentStatus
        )
        from prototype.common import EventBus

        self.bus = EventBus()
        self.tool_manager = ToolManager()
        self.tool_manager.load()
        self.runtime = AgentRuntime(self.tool_manager, self.bus)

        class StubAgent(BaseAgent):
            @property
            def agent_id(self): return "test_agent"
            @property
            def name(self): return "Test Agent"
            @property
            def description(self): return "A test agent"
            @property
            def role(self): return AgentRole.ASSISTANT
            @property
            def capabilities(self): return ["calculator"]
            def run(self, context):
                return AgentResult(agent_id="test_agent", task_id=context.task_id,
                                   status=AgentStatus.COMPLETED, output="test output")

        self.runtime.register_agent(StubAgent())
        self.runtime.load()

    def test_run_agent(self):
        result = self.runtime.run_agent("test_agent", "do something")
        assert result.success
        assert result.output == "test output"

    def test_run_agent_not_found(self):
        result = self.runtime.run_agent("nonexistent", "do something")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_run_agent_disabled(self):
        self.runtime.registry.disable("test_agent")
        result = self.runtime.run_agent("test_agent", "do something")
        assert not result.success
        assert "disabled" in result.error.lower()

    def test_plan(self):
        plan = self.runtime.plan("calculate something")
        assert plan.goal == "calculate something"
        assert len(plan.steps) >= 1

    def test_reflect(self):
        from prototype.agent.base_agent import AgentResult, AgentStatus
        result = AgentResult(agent_id="a1", task_id="t1", status=AgentStatus.COMPLETED, output="ok")
        record = self.runtime.reflect(result)
        assert record.quality_score > 0

    def test_stats(self):
        stats = self.runtime.get_stats()
        assert "agents" in stats
        assert "reflection" in stats

    def test_shutdown(self):
        self.runtime.shutdown()
        assert self.runtime.is_loaded() is False


# ═══════════════════════════════════════════════════════════════════════════════
#  Service Registry
# ═══════════════════════════════════════════════════════════════════════════════

class TestServiceRegistry(unittest.TestCase):
    def setUp(self):
        from prototype.services.service_registry import ServiceRegistry
        self.registry = ServiceRegistry()

    def test_register_and_get(self):
        sid = self.registry.register("test_svc", version="1.0.0", description="test")
        assert sid is not None
        svc = self.registry.get_service("test_svc")
        assert svc is not None
        assert svc.name == "test_svc"
        assert svc.version == "1.0.0"

    def test_unregister(self):
        self.registry.register("svc1")
        assert self.registry.unregister("svc1") is True
        assert self.registry.get_service("svc1") is None

    def test_unregister_nonexistent(self):
        assert self.registry.unregister("nope") is False

    def test_list_services(self):
        self.registry.register("svc1")
        self.registry.register("svc2")
        services = self.registry.list_services()
        assert len(services) == 2

    def test_health_check(self):
        self.registry.register("svc1", health_fn=lambda: True)
        ok = self.registry.check_health("svc1")
        assert ok is True

    def test_health_check_failure(self):
        self.registry.register("svc1", health_fn=lambda: False)
        ok = self.registry.check_health("svc1")
        assert ok is False

    def test_health_check_exception(self):
        def bad_health():
            raise ValueError("boom")
        self.registry.register("svc1", health_fn=bad_health)
        ok = self.registry.check_health("svc1")
        assert ok is False

    def test_check_all_health(self):
        self.registry.register("svc1", health_fn=lambda: True)
        self.registry.register("svc2", health_fn=lambda: False)
        results = self.registry.check_all_health()
        assert results["svc1"] is True
        assert results["svc2"] is False

    def test_list_healthy(self):
        self.registry.register("svc1", health_fn=lambda: True)
        self.registry.register("svc2", health_fn=lambda: False)
        self.registry.check_all_health()
        healthy = self.registry.list_healthy()
        assert len(healthy) == 1

    def test_list_unhealthy(self):
        self.registry.register("svc1", health_fn=lambda: True)
        self.registry.register("svc2", health_fn=lambda: False)
        self.registry.check_all_health()
        unhealthy = self.registry.list_unhealthy()
        assert len(unhealthy) == 1

    def test_count(self):
        self.registry.register("svc1")
        assert self.registry.count() == 1

    def test_clear(self):
        self.registry.register("svc1")
        self.registry.clear()
        assert self.registry.count() == 0

    def test_service_info_to_dict(self):
        sid = self.registry.register("svc1", version="2.0.0", description="desc")
        svc = self.registry.get_service("svc1")
        d = svc.to_dict()
        assert d["name"] == "svc1"
        assert d["version"] == "2.0.0"


# ═══════════════════════════════════════════════════════════════════════════════
#  Diagnostics
# ═══════════════════════════════════════════════════════════════════════════════

class TestDiagnostics(unittest.TestCase):
    def setUp(self):
        from prototype.diagnostics.diagnostics import Diagnostics
        self.diag = Diagnostics()

    def test_record_metric(self):
        self.diag.record("test.metric", 42.0)
        history = self.diag.get_metric_history("test.metric")
        assert len(history) == 1
        assert history[0].value == 42.0

    def test_record_with_tags(self):
        self.diag.record("test.metric", 1.0, tags={"env": "test"})
        history = self.diag.get_metric_history("test.metric")
        assert history[0].tags["env"] == "test"

    def test_increment_counter(self):
        self.diag.increment("test.counter")
        self.diag.increment("test.counter", 5)
        assert self.diag.get_counter("test.counter") == 6

    def test_gauge(self):
        self.diag.gauge("test.gauge", 3.14)
        assert self.diag.get_gauge("test.gauge") == 3.14

    def test_get_metric_stats(self):
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            self.diag.record("test.stats", v)
        stats = self.diag.get_metric_stats("test.stats")
        assert stats["count"] == 5
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["avg"] == 3.0

    def test_register_health_check(self):
        from prototype.diagnostics.diagnostics import HealthStatus
        self.diag.register_health_check(
            "comp1",
            lambda: HealthStatus(component="comp1", healthy=True),
        )
        status = self.diag.check_health("comp1")
        assert status.healthy is True

    def test_health_check_failure(self):
        from prototype.diagnostics.diagnostics import HealthStatus
        def fail_check():
            raise ValueError("broken")
        self.diag.register_health_check("comp1", fail_check)
        status = self.diag.check_health("comp1")
        assert status.healthy is False

    def test_unregister_health_check(self):
        from prototype.diagnostics.diagnostics import HealthStatus
        self.diag.register_health_check(
            "comp1",
            lambda: HealthStatus(component="comp1", healthy=True),
        )
        assert self.diag.unregister_health_check("comp1") is True
        assert self.diag.unregister_health_check("comp1") is False

    def test_check_all_health(self):
        from prototype.diagnostics.diagnostics import HealthStatus
        self.diag.register_health_check(
            "c1", lambda: HealthStatus(component="c1", healthy=True))
        self.diag.register_health_check(
            "c2", lambda: HealthStatus(component="c2", healthy=False))
        results = self.diag.check_all()
        assert len(results) == 2
        assert results["c1"].healthy is True
        assert results["c2"].healthy is False

    def test_health_summary(self):
        from prototype.diagnostics.diagnostics import HealthStatus
        self.diag.register_health_check(
            "c1", lambda: HealthStatus(component="c1", healthy=True))
        self.diag.check_all()
        summary = self.diag.get_health_summary()
        assert summary["total_components"] == 1
        assert summary["healthy"] == 1
        assert summary["overall"] is True

    def test_system_info(self):
        info = self.diag.get_system_info()
        assert "uptime_seconds" in info
        assert info["uptime_seconds"] >= 0

    def test_stats(self):
        self.diag.record("m1", 1.0)
        self.diag.increment("c1")
        self.diag.gauge("g1", 1.0)
        stats = self.diag.get_stats()
        assert stats["total_metrics"] == 1
        assert "m1" in stats["metric_names"]
        assert "c1" in stats["counter_names"]
        assert "g1" in stats["gauge_names"]

    def test_clear(self):
        self.diag.record("m1", 1.0)
        self.diag.increment("c1")
        self.diag.clear()
        assert self.diag.get_metric_history("m1") == []
        assert self.diag.get_counter("c1") == 0


# ═══════════════════════════════════════════════════════════════════════════════
#  API Contracts — new types
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewAPIContracts(unittest.TestCase):
    def test_agent_run_request(self):
        from prototype.api.contracts import AgentRunRequest
        req = AgentRunRequest(agent_id="a1", goal="test")
        assert req.agent_id == "a1"
        assert req.goal == "test"

    def test_agent_multi_request(self):
        from prototype.api.contracts import AgentMultiRequest
        req = AgentMultiRequest(agent_ids=["a1", "a2"], goal="test", pattern="parallel")
        assert len(req.agent_ids) == 2
        assert req.pattern == "parallel"

    def test_agent_plan_request(self):
        from prototype.api.contracts import AgentPlanRequest
        req = AgentPlanRequest(goal="plan this")
        assert req.goal == "plan this"
        assert req.available_tools is None

    def test_agent_api_is_abstract(self):
        from prototype.api.contracts import AgentAPI
        with self.assertRaises(TypeError):
            AgentAPI()

    def test_diagnostics_api_is_abstract(self):
        from prototype.api.contracts import DiagnosticsAPI
        with self.assertRaises(TypeError):
            DiagnosticsAPI()

    def test_service_registry_api_is_abstract(self):
        from prototype.api.contracts import ServiceRegistryAPI
        with self.assertRaises(TypeError):
            ServiceRegistryAPI()


# ═══════════════════════════════════════════════════════════════════════════════
#  AlfaRuntime Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlfaRuntimeNewModules(unittest.TestCase):
    def setUp(self):
        from prototype.runtime.alfa_runtime import AlfaRuntime
        from prototype.config import SettingsManager
        self.settings = SettingsManager()
        self.settings.set_provider("mock")
        self.runtime = AlfaRuntime(settings=self.settings)
        self.runtime.load()

    def tearDown(self):
        self.runtime.shutdown()

    def test_agent_runtime_wired(self):
        assert self.runtime.agent_runtime is not None
        assert self.runtime.agent_runtime.is_loaded()

    def test_service_registry_wired(self):
        assert self.runtime.service_registry is not None
        services = self.runtime.service_registry.list_services()
        assert len(services) >= 7  # kernel, memory, provider, tools, plugins, workers, agents

    def test_diagnostics_wired(self):
        assert self.runtime.diagnostics is not None

    def test_stats_includes_new_modules(self):
        stats = self.runtime.get_stats()
        assert "agents" in stats
        assert "services" in stats
        assert "diagnostics" in stats

    def test_process_records_diagnostics(self):
        result = self.runtime.process("hello")
        assert result.success
        counter = self.runtime.diagnostics.get_counter("kernel.process_count")
        assert counter >= 1


if __name__ == "__main__":
    unittest.main()
