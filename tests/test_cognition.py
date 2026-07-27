"""Tests for the Cognition Engine — perception, planner, reasoner, executor, reflector, runtime."""

import unittest
from unittest.mock import MagicMock
from prototype.common import Event, EventBus, EngineResult


# ═══════════════════════════════════════════════════════════════════════════════
#  Perception Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerceptionEngine(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.perception import PerceptionEngine
        self.bus = EventBus()
        self.engine = PerceptionEngine(event_bus=self.bus)
        self.engine.load()

    def tearDown(self):
        pass

    def test_load_and_lifecycle(self):
        assert self.engine.is_loaded()
        assert self.engine.load() is None  # idempotent

    def test_process_query(self):
        result = self.engine.process("What is the weather today?")
        assert result.raw_input == "What is the weather today?"
        assert len(result.intents) > 0
        assert result.intents[0]["name"] == "query"
        assert result.confidence > 0
        assert result.latency_ms >= 0

    def test_process_command(self):
        result = self.engine.process("Run the test suite")
        assert any(i["name"] == "command" for i in result.intents)

    def test_process_conversation(self):
        result = self.engine.process("Hello, how are you?")
        assert any(i["name"] in ("conversation", "query") for i in result.intents)

    def test_process_analysis(self):
        result = self.engine.process("Analyze the performance data")
        assert any(i["name"] == "analysis" for i in result.intents)

    def test_process_generation(self):
        result = self.engine.process("Generate a report")
        assert any(i["name"] == "generation" for i in result.intents)

    def test_entity_extraction(self):
        result = self.engine.process("What is 42 plus 58?")
        assert "number" in result.entities

    def test_feature_extraction(self):
        result = self.engine.process("Hello?")
        assert result.features["has_question"] is True
        assert result.features["word_count"] == 1

    def test_empty_input(self):
        result = self.engine.process("")
        assert result.raw_input == ""
        assert isinstance(result.intents, list)

    def test_normalization(self):
        result = self.engine.process("  Hello   World  ")
        assert result.normalized_input == "hello world"

    def test_plugin_registration(self):
        from prototype.cognition.perception import PerceptionPlugin
        plugin = PerceptionPlugin()
        self.engine.register_plugin(plugin)
        assert plugin in self.engine._plugins
        assert self.engine.unregister_plugin(plugin)
        assert plugin not in self.engine._plugins

    def test_plugin_pre_process(self):
        from prototype.cognition.perception import PerceptionPlugin
        class UpperPlugin(PerceptionPlugin):
            def pre_process(self, raw_input, context):
                return raw_input.upper()
        plugin = UpperPlugin()
        self.engine.register_plugin(plugin)
        result = self.engine.process("hello world")
        assert result.raw_input == "hello world"
        # normalization lowercases, so plugin output is also lowered
        assert "hello world" in result.normalized_input

    def test_plugin_post_process(self):
        from prototype.cognition.perception import PerceptionPlugin, PerceptionResult
        class TagPlugin(PerceptionPlugin):
            def post_process(self, result, context):
                result.metadata["tagged"] = True
                return result
        plugin = TagPlugin()
        self.engine.register_plugin(plugin)
        result = self.engine.process("test input")
        assert result.metadata.get("tagged") is True

    def test_plugin_detect_intents_override(self):
        from prototype.cognition.perception import PerceptionPlugin
        class CustomIntentPlugin(PerceptionPlugin):
            def detect_intents(self, normalized, context):
                return [{"name": "custom_intent", "confidence": 1.0, "method": "plugin"}]
        plugin = CustomIntentPlugin()
        self.engine.register_plugin(plugin)
        result = self.engine.process("anything")
        assert result.intents[0]["name"] == "custom_intent"

    def test_event_emission(self):
        received = []
        self.bus.subscribe("PerceptionStarted", lambda e: received.append(e))
        self.bus.subscribe("PerceptionProcessed", lambda e: received.append(e))
        self.engine.process("test")
        assert len(received) == 2
        assert received[0].event_type == "PerceptionStarted"
        assert received[1].event_type == "PerceptionProcessed"

    def test_context_signals(self):
        result = self.engine.process("test", context={"source": "test"})
        assert result.context_signals.get("source") == "test"


