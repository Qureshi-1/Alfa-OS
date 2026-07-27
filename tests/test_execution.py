"""Tests for Execution Runtime — all 7 modules."""

import time
import unittest
from prototype.common import Event, EventBus


# ═══════════════════════════════════════════════════════════════════════════════
#  ExecutionContext
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionContext(unittest.TestCase):
    def setUp(self):
        from prototype.execution.execution_context import (
            ExecutionContext, ExecutionMode, RetryConfig, RollbackConfig,
        )
        self.Ctx = ExecutionContext
        self.Mode = ExecutionMode
        self.Retry = RetryConfig
        self.Rollback = RollbackConfig

    def test_create_default(self):
        ctx = self.Ctx()
        assert ctx.task_id
        assert ctx.action == ""
        assert ctx.parameters == {}
        assert ctx.dependencies == []
        assert ctx.timeout_seconds == 30.0
        assert ctx.retry.max_retries == 0
        assert ctx.rollback.enabled is False

    def test_create_with_params(self):
        ctx = self.Ctx(
            action="run_task", parameters={"key": "val"},
            dependencies=["dep1"], timeout_seconds=60.0,
            priority=5, handler_type="tool", handler_name="my_tool",
        )
        assert ctx.action == "run_task"
        assert ctx.parameters == {"key": "val"}
        assert ctx.dependencies == ["dep1"]
        assert ctx.timeout_seconds == 60.0
        assert ctx.priority == 5
        assert ctx.handler_type == "tool"
        assert ctx.handler_name == "my_tool"

    def test_retry_config(self):
        r = self.Retry(max_retries=3, backoff_seconds=2.0, retry_on=["timeout", "error"])
        assert r.max_retries == 3
        assert r.backoff_seconds == 2.0
        assert r.retry_on == ["timeout", "error"]

    def test_rollback_config(self):
        rb = self.Rollback(enabled=True, handler_name="undo", parameters={"x": 1})
        assert rb.enabled is True
        assert rb.handler_name == "undo"
        assert rb.parameters == {"x": 1}

    def test_execution_mode_values(self):
        assert self.Mode.SEQUENTIAL.value == "sequential"
        assert self.Mode.PARALLEL.value == "parallel"
        assert self.Mode.PIPELINE.value == "pipeline"
        assert self.Mode.DEPENDENCY_AWARE.value == "dependency_aware"

    def test_created_at_populated(self):
        ctx = self.Ctx()
        assert ctx.created_at > 0


# ═══════════════════════════════════════════════════════════════════════════════
#  ExecutionResult
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionResult(unittest.TestCase):
    def setUp(self):
        from prototype.execution.execution_result import (
            TaskExecutionResult, ExecutionPlanResult, TaskStatus,
        )
        self.TR = TaskExecutionResult
        self.PR = ExecutionPlanResult
        self.S = TaskStatus

    def test_task_result_success(self):
        r = self.TR(task_id="t1", status=self.S.COMPLETED, output="ok")
        assert r.success is True

    def test_task_result_failure(self):
        r = self.TR(task_id="t1", status=self.S.FAILED, error="boom")
        assert r.success is False

    def test_task_result_default_pending(self):
        r = self.TR()
        assert r.status == self.S.PENDING
        assert r.success is False

    def test_plan_result_all_success(self):
        r1 = self.TR(status=self.S.COMPLETED)
        r2 = self.TR(status=self.S.COMPLETED)
        pr = self.PR(task_results=[r1, r2])
        assert pr.success is True

    def test_plan_result_has_failure(self):
        r1 = self.TR(status=self.S.COMPLETED)
        r2 = self.TR(status=self.S.FAILED)
        pr = self.PR(task_results=[r1, r2])
        assert pr.success is False

    def test_plan_result_empty(self):
        pr = self.PR()
        assert pr.success is True  # vacuously true

    def test_plan_failed_tasks(self):
        r1 = self.TR(status=self.S.COMPLETED)
        r2 = self.TR(status=self.S.FAILED)
        r3 = self.TR(status=self.S.FAILED)
        pr = self.PR(task_results=[r1, r2, r3])
        assert len(pr.failed_tasks) == 2
        assert len(pr.succeeded_tasks) == 1

    def test_plan_output_last(self):
        r1 = self.TR(output="first")
        r2 = self.TR(output="second")
        pr = self.PR(task_results=[r1, r2])
        assert pr.output == "second"

    def test_plan_output_empty(self):
        pr = self.PR()
        assert pr.output is None