# ═══════════════════════════════════════════════════════════════════════════════
#  Task Planner
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaskPlanner(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.planner import TaskPlanner
        self.bus = EventBus()
        self.planner = TaskPlanner(event_bus=self.bus)
        self.planner.load()

    def test_load_and_lifecycle(self):
        assert self.planner.is_loaded()
        assert self.planner.load() is None  # idempotent

    def test_create_plan_query(self):
        intents = [{"name": "query", "confidence": 0.8}]
        plan = self.planner.create_plan("What is AI?", intents)
        assert plan.goal == "What is AI?"
        assert len(plan.steps) > 0
        assert plan.status == "ready"
        assert plan.latency_ms >= 0

    def test_create_plan_command(self):
        intents = [{"name": "command", "confidence": 0.9}]
        plan = self.planner.create_plan("Run the tests", intents)
        assert any(s.action == "execute" for s in plan.steps)

    def test_create_plan_analysis(self):
        intents = [{"name": "analysis", "confidence": 0.85}]
        plan = self.planner.create_plan("Analyze code", intents)
        assert any(s.action == "analyze" for s in plan.steps)

    def test_create_plan_generation(self):
        intents = [{"name": "generation", "confidence": 0.9}]
        plan = self.planner.create_plan("Write a function", intents)
        assert any(s.action == "generate" for s in plan.steps)

    def test_create_plan_generic(self):
        intents = [{"name": "unknown_intent", "confidence": 0.5}]
        plan = self.planner.create_plan("do something", intents)
        assert len(plan.steps) > 0

    def test_task_plan_properties(self):
        from prototype.cognition.planner import TaskPlan, TaskStep
        step1 = TaskStep(name="a", status="completed")
        step2 = TaskStep(name="b", status="pending", dependencies=[step1.id])
        plan = TaskPlan(steps=[step1, step2])
        assert not plan.is_complete
        assert len(plan.pending_steps) == 1
        assert len(plan.completed_steps) == 1
        # step1 is completed, step2 depends on step1, so step2 should be ready
        ready = plan.next_ready()
        assert ready is not None
        assert ready.name == "b"

    def test_replan(self):
        from prototype.cognition.planner import TaskPlan, TaskStep
        step1 = TaskStep(name="a")
        step2 = TaskStep(name="b", dependencies=[step1.id])
        step3 = TaskStep(name="c", dependencies=[step2.id])
        plan = TaskPlan(steps=[step1, step2, step3])
        plan = self.planner.replan(plan, step1, "tool not found")
        assert step2.status == "skipped"
        # step3 depends on step2, not step1 — replan only skips direct dependents
        assert step3.status == "pending"
        assert plan.status == "replanned"

    def test_plugin_registration(self):
        from prototype.cognition.planner import TaskPlannerPlugin
        plugin = TaskPlannerPlugin()
        self.planner.register_plugin(plugin)
        assert plugin in self.planner._plugins
        assert self.planner.unregister_plugin(plugin)

    def test_plugin_custom_plan(self):
        from prototype.cognition.planner import TaskPlannerPlugin, TaskPlan, TaskStep
        class CustomPlanner(TaskPlannerPlugin):
            def should_handle(self, intents, context):
                return any(i["name"] == "custom" for i in intents)
            def create_plan(self, goal, intents, entities, context):
                return TaskPlan(goal=goal, steps=[TaskStep(name="custom_step")])
        plugin = CustomPlanner()
        self.planner.register_plugin(plugin)
        plan = self.planner.create_plan("test", [{"name": "custom", "confidence": 1.0}])
        assert len(plan.steps) == 1
        assert plan.steps[0].name == "custom_step"

    def test_event_emission(self):
        received = []
        self.bus.subscribe("PlanStarted", lambda e: received.append(e))
        self.bus.subscribe("PlanCreated", lambda e: received.append(e))
        self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        assert len(received) == 2

    def test_estimated_cost(self):
        intents = [{"name": "command", "confidence": 0.9}]
        plan = self.planner.create_plan("run something", intents)
        assert plan.estimated_total_cost >= 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Reasoner
# ═══════════════════════════════════════════════════════════════════════════════

class TestReasoner(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.reasoner import Reasoner
        from prototype.cognition.planner import TaskPlanner, TaskPlan, TaskStep
        self.bus = EventBus()
        self.reasoner = Reasoner(event_bus=self.bus)
        self.reasoner.load()
        self.planner = TaskPlanner(event_bus=self.bus)
        self.planner.load()

    def test_load_and_lifecycle(self):
        assert self.reasoner.is_loaded()
        assert self.reasoner.load() is None

    def test_register_tool(self):
        self.reasoner.register_tool("calculator", ["compute", "math"])
        assert "calculator" in self.reasoner._tool_registry

    def test_register_agent(self):
        self.reasoner.register_agent("code_agent", ["code", "write"])
        assert "code_agent" in self.reasoner._agent_registry

    def test_register_worker(self):
        self.reasoner.register_worker("bg_worker", ["background", "task"])
        assert "bg_worker" in self.reasoner._worker_registry

    def test_reason_with_tools(self):
        self.reasoner.register_tool("memory_search", ["memory_recall", "search"])
        self.reasoner.register_tool("responder", ["respond", "generate"])
        plan = self.planner.create_plan("What is AI?", [{"name": "query", "confidence": 0.8}])
        result = self.reasoner.reason(plan)
        assert result.plan_id == plan.id
        assert len(result.selections) > 0
        assert result.confidence > 0

    def test_reason_no_candidates(self):
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        result = self.reasoner.reason(plan)
        assert result.plan_id == plan.id
        assert len(result.selections) == 0

    def test_reason_explicit_requirement(self):
        from prototype.cognition.planner import TaskStep
        self.reasoner.register_tool("special_tool", ["special"])
        step = TaskStep(name="special", action="do_special", requires_tool="special_tool")
        plan = self.planner.create_plan("test", [{"name": "command", "confidence": 0.9}])
        plan.steps = [step]
        result = self.reasoner.reason(plan)
        assert "special_tool" in [s.name for s in result.selections.values()]

    def test_strategy_determination(self):
        from prototype.cognition.planner import TaskStep
        # Steps with no dependencies -> parallel
        plan_steps = [
            TaskStep(name="a", action="do_a"),
            TaskStep(name="b", action="do_b"),
        ]
        from prototype.cognition.planner import TaskPlan
        plan = TaskPlan(goal="test", steps=plan_steps)
        result = self.reasoner.reason(plan)
        assert result.strategy == "parallel"

        # Steps with dependencies -> sequential
        step1 = TaskStep(name="a", action="do_a")
        step2 = TaskStep(name="b", action="do_b", dependencies=[step1.id])
        plan = TaskPlan(goal="test", steps=[step1, step2])
        result = self.reasoner.reason(plan)
        assert result.strategy == "sequential"

    def test_capability_match(self):
        score = self.reasoner._capability_match("memory_recall", ["memory_recall", "search"])
        assert score == 1.0
        score = self.reasoner._capability_match("memory", ["memory_recall"])
        assert score > 0

    def test_plugin_registration(self):
        from prototype.cognition.reasoner import ReasonerPlugin
        plugin = ReasonerPlugin()
        self.reasoner.register_plugin(plugin)
        assert plugin in self.reasoner._plugins
        assert self.reasoner.unregister_plugin(plugin)

    def test_event_emission(self):
        received = []
        self.bus.subscribe("ReasoningStarted", lambda e: received.append(e))
        self.bus.subscribe("ReasoningCompleted", lambda e: received.append(e))
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        self.reasoner.reason(plan)
        assert len(received) == 2

    def test_reasoning_trace(self):
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        result = self.reasoner.reason(plan)
        assert len(result.reasoning_trace) == len(plan.steps)
        for entry in result.reasoning_trace:
            assert "step_id" in entry
            assert "candidates" in entry


# ═══════════════════════════════════════════════════════════════════════════════
#  Cognition Executor
# ═══════════════════════════════════════════════════════════════════════════════

class TestCognitionExecutor(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.executor import CognitionExecutor
        from prototype.cognition.reasoner import Reasoner
        from prototype.cognition.planner import TaskPlanner
        self.bus = EventBus()
        self.executor = CognitionExecutor(event_bus=self.bus)
        self.executor.load()
        self.reasoner = Reasoner(event_bus=self.bus)
        self.reasoner.load()
        self.planner = TaskPlanner(event_bus=self.bus)
        self.planner.load()

    def test_load_and_lifecycle(self):
        assert self.executor.is_loaded()
        assert self.executor.load() is None

    def test_register_handlers(self):
        self.executor.register_tool_handler("calc", lambda x: x)
        self.executor.register_agent_handler("agent1", lambda x: x)
        self.executor.register_worker_handler("worker1", lambda x: x)
        assert "calc" in self.executor._tool_handlers

    def test_execute_with_handler(self):
        self.reasoner.register_tool("echo_tool", ["echo"])
        self.executor.register_tool_handler("echo_tool", lambda x: {"echoed": x})
        plan = self.planner.create_plan("echo test", [{"name": "command", "confidence": 0.9}])
        reasoning = self.reasoner.reason(plan)
        result = self.executor.execute(plan, reasoning)
        assert result.plan_id == plan.id

    def test_execute_no_handler(self):
        self.reasoner.register_tool("unregistered_tool", ["test"])
        plan = self.planner.create_plan("test", [{"name": "command", "confidence": 0.9}])
        reasoning = self.reasoner.reason(plan)
        result = self.executor.execute(plan, reasoning)
        # Should still produce results (placeholder output)
        assert len(result.step_results) > 0

    def test_execute_parallel_strategy(self):
        from prototype.cognition.planner import TaskPlan, TaskStep
        from prototype.cognition.reasoner import ReasoningResult
        step1 = TaskStep(name="a", action="echo")
        step2 = TaskStep(name="b", action="echo")
        plan = TaskPlan(goal="test", steps=[step1, step2])
        reasoning = ReasoningResult(plan_id=plan.id, strategy="parallel")
        result = self.executor.execute(plan, reasoning)
        assert result.plan_id == plan.id

    def test_plugin_pre_execute(self):
        from prototype.cognition.executor import ExecutorPlugin, StepResult
        class ShortCircuitPlugin(ExecutorPlugin):
            def pre_execute(self, step, context):
                return StepResult(step_id=step.id, step_name=step.name, success=True, output="short-circuited")
        self.executor.register_plugin(ShortCircuitPlugin())
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        from prototype.cognition.reasoner import ReasoningResult
        reasoning = ReasoningResult(plan_id=plan.id)
        result = self.executor.execute(plan, reasoning)
        assert all(r.output == "short-circuited" for r in result.step_results)

    def test_plugin_execute_override(self):
        from prototype.cognition.executor import ExecutorPlugin, StepResult
        class OverridePlugin(ExecutorPlugin):
            def execute_step(self, step, candidate, context):
                return StepResult(step_id=step.id, step_name=step.name, success=True, output="override")
        self.executor.register_plugin(OverridePlugin())
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        from prototype.cognition.reasoner import ReasoningResult
        reasoning = ReasoningResult(plan_id=plan.id)
        result = self.executor.execute(plan, reasoning)
        assert all(r.output == "override" for r in result.step_results)

    def test_plugin_post_execute(self):
        from prototype.cognition.executor import ExecutorPlugin, StepResult
        class PostPlugin(ExecutorPlugin):
            def post_execute(self, step, result, context):
                result.metadata["post_processed"] = True
                return result
        self.executor.register_plugin(PostPlugin())
        # Use a plan with no dependencies so all steps go through _execute_step
        from prototype.cognition.planner import TaskPlan, TaskStep
        plan = TaskPlan(goal="test", steps=[
            TaskStep(name="a", action="reason"),
            TaskStep(name="b", action="respond"),
        ])
        from prototype.cognition.reasoner import ReasoningResult
        reasoning = ReasoningResult(plan_id=plan.id)
        result = self.executor.execute(plan, reasoning)
        # All steps that go through _execute_step should have post_processed
        assert all(r.metadata.get("post_processed") for r in result.step_results)

    def test_handler_exception(self):
        self.reasoner.register_tool("bad_tool", ["test"])
        def bad_handler(x):
            raise ValueError("intentional error")
        self.executor.register_tool_handler("bad_tool", bad_handler)
        plan = self.planner.create_plan("test", [{"name": "command", "confidence": 0.9}])
        reasoning = self.reasoner.reason(plan)
        result = self.executor.execute(plan, reasoning)
        # The step with the handler should fail, others should still run
        failed = [r for r in result.step_results if not r.success]
        assert len(failed) > 0

    def test_event_emission(self):
        received = []
        self.bus.subscribe("ExecutionStarted", lambda e: received.append(e))
        self.bus.subscribe("ExecutionCompleted", lambda e: received.append(e))
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        from prototype.cognition.reasoner import ReasoningResult
        reasoning = ReasoningResult(plan_id=plan.id)
        self.executor.execute(plan, reasoning)
        assert len(received) == 2

    def test_step_events(self):
        received = []
        self.bus.subscribe("StepStarted", lambda e: received.append(e))
        self.bus.subscribe("StepCompleted", lambda e: received.append(e))
        plan = self.planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        from prototype.cognition.reasoner import ReasoningResult
        reasoning = ReasoningResult(plan_id=plan.id)
        self.executor.execute(plan, reasoning)
        assert len(received) >= 2  # at least StepStarted + StepCompleted


# ═══════════════════════════════════════════════════════════════════════════════
#  Cognition Reflector
# ═══════════════════════════════════════════════════════════════════════════════

class TestCognitionReflector(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.reflector import CognitionReflector
        from prototype.cognition.executor import ExecutionResult, StepResult
        from prototype.cognition.planner import TaskPlan, TaskStep
        self.bus = EventBus()
        self.reflector = CognitionReflector(event_bus=self.bus)
        self.reflector.load()

        # Create test data
        self.step1 = StepResult(step_id="s1", step_name="step1", success=True, output="ok")
        self.step2 = StepResult(step_id="s2", step_name="step2", success=False, error="failed")
        self.execution = ExecutionResult(
            plan_id="plan1", success=False,
            step_results=[self.step1, self.step2],
            output="result", total_time_ms=100,
        )
        self.plan = TaskPlan(
            id="plan1",
            goal="test goal",
            steps=[
                TaskStep(id="s1", name="step1"),
                TaskStep(id="s2", name="step2"),
            ],
            estimated_total_cost=1.0,
        )

    def test_load_and_lifecycle(self):
        assert self.reflector.is_loaded()
        assert self.reflector.load() is None

    def test_reflect_basic(self):
        result = self.reflector.reflect(self.execution, self.plan)
        assert result.plan_id == "plan1"
        assert result.overall_score >= 0
        assert len(result.assessments) > 0
        assert len(result.lessons) > 0
        assert result.latency_ms >= 0

    def test_quality_assessments(self):
        result = self.reflector.reflect(self.execution, self.plan)
        dimensions = [a.dimension for a in result.assessments]
        assert "success_rate" in dimensions
        assert "completeness" in dimensions
        assert "output_quality" in dimensions

    def test_success_rate_assessment(self):
        result = self.reflector.reflect(self.execution, self.plan)
        sr = next(a for a in result.assessments if a.dimension == "success_rate")
        assert sr.score == 0.5  # 1/2 steps succeeded

    def test_lessons_from_failures(self):
        result = self.reflector.reflect(self.execution, self.plan)
        failure_lessons = [l for l in result.lessons if l.category == "failure_pattern"]
        assert len(failure_lessons) > 0

    def test_memory_updates(self):
        result = self.reflector.reflect(self.execution, self.plan)
        assert len(result.memory_updates) > 0
        # Should have failure memory updates (step2 failed)
        tags = [u.tags for u in result.memory_updates]
        assert any("failure" in t for t in tags)

    def test_recommendations(self):
        result = self.reflector.reflect(self.execution, self.plan)
        assert isinstance(result.recommendations, list)

    def test_history(self):
        self.reflector.reflect(self.execution, self.plan)
        self.reflector.reflect(self.execution, self.plan)
        history = self.reflector.get_history(limit=1)
        assert len(history) == 1

    def test_stats(self):
        self.reflector.reflect(self.execution, self.plan)
        stats = self.reflector.get_stats()
        assert stats["total_reflections"] == 1
        assert stats["avg_score"] > 0

    def test_plugin_registration(self):
        from prototype.cognition.reflector import ReflectorPlugin
        plugin = ReflectorPlugin()
        self.reflector.register_plugin(plugin)
        assert plugin in self.reflector._plugins
        assert self.reflector.unregister_plugin(plugin)

    def test_plugin_custom_assessment(self):
        from prototype.cognition.reflector import ReflectorPlugin, QualityAssessment
        class CustomAssessment(ReflectorPlugin):
            def assess_quality(self, execution, plan, context):
                return QualityAssessment(dimension="custom", score=0.42, reason="custom check")
        self.reflector.register_plugin(CustomAssessment())
        result = self.reflector.reflect(self.execution, self.plan)
        custom = next((a for a in result.assessments if a.dimension == "custom"), None)
        assert custom is not None
        assert custom.score == 0.42

    def test_plugin_lessons(self):
        from prototype.cognition.reflector import ReflectorPlugin, Lesson
        class CustomLesson(ReflectorPlugin):
            def generate_lessons(self, execution, plan, assessments, context):
                return [Lesson(content="custom lesson", category="optimization", confidence=0.5)]
        self.reflector.register_plugin(CustomLesson())
        result = self.reflector.reflect(self.execution, self.plan)
        custom = [l for l in result.lessons if l.content == "custom lesson"]
        assert len(custom) == 1

    def test_plugin_memory_updates(self):
        from prototype.cognition.reflector import ReflectorPlugin, MemoryUpdate
        class CustomMemory(ReflectorPlugin):
            def suggest_memory_updates(self, execution, plan, context):
                return [MemoryUpdate(content="custom memory", tags=["custom"])]
        self.reflector.register_plugin(CustomMemory())
        result = self.reflector.reflect(self.execution, self.plan)
        custom = [m for m in result.memory_updates if "custom" in m.tags]
        assert len(custom) == 1

    def test_event_emission(self):
        received = []
        self.bus.subscribe("ReflectionStarted", lambda e: received.append(e))
        self.bus.subscribe("ReflectionCompleted", lambda e: received.append(e))
        self.bus.subscribe("LessonLearned", lambda e: received.append(e))
        self.reflector.reflect(self.execution, self.plan)
        assert len(received) >= 2  # Started + Completed + at least one LessonLearned

    def test_overall_score_range(self):
        result = self.reflector.reflect(self.execution, self.plan)
        assert 0.0 <= result.overall_score <= 1.0

    def test_perfect_execution(self):
        from prototype.cognition.executor import ExecutionResult, StepResult
        from prototype.cognition.planner import TaskPlan, TaskStep
        perfect_exec = ExecutionResult(
            plan_id="p1", success=True,
            step_results=[StepResult(step_id="s1", step_name="s1", success=True, output="ok")],
            output="done", total_time_ms=50,
        )
        perfect_plan = TaskPlan(goal="test", steps=[TaskStep(id="s1", name="s1")])
        result = self.reflector.reflect(perfect_exec, perfect_plan)
        assert result.overall_score > 0.5


# ═══════════════════════════════════════════════════════════════════════════════
#  Cognition Runtime (Integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCognitionRuntime(unittest.TestCase):
    def setUp(self):
        from prototype.cognition.cognition_runtime import CognitionRuntime
        self.bus = EventBus()
        self.runtime = CognitionRuntime(event_bus=self.bus)
        self.runtime.load()

    def tearDown(self):
        self.runtime.shutdown()

    def test_load_and_lifecycle(self):
        assert self.runtime.is_loaded()
        assert self.runtime.load() is None  # idempotent
        self.runtime.shutdown()
        assert not self.runtime.is_loaded()

    def test_shutdown_idempotent(self):
        self.runtime.shutdown()
        self.runtime.shutdown()  # should not raise

    def test_process_basic(self):
        result = self.runtime.process("What is machine learning?")
        assert isinstance(result, EngineResult)
        assert result.metadata.get("plan_id") is not None
        assert result.metadata.get("perception_id") is not None
        assert result.metadata.get("execution_id") is not None
        assert result.metadata.get("reflection_score") is not None

    def test_process_with_context(self):
        result = self.runtime.process("test", context={"source": "test"})
        assert result.metadata.get("plan_id") is not None

    def test_process_command(self):
        result = self.runtime.process("Run the test suite")
        assert result.metadata.get("plan_id") is not None

    def test_process_generation(self):
        result = self.runtime.process("Generate a report about sales")
        assert result.metadata.get("plan_id") is not None

    def test_process_analysis(self):
        result = self.runtime.process("Analyze the codebase for issues")
        assert result.metadata.get("plan_id") is not None

    def test_process_empty_input(self):
        result = self.runtime.process("")
        assert result.metadata.get("plan_id") is not None

    def test_register_tool(self):
        self.runtime.register_tool("test_tool", ["test", "compute"])
        assert "test_tool" in self.runtime.reasoner._tool_registry

    def test_register_tool_with_handler(self):
        self.runtime.register_tool("echo", ["echo"], handler=lambda x: x)
        assert "echo" in self.runtime.executor._tool_handlers

    def test_register_agent(self):
        self.runtime.register_agent("test_agent", ["reason"])
        assert "test_agent" in self.runtime.reasoner._agent_registry

    def test_register_worker(self):
        self.runtime.register_worker("test_worker", ["background"])
        assert "test_worker" in self.runtime.reasoner._worker_registry

    def test_plugin_registration(self):
        from prototype.cognition.perception import PerceptionPlugin
        from prototype.cognition.planner import TaskPlannerPlugin
        from prototype.cognition.reasoner import ReasonerPlugin
        from prototype.cognition.executor import ExecutorPlugin
        from prototype.cognition.reflector import ReflectorPlugin

        pp = PerceptionPlugin()
        tp = TaskPlannerPlugin()
        rp = ReasonerPlugin()
        ep = ExecutorPlugin()
        rfp = ReflectorPlugin()

        self.runtime.register_perception_plugin(pp)
        self.runtime.register_planner_plugin(tp)
        self.runtime.register_reasoner_plugin(rp)
        self.runtime.register_executor_plugin(ep)
        self.runtime.register_reflector_plugin(rfp)

        assert pp in self.runtime.perception._plugins
        assert tp in self.runtime.planner._plugins
        assert rp in self.runtime.reasoner._plugins
        assert ep in self.runtime.executor._plugins
        assert rfp in self.runtime.reflector._plugins

    def test_stats(self):
        stats = self.runtime.get_stats()
        assert stats["loaded"] is True
        assert stats["process_count"] == 0
        assert "perception" in stats
        assert "planner" in stats
        assert "reasoner" in stats
        assert "executor" in stats
        assert "reflector" in stats

    def test_stats_after_process(self):
        self.runtime.process("test")
        stats = self.runtime.get_stats()
        assert stats["process_count"] == 1

    def test_event_emission(self):
        # Re-create runtime so we can subscribe before load
        from prototype.cognition.cognition_runtime import CognitionRuntime
        bus = EventBus()
        runtime = CognitionRuntime(event_bus=bus)
        received = []
        bus.subscribe("CognitionStarted", lambda e: received.append(e))
        bus.subscribe("CognitionProcessing", lambda e: received.append(e))
        bus.subscribe("CognitionCompleted", lambda e: received.append(e))
        runtime.load()
        runtime.process("test")
        event_types = [e.event_type for e in received]
        assert "CognitionStarted" in event_types
        assert "CognitionProcessing" in event_types
        assert "CognitionCompleted" in event_types
        runtime.shutdown()

    def test_perception_events(self):
        received = []
        self.bus.subscribe("PerceptionStarted", lambda e: received.append(e))
        self.bus.subscribe("PerceptionProcessed", lambda e: received.append(e))
        self.runtime.process("test")
        assert any(e.event_type == "PerceptionStarted" for e in received)
        assert any(e.event_type == "PerceptionProcessed" for e in received)

    def test_planner_events(self):
        received = []
        self.bus.subscribe("PlanStarted", lambda e: received.append(e))
        self.bus.subscribe("PlanCreated", lambda e: received.append(e))
        self.runtime.process("test")
        assert any(e.event_type == "PlanStarted" for e in received)
        assert any(e.event_type == "PlanCreated" for e in received)

    def test_reasoner_events(self):
        received = []
        self.bus.subscribe("ReasoningStarted", lambda e: received.append(e))
        self.bus.subscribe("ReasoningCompleted", lambda e: received.append(e))
        self.runtime.process("test")
        assert any(e.event_type == "ReasoningStarted" for e in received)
        assert any(e.event_type == "ReasoningCompleted" for e in received)

    def test_executor_events(self):
        received = []
        self.bus.subscribe("ExecutionStarted", lambda e: received.append(e))
        self.bus.subscribe("ExecutionCompleted", lambda e: received.append(e))
        self.runtime.process("test")
        assert any(e.event_type == "ExecutionStarted" for e in received)
        assert any(e.event_type == "ExecutionCompleted" for e in received)

    def test_reflector_events(self):
        received = []
        self.bus.subscribe("ReflectionStarted", lambda e: received.append(e))
        self.bus.subscribe("ReflectionCompleted", lambda e: received.append(e))
        self.runtime.process("test")
        assert any(e.event_type == "ReflectionStarted" for e in received)
        assert any(e.event_type == "ReflectionCompleted" for e in received)

    def test_shutdown_event(self):
        received = []
        self.bus.subscribe("CognitionShutdown", lambda e: received.append(e))
        self.runtime.shutdown()
        assert len(received) == 1

    def test_process_count_increments(self):
        self.runtime.process("first")
        self.runtime.process("second")
        stats = self.runtime.get_stats()
        assert stats["process_count"] == 2

    def test_metadata_fields(self):
        result = self.runtime.process("test input")
        meta = result.metadata
        assert "perception_id" in meta
        assert "plan_id" in meta
        assert "execution_id" in meta
        assert "reflection_score" in meta
        assert "latency_ms" in meta

    def test_full_pipeline_end_to_end(self):
        """End-to-end test: input → perception → plan → reason → execute → reflect → response."""
        self.runtime.register_tool("echo", ["echo", "respond"], handler=lambda x: {"response": x.get("goal", "")})
        result = self.runtime.process("What is the meaning of life?")
        assert result.success is not None
        assert result.metadata.get("plan_id") is not None
        assert result.metadata.get("reflection_score") >= 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Plugin Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestPluginIntegration(unittest.TestCase):
    def test_perception_plugin_chain(self):
        from prototype.cognition.perception import PerceptionEngine, PerceptionPlugin
        bus = EventBus()
        engine = PerceptionEngine(event_bus=bus)
        engine.load()

        class PluginA(PerceptionPlugin):
            def pre_process(self, raw_input, context):
                return raw_input + " [pluginA]"
        class PluginB(PerceptionPlugin):
            def post_process(self, result, context):
                result.metadata["plugin_b"] = True
                return result

        engine.register_plugin(PluginA())
        engine.register_plugin(PluginB())
        result = engine.process("hello")
        # normalization lowercases
        assert "[plugina]" in result.normalized_input
        assert result.metadata.get("plugin_b") is True

    def test_planner_plugin_chain(self):
        from prototype.cognition.planner import TaskPlanner, TaskPlannerPlugin, TaskPlan, TaskStep
        bus = EventBus()
        planner = TaskPlanner(event_bus=bus)
        planner.load()

        class AddStepPlugin(TaskPlannerPlugin):
            def refine_plan(self, plan, context):
                plan.steps.append(TaskStep(name="extra_step"))
                return plan

        planner.register_plugin(AddStepPlugin())
        plan = planner.create_plan("test", [{"name": "query", "confidence": 0.8}])
        assert any(s.name == "extra_step" for s in plan.steps)

    def test_reflector_plugin_chain(self):
        from prototype.cognition.reflector import CognitionReflector, ReflectorPlugin, QualityAssessment
        from prototype.cognition.executor import ExecutionResult, StepResult
        from prototype.cognition.planner import TaskPlan, TaskStep
        bus = EventBus()
        reflector = CognitionReflector(event_bus=bus)
        reflector.load()

        class ExtraDimensionPlugin(ReflectorPlugin):
            def assess_quality(self, execution, plan, context):
                return QualityAssessment(dimension="extra", score=0.75, reason="extra check")

        reflector.register_plugin(ExtraDimensionPlugin())
        execution = ExecutionResult(
            plan_id="p1", success=True,
            step_results=[StepResult(step_id="s1", step_name="s1", success=True, output="ok")],
            output="done", total_time_ms=50,
        )
        plan = TaskPlan(goal="test", steps=[TaskStep(id="s1", name="s1")])
        result = reflector.reflect(execution, plan)
        assert any(a.dimension == "extra" for a in result.assessments)


if __name__ == "__main__":
    unittest.main()