# ═══════════════════════════════════════════════════════════════════════════════
#  ExecutionHistory
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionHistory(unittest.TestCase):
    def setUp(self):
        from prototype.execution.execution_history import ExecutionHistory
        from prototype.execution.execution_result import TaskExecutionResult, TaskStatus
        self.H = ExecutionHistory
        self.TR = TaskExecutionResult
        self.S = TaskStatus

    def test_add_and_get_recent(self):
        h = self.H()
        h.add_record(self.TR(task_id="t1", action="a1", status=self.S.COMPLETED))
        h.add_record(self.TR(task_id="t2", action="a2", status=self.S.FAILED))
        recent = h.get_recent()
        assert len(recent) == 2

    def test_get_task_history(self):
        h = self.H()
        h.add_record(self.TR(task_id="t1", action="a1"))
        h.add_record(self.TR(task_id="t2", action="a2"))
        h.add_record(self.TR(task_id="t1", action="a3"))
        history = h.get_task_history("t1")
        assert len(history) == 2

    def test_get_action_history(self):
        h = self.H()
        h.add_record(self.TR(task_id="t1", action="deploy"))
        h.add_record(self.TR(task_id="t2", action="build"))
        h.add_record(self.TR(task_id="t3", action="deploy"))
        history = h.get_action_history("deploy")
        assert len(history) == 2

    def test_get_failed(self):
        h = self.H()
        h.add_record(self.TR(status=self.S.COMPLETED))
        h.add_record(self.TR(status=self.S.FAILED))
        assert len(h.get_failed()) == 1

    def test_get_successful(self):
        h = self.H()
        h.add_record(self.TR(status=self.S.COMPLETED))
        h.add_record(self.TR(status=self.S.FAILED))
        assert len(h.get_successful()) == 1

    def test_query_by_status(self):
        h = self.H()
        h.add_record(self.TR(status=self.S.COMPLETED))
        h.add_record(self.TR(status=self.S.FAILED))
        h.add_record(self.TR(status=self.S.COMPLETED))
        results = h.query(status=self.S.COMPLETED)
        assert len(results) == 2

    def test_query_by_handler_type(self):
        h = self.H()
        h.add_record(self.TR(handler_type="tool"))
        h.add_record(self.TR(handler_type="agent"))
        results = h.query(handler_type="tool")
        assert len(results) == 1

    def test_max_records(self):
        h = self.H(max_records=3)
        for i in range(5):
            h.add_record(self.TR(task_id=f"t{i}"))
        assert len(h.get_recent()) == 3

    def test_stats(self):
        h = self.H()
        h.add_record(self.TR(status=self.S.COMPLETED, execution_time_ms=100))
        h.add_record(self.TR(status=self.S.FAILED, execution_time_ms=200))
        stats = h.get_stats()
        assert stats["total"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["avg_time_ms"] == 150.0

    def test_stats_empty(self):
        h = self.H()
        stats = h.get_stats()
        assert stats["total"] == 0
        assert stats["avg_time_ms"] == 0.0

    def test_clear(self):
        h = self.H()
        h.add_record(self.TR())
        h.clear()
        assert len(h.get_recent()) == 0


# ═══════════════════════════════════════════════════════════════════════════════
#  ExecutionScheduler
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionScheduler(unittest.TestCase):
    def setUp(self):
        from prototype.execution.execution_scheduler import ExecutionScheduler
        from prototype.execution.execution_context import ExecutionContext, ExecutionMode
        self.S = ExecutionScheduler
        self.Ctx = ExecutionContext
        self.Mode = ExecutionMode

    def test_empty_scheduler(self):
        s = self.S()
        order = s.get_execution_order(self.Mode.DEPENDENCY_AWARE)
        assert order == []

    def test_no_dependencies(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b"))
        order = s.get_execution_order(self.Mode.DEPENDENCY_AWARE)
        flat = [tid for batch in order for tid in batch]
        assert set(flat) == {"a", "b"}

    def test_linear_dependency(self):
        s = self.S()
        a = self.Ctx(task_id="a")
        b = self.Ctx(task_id="b", dependencies=["a"])
        c = self.Ctx(task_id="c", dependencies=["b"])
        s.register(a)
        s.register(b)
        s.register(c)
        order = s.get_execution_order(self.Mode.DEPENDENCY_AWARE)
        flat = [tid for batch in order for tid in batch]
        assert flat.index("a") < flat.index("b") < flat.index("c")

    def test_diamond_dependency(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        s.register(self.Ctx(task_id="c", dependencies=["a"]))
        s.register(self.Ctx(task_id="d", dependencies=["b", "c"]))
        order = s.get_execution_order(self.Mode.DEPENDENCY_AWARE)
        flat = [tid for batch in order for tid in batch]
        assert flat.index("a") < flat.index("b")
        assert flat.index("a") < flat.index("c")
        assert flat.index("b") < flat.index("d")
        assert flat.index("c") < flat.index("d")

    def test_parallel_mode(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        order = s.get_execution_order(self.Mode.PARALLEL)
        assert len(order) == 1
        assert set(order[0]) == {"a", "b"}

    def test_sequential_mode(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        order = s.get_execution_order(self.Mode.SEQUENTIAL)
        flat = [tid for batch in order for tid in batch]
        assert flat.index("a") < flat.index("b")
        assert all(len(batch) == 1 for batch in order)

    def test_pipeline_mode(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        s.register(self.Ctx(task_id="c", dependencies=["b"]))
        order = s.get_execution_order(self.Mode.PIPELINE)
        assert len(order) == 3  # 3 depth levels

    def test_validate_unknown_dependency(self):
        s = self.S()
        s.register(self.Ctx(task_id="a", dependencies=["missing"]))
        errors = s.validate_dependencies()
        assert len(errors) == 1
        assert "missing" in errors[0]

    def test_validate_cycle(self):
        s = self.S()
        s.register(self.Ctx(task_id="a", dependencies=["b"]))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        errors = s.validate_dependencies()
        assert any("cycle" in e.lower() for e in errors)

    def test_validate_clean(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.register(self.Ctx(task_id="b", dependencies=["a"]))
        errors = s.validate_dependencies()
        assert errors == []

    def test_unregister(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        assert s.unregister("a") is True
        assert s.unregister("a") is False

    def test_clear(self):
        s = self.S()
        s.register(self.Ctx(task_id="a"))
        s.clear()
        assert s.get_execution_order() == []

    def test_get_context(self):
        s = self.S()
        ctx = self.Ctx(task_id="a", action="test")
        s.register(ctx)
        assert s.get_context("a") is ctx
        assert s.get_context("missing") is None


# ═══════════════════════════════════════════════════════════════════════════════
#  ToolRouter
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolRouter(unittest.TestCase):
    def setUp(self):
        from prototype.execution.tool_router import ToolRouter
        self.R = ToolRouter

    def test_register_and_route_tool(self):
        r = self.R()
        r.register_tool("echo", lambda p: p)
        result = r.route("tool", "echo", {"x": 1})
        assert result == {"x": 1}

    def test_register_and_route_agent(self):
        r = self.R()
        r.register_agent("planner", lambda p: "planned")
        result = r.route("agent", "planner", {})
        assert result == "planned"

    def test_register_and_route_worker(self):
        r = self.R()
        r.register_worker("echo_worker", lambda p: "echoed")
        result = r.route("worker", "echo_worker", {})
        assert result == "echoed"

    def test_register_cognition(self):
        r = self.R()
        r.register_cognition(lambda p: "cog_output")
        result = r.route("cognition", "any", {})
        assert result == "cog_output"

    def test_route_unknown_raises(self):
        r = self.R()
        with self.assertRaises(ValueError):
            r.route("tool", "nonexistent", {})

    def test_has_handler(self):
        r = self.R()
        r.register_tool("t1", lambda p: None)
        assert r.has_handler("tool", "t1") is True
        assert r.has_handler("tool", "t2") is False
        assert r.has_handler("agent", "t1") is False

    def test_unregister(self):
        r = self.R()
        r.register_tool("t1", lambda p: None)
        assert r.unregister_tool("t1") is True
        assert r.unregister_tool("t1") is False

    def test_unregister_agent(self):
        r = self.R()
        r.register_agent("a1", lambda p: None)
        assert r.unregister_agent("a1") is True

    def test_unregister_worker(self):
        r = self.R()
        r.register_worker("w1", lambda p: None)
        assert r.unregister_worker("w1") is True

    def test_get_handler_names(self):
        r = self.R()
        r.register_tool("t1", lambda p: None)
        r.register_tool("t2", lambda p: None)
        assert set(r.get_handler_names("tool")) == {"t1", "t2"}

    def test_clear(self):
        r = self.R()
        r.register_tool("t1", lambda p: None)
        r.register_agent("a1", lambda p: None)
        r.clear()
        assert r.get_handler_names("tool") == []
        assert r.get_handler_names("agent") == []

    def test_route_type_mismatch(self):
        r = self.R()
        r.register_tool("t1", lambda p: None)
        with self.assertRaises(ValueError):
            r.route("agent", "t1", {})


# ═══════════════════════════════════════════════════════════════════════════════
#  TaskExecutor
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskExecutor(unittest.TestCase):
    def setUp(self):
        from prototype.execution.task_executor import TaskExecutor
        from prototype.execution.tool_router import ToolRouter
        from prototype.execution.execution_context import ExecutionContext, RetryConfig, RollbackConfig
        from prototype.execution.execution_result import TaskStatus
        from prototype.common import EventBus
        self.E = TaskExecutor
        self.R = ToolRouter
        self.Ctx = ExecutionContext
        self.Retry = RetryConfig
        self.Rollback = RollbackConfig
        self.S = TaskStatus
        self.bus = EventBus()

    def test_execute_success(self):
        router = self.R()
        router.register_tool("add", lambda p: p.get("a", 0) + p.get("b", 0))
        ex = self.E(router, event_bus=self.bus)
        ctx = self.Ctx(action="add", parameters={"a": 2, "b": 3}, handler_type="tool", handler_name="add")
        result = ex.execute(ctx)
        assert result.success is True
        assert result.output == 5

    def test_execute_failure(self):
        router = self.R()
        router.register_tool("fail", lambda p: 1 / 0)
        ex = self.E(router)
        ctx = self.Ctx(action="fail", handler_type="tool", handler_name="fail")
        result = ex.execute(ctx)
        assert result.success is False
        assert "division" in result.error.lower() or "zero" in result.error.lower()

    def test_execute_no_handler(self):
        router = self.R()
        ex = self.E(router)
        ctx = self.Ctx(action="missing", handler_type="tool", handler_name="missing")
        result = ex.execute(ctx)
        assert result.success is False

    def test_retry_success(self):
        router = self.R()
        call_count = [0]
        def flaky(p):
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("transient error")
            return "ok"
        router.register_tool("flaky", flaky)
        ex = self.E(router)
        ctx = self.Ctx(
            action="flaky", handler_type="tool", handler_name="flaky",
            retry=self.Retry(max_retries=3, backoff_seconds=0.0, retry_on=[]),
        )
        result = ex.execute(ctx)
        assert result.success is True
        assert result.retry_count == 2

    def test_retry_exhausted(self):
        router = self.R()
        router.register_tool("always_fail", lambda p: (_ for _ in ()).throw(RuntimeError("permanent")))
        ex = self.E(router)
        ctx = self.Ctx(
            action="always_fail", handler_type="tool", handler_name="always_fail",
            retry=self.Retry(max_retries=2, backoff_seconds=0.0, retry_on=[]),
        )
        result = ex.execute(ctx)
        assert result.success is False
        assert result.retry_count == 2

    def test_retry_filtered(self):
        router = self.R()
        router.register_tool("filter", lambda p: (_ for _ in ()).throw(ValueError("wrong type")))
        ex = self.E(router)
        ctx = self.Ctx(
            action="filter", handler_type="tool", handler_name="filter",
            retry=self.Retry(max_retries=3, backoff_seconds=0.0, retry_on=["timeout"]),
        )
        result = ex.execute(ctx)
        assert result.retry_count == 0  # shouldn't retry

    def test_cancel(self):
        router = self.R()
        call_count = [0]
        def slow(p):
            call_count[0] += 1
            if call_count[0] == 1:
                import time; time.sleep(0.01)
                raise RuntimeError("first")
            return "ok"
        router.register_tool("slow", slow)
        ex = self.E(router)
        ctx = self.Ctx(
            action="slow", handler_type="tool", handler_name="slow",
            retry=self.Retry(max_retries=5, backoff_seconds=0.0, retry_on=[]),
        )
        ex.cancel(ctx.task_id)
        result = ex.execute(ctx)
        assert result.status == self.S.CANCELLED

    def test_rollback(self):
        router = self.R()
        router.register_tool("deploy", lambda p: (_ for _ in ()).throw(RuntimeError("deploy failed")))
        ex = self.E(router)
        rollback_called = [False]
        def rollback_handler(p):
            rollback_called[0] = True
        ex.register_rollback("deploy", rollback_handler)
        ctx = self.Ctx(
            action="deploy", handler_type="tool", handler_name="deploy",
            rollback=self.Rollback(enabled=True),
        )
        result = ex.execute(ctx)
        assert result.success is False
        assert result.rollback_success is True
        assert rollback_called[0] is True

    def test_rollback_disabled(self):
        router = self.R()
        router.register_tool("deploy", lambda p: (_ for _ in ()).throw(RuntimeError("fail")))
        ex = self.E(router)
        ctx = self.Ctx(
            action="deploy", handler_type="tool", handler_name="deploy",
            rollback=self.Rollback(enabled=False),
        )
        result = ex.execute(ctx)
        assert result.rollback_success is None

    def test_events_emitted(self):
        router = self.R()
        router.register_tool("echo", lambda p: "done")
        ex = self.E(router, event_bus=self.bus)
        ctx = self.Ctx(action="echo", handler_type="tool", handler_name="echo")
        ex.execute(ctx)
        events = self.bus.get_history()
        types = [e.event_type for e in events]
        assert "StepStarted" in types
        assert "StepCompleted" in types


# ═══════════════════════════════════════════════════════════════════════════════
#  ExecutionRuntime
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionRuntime(unittest.TestCase):
    def setUp(self):
        from prototype.execution.execution_runtime import ExecutionRuntime
        from prototype.execution.execution_context import ExecutionContext, ExecutionMode
        from prototype.common import EventBus
        self.R = ExecutionRuntime
        self.Ctx = ExecutionContext
        self.Mode = ExecutionMode
        self.bus = EventBus()

    def test_load_shutdown(self):
        r = self.R(event_bus=self.bus)
        r.load()
        assert r.is_loaded() is True
        r.shutdown()
        assert r.is_loaded() is False

    def test_double_load(self):
        r = self.R()
        r.load()
        r.load()  # no-op
        assert r.is_loaded() is True
        r.shutdown()

    def test_shutdown_when_not_loaded(self):
        r = self.R()
        r.shutdown()  # no-op

    def test_execute_task(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("echo", lambda p: p)
        r.load()
        ctx = self.Ctx(action="echo", parameters={"msg": "hi"}, handler_type="tool", handler_name="echo")
        result = r.execute_task(ctx)
        assert result.success is True
        assert result.output == {"msg": "hi"}
        r.shutdown()

    def test_execute_task_not_loaded(self):
        r = self.R()
        with self.assertRaises(RuntimeError):
            r.execute_task(self.Ctx())

    def test_cancel_task(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("slow", lambda p: (_ for _ in ()).throw(RuntimeError("err")))
        r.load()
        ctx = self.Ctx(
            action="slow", handler_type="tool", handler_name="slow",
            retry={"max_retries": 5, "backoff_seconds": 0.0, "retry_on": []},
        )
        # Cancel before execute triggers
        r._active[ctx.task_id] = True
        result = r.cancel_task(ctx.task_id)
        assert result is True
        r.shutdown()

    def test_cancel_nonexistent(self):
        r = self.R()
        r.load()
        assert r.cancel_task("missing") is False
        r.shutdown()

    def test_execute_batch(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("op", lambda p: p.get("val", 0))
        r.load()
        contexts = [
            self.Ctx(task_id="a", action="op", parameters={"val": 1}, handler_type="tool", handler_name="op"),
            self.Ctx(task_id="b", action="op", parameters={"val": 2}, handler_type="tool", handler_name="op"),
        ]
        result = r.execute_batch(contexts, self.Mode.PARALLEL)
        assert result.success is True
        assert len(result.task_results) == 2
        r.shutdown()

    def test_execute_batch_dependency_error(self):
        r = self.R()
        r.load()
        contexts = [
            self.Ctx(task_id="a", action="op", dependencies=["missing"], handler_type="tool", handler_name="op"),
        ]
        result = r.execute_batch(contexts, self.Mode.DEPENDENCY_AWARE)
        assert result.success is False
        r.shutdown()

    def test_history_populated(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("t", lambda p: "ok")
        r.load()
        ctx = self.Ctx(action="t", handler_type="tool", handler_name="t")
        r.execute_task(ctx)
        history = r.get_history()
        assert len(history.get_recent()) == 1
        r.shutdown()

    def test_stats(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("t", lambda p: "ok")
        r.load()
        ctx = self.Ctx(action="t", handler_type="tool", handler_name="t")
        r.execute_task(ctx)
        stats = r.get_stats()
        assert stats["execution_count"] == 1
        assert stats["history"]["total"] == 1
        r.shutdown()

    def test_events_emitted(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("t", lambda p: "ok")
        r.load()
        ctx = self.Ctx(action="t", handler_type="tool", handler_name="t")
        r.execute_task(ctx)
        events = self.bus.get_history()
        types = [e.event_type for e in events]
        assert "ExecutionStarted" in types
        assert "ExecutionRuntimeStarted" in types
        r.shutdown()

    def test_register_rollback(self):
        r = self.R()
        r.load()
        r.register_rollback("deploy", lambda p: "rolled back")
        r.shutdown()

    def test_health_check(self):
        r = self.R()
        r.load()
        check = r._health_check()
        assert check.healthy is True
        r.shutdown()

    def test_health_check_not_loaded(self):
        r = self.R()
        check = r._health_check()
        assert check.healthy is False

    def test_linear_dependency_batch(self):
        r = self.R(event_bus=self.bus)
        r.register_tool("op", lambda p: p.get("val", 0))
        r.load()
        contexts = [
            self.Ctx(task_id="a", action="op", parameters={"val": 1}, handler_type="tool", handler_name="op"),
            self.Ctx(task_id="b", action="op", parameters={"val": 2}, dependencies=["a"], handler_type="tool", handler_name="op"),
            self.Ctx(task_id="c", action="op", parameters={"val": 3}, dependencies=["b"], handler_type="tool", handler_name="op"),
        ]
        result = r.execute_batch(contexts, self.Mode.SEQUENTIAL)
        assert result.success is True
        flat = [tr.task_id for tr in result.task_results]
        assert flat == ["a", "b", "c"]
        r.shutdown()

    def test_batch_stops_on_failure_sequential(self):
        r = self.R(event_bus=self.bus)
        call_count = [0]
        def sometimes_fail(p):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("fail on second")
            return "ok"
        r.register_tool("op", sometimes_fail)
        r.load()
        contexts = [
            self.Ctx(task_id="a", action="op", handler_type="tool", handler_name="op"),
            self.Ctx(task_id="b", action="op", handler_type="tool", handler_name="op"),
            self.Ctx(task_id="c", action="op", handler_type="tool", handler_name="op"),
        ]
        result = r.execute_batch(contexts, self.Mode.SEQUENTIAL)
        assert result.success is False
        assert len(result.task_results) == 2  # stopped after b
        r.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration: ExecutionRuntime + MissionRuntime
# ═══════════════════════════════════════════════════════════════════════════════

class TestExecutionMissionIntegration(unittest.TestCase):
    def test_execute_mission_tasks(self):
        from prototype.execution.execution_runtime import ExecutionRuntime
        from prototype.execution.execution_context import ExecutionContext, ExecutionMode
        from prototype.mission.mission_runtime import MissionRuntime
        from prototype.mission.task_graph import TaskStatus
        from prototype.common import EventBus

        bus = EventBus()
        mission = MissionRuntime(event_bus=bus)
        mission.load()

        exec_rt = ExecutionRuntime(event_bus=bus, mission_runtime=mission)
        exec_rt.register_tool("echo", lambda p: p)
        exec_rt.load()

        # Create mission with tasks
        m = mission.create_mission("test", "test mission")
        mission.activate_mission(m.id)

        t1 = mission.add_task(m.id, "step1", action="echo", parameters={"v": 1})
        t2 = mission.add_task(m.id, "step2", action="echo", parameters={"v": 2}, dependencies=[t1.id])

        result = exec_rt.execute_mission_tasks(m.id, ExecutionMode.SEQUENTIAL)
        assert result.success is True
        assert len(result.task_results) == 2

        exec_rt.shutdown()
        mission.shutdown()

    def test_execute_mission_no_graph(self):
        from prototype.execution.execution_runtime import ExecutionRuntime
        from prototype.mission.mission_runtime import MissionRuntime
        from prototype.common import EventBus

        mission = MissionRuntime(event_bus=EventBus())
        mission.load()
        exec_rt = ExecutionRuntime(mission_runtime=mission)
        exec_rt.load()

        result = exec_rt.execute_mission_tasks("nonexistent")
        assert len(result.task_results) == 0

        exec_rt.shutdown()
        mission.shutdown()


if __name__ == "__main__":
    unittest.main()
