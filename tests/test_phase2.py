"""Phase 2 test suite for Alfa COS.

Tests all new modules: Executive, Decision, Reflection, Learning,
Memory Manager, Persistent Memory, Tool Manager, Plugin Manager,
Ollama Provider, and the Phase 2 Runtime pipeline.

Run:  python -m pytest tests/ -v
"""

import os
import tempfile
import unittest

from prototype.common import Context, Goal, EngineResult, Episode, EventBus, Event
from prototype.config import SettingsManager
from prototype.decision import DecisionEngine, DecisionAction
from prototype.executive import ExecutiveController
from prototype.executive.executive_controller import (
    Execution,
    ExecutionStatus,
    ExecutionPriority,
)
from prototype.learning import LearningEngine
from prototype.memory import Memory, PersistentMemory, MemoryManager
from prototype.plugins import PluginManager
from prototype.plugins.base_plugin import BasePlugin, PluginManifest
from prototype.provider import OllamaProvider, Provider
from prototype.reflection import ReflectionEngine
from prototype.reflection.reflection_engine import ReflectionRecord
from prototype.runtime import AlfaRuntime
from prototype.tools import ToolManager, BaseTool, ToolResult


# ═══════════════════════════════════════════════════════════════════════════════
#  Executive Controller
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecutiveController(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.exec = ExecutiveController(event_bus=self.bus)
        self.exec.load()

    def test_execute_goal(self) -> None:
        goal = Goal(name="TEST", parameters={"input": "hello"})
        execution = self.exec.execute_goal(goal, Context())
        self.assertIsInstance(execution, Execution)
        self.assertEqual(execution.status, ExecutionStatus.RUNNING)
        self.assertIsNotNone(execution.started_at)

    def test_complete_execution(self) -> None:
        goal = Goal(name="TEST")
        execution = self.exec.execute_goal(goal, Context())
        result = EngineResult(content="done", success=True)
        self.exec.complete_execution(execution.execution_id, result)
        # Should be archived to history
        history = self.exec.get_execution_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].status, ExecutionStatus.COMPLETED)

    def test_fail_and_retry(self) -> None:
        goal = Goal(name="TEST")
        execution = self.exec.execute_goal(goal, Context())
        retried = self.exec.fail_execution(execution.execution_id, "test error")
        self.assertTrue(retried)  # Should retry first time
        self.assertEqual(execution.retry_count, 1)

    def test_cancel_execution(self) -> None:
        goal = Goal(name="TEST")
        execution = self.exec.execute_goal(goal, Context())
        self.assertTrue(self.exec.cancel_execution(execution.execution_id))
        history = self.exec.get_execution_history()
        self.assertEqual(history[0].status, ExecutionStatus.CANCELLED)

    def test_get_stats(self) -> None:
        stats = self.exec.get_stats()
        self.assertIn("active", stats)
        self.assertIn("completed", stats)

    def test_event_published(self) -> None:
        received = []
        self.bus.subscribe("ExecutionStarted", lambda e: received.append(e))
        goal = Goal(name="TEST")
        self.exec.execute_goal(goal, Context())
        self.assertEqual(len(received), 1)

    def tearDown(self) -> None:
        self.exec.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Decision Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestDecisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.engine.load()

    def test_memory_store_decision(self) -> None:
        goal = Goal(name="REMEMBER", parameters={"content": "test"})
        decision = self.engine.decide(goal)
        self.assertEqual(decision.action, DecisionAction.STORE_MEMORY)

    def test_memory_recall_decision(self) -> None:
        goal = Goal(name="RECALL", parameters={"query": "test"})
        decision = self.engine.decide(goal)
        self.assertEqual(decision.action, DecisionAction.RETRIEVE_MEMORY)

    def test_conversation_decision(self) -> None:
        goal = Goal(name="USER_REQUEST", parameters={"input": "hello"})
        decision = self.engine.decide(goal)
        self.assertEqual(decision.action, DecisionAction.CALL_PROVIDER)

    def test_no_provider_aborts(self) -> None:
        goal = Goal(name="USER_REQUEST", parameters={"input": "hello"})
        decision = self.engine.decide(goal, provider_available=False)
        self.assertEqual(decision.action, DecisionAction.ABORT)

    def test_builtin_command_responds(self) -> None:
        goal = Goal(name="HELP")
        decision = self.engine.decide(goal)
        self.assertEqual(decision.action, DecisionAction.RESPOND)

    def tearDown(self) -> None:
        self.engine.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Reflection Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestReflectionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.engine = ReflectionEngine(event_bus=self.bus)
        self.engine.load()

    def test_reflect_success(self) -> None:
        result = EngineResult(content="Great response", success=True)
        record = self.engine.reflect("exec-1", result, latency_ms=100.0)
        self.assertIsInstance(record, ReflectionRecord)
        self.assertGreater(record.quality_score, 0.5)
        self.assertEqual(len(record.errors), 0)

    def test_reflect_failure(self) -> None:
        result = EngineResult(content="", success=False, error="Provider down")
        record = self.engine.reflect("exec-2", result, latency_ms=50.0)
        self.assertLess(record.quality_score, 0.7)
        self.assertGreater(len(record.errors), 0)

    def test_reflect_high_latency(self) -> None:
        result = EngineResult(content="OK response", success=True)
        record = self.engine.reflect("exec-3", result, latency_ms=10000.0)
        self.assertTrue(len(record.recommendations) > 0)

    def test_get_stats(self) -> None:
        result = EngineResult(content="test", success=True)
        self.engine.reflect("x", result, latency_ms=100.0)
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_reflections"], 1)

    def test_event_published(self) -> None:
        received = []
        self.bus.subscribe("ReflectionCompleted", lambda e: received.append(e))
        result = EngineResult(content="test", success=True)
        self.engine.reflect("x", result, latency_ms=100.0)
        self.assertEqual(len(received), 1)

    def tearDown(self) -> None:
        self.engine.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Learning Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestLearningEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LearningEngine()
        self.engine.load()

    def test_learn(self) -> None:
        lesson = self.engine.learn("Use shorter prompts", confidence=0.8)
        self.assertEqual(lesson.lesson, "Use shorter prompts")
        self.assertEqual(lesson.confidence, 0.8)

    def test_get_lessons(self) -> None:
        self.engine.learn("lesson 1")
        self.engine.learn("lesson 2")
        lessons = self.engine.get_lessons()
        self.assertEqual(len(lessons), 2)

    def test_get_stats(self) -> None:
        self.engine.learn("test", source="reflection")
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_lessons"], 1)
        self.assertIn("reflection", stats["sources"])

    def tearDown(self) -> None:
        self.engine.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Persistent Memory (SQLite)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPersistentMemory(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._tmpfile.close()
        self.mem = PersistentMemory(db_path=self._tmpfile.name)
        self.mem.load()

    def test_store_and_retrieve(self) -> None:
        ep = Episode(content="My name is Sohail")
        self.mem.store(ep)
        retrieved = self.mem.retrieve(ep.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "My name is Sohail")

    def test_search(self) -> None:
        self.mem.store(Episode(content="Python is great"))
        self.mem.store(Episode(content="Java is old"))
        results = self.mem.search("Python")
        self.assertEqual(len(results), 1)
        self.assertIn("Python", results[0].content)

    def test_delete(self) -> None:
        ep = Episode(content="temp")
        self.mem.store(ep)
        self.assertTrue(self.mem.delete(ep.id))
        self.assertIsNone(self.mem.retrieve(ep.id))

    def test_clear(self) -> None:
        self.mem.store(Episode(content="one"))
        self.mem.store(Episode(content="two"))
        cleared = self.mem.clear()
        self.assertEqual(cleared, 2)
        self.assertEqual(self.mem.count(), 0)

    def test_list_all(self) -> None:
        self.mem.store(Episode(content="a"))
        self.mem.store(Episode(content="b"))
        items = self.mem.list_all()
        self.assertEqual(len(items), 2)

    def test_count(self) -> None:
        self.mem.store(Episode(content="x"))
        self.assertEqual(self.mem.count(), 1)

    def tearDown(self) -> None:
        self.mem.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)


# ═══════════════════════════════════════════════════════════════════════════════
#  Memory Manager
# ═══════════════════════════════════════════════════════════════════════════════


class TestMemoryManager(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._tmpfile.close()
        working = Memory()
        persistent = PersistentMemory(db_path=self._tmpfile.name)
        self.mgr = MemoryManager(
            working_memory=working, persistent_memory=persistent
        )
        self.mgr.load()

    def test_remember(self) -> None:
        ep = self.mgr.remember("My cat is Luna")
        self.assertEqual(ep.content, "My cat is Luna")
        self.assertEqual(len(self.mgr.get_working_memory()), 1)

    def test_remember_with_persist(self) -> None:
        ep = self.mgr.remember("Persistent fact", persist=True)
        # Should be in both working and persistent
        self.assertEqual(len(self.mgr.get_working_memory()), 1)
        persistent = self.mgr.get_persistent_memories()
        self.assertEqual(len(persistent), 1)

    def test_recall_merges(self) -> None:
        self.mgr.remember("Working memory fact")
        self.mgr.remember("Persistent only", persist=True)
        results = self.mgr.recall("fact")
        self.assertGreater(len(results), 0)

    def test_forget(self) -> None:
        ep = self.mgr.remember("temp")
        self.assertTrue(self.mgr.forget(ep.id))
        self.assertEqual(len(self.mgr.get_working_memory()), 0)

    def test_clear(self) -> None:
        self.mgr.remember("a")
        self.mgr.remember("b")
        self.mgr.clear()
        self.assertEqual(len(self.mgr.get_working_memory()), 0)

    def test_stats(self) -> None:
        self.mgr.remember("test")
        stats = self.mgr.get_stats()
        self.assertEqual(stats["working_count"], 1)

    def tearDown(self) -> None:
        self.mgr.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)


# ═══════════════════════════════════════════════════════════════════════════════
#  Tool Manager
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolManager(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = ToolManager()
        self.mgr.load()

    def test_builtin_tools_registered(self) -> None:
        names = self.mgr.get_tool_names()
        self.assertIn("calculator", names)
        self.assertIn("datetime", names)
        self.assertIn("system_info", names)

    def test_calculator(self) -> None:
        result = self.mgr.execute("calculator", {"expression": "2 + 3"})
        self.assertTrue(result.success)
        self.assertEqual(result.result, 5)

    def test_calculator_complex(self) -> None:
        result = self.mgr.execute("calculator", {"expression": "sqrt(16) + pi"})
        self.assertTrue(result.success)
        import math
        self.assertAlmostEqual(result.result, 4 + math.pi)

    def test_datetime_tool(self) -> None:
        result = self.mgr.execute("datetime", {})
        self.assertTrue(result.success)
        self.assertIn("date", result.result)
        self.assertIn("time", result.result)

    def test_system_info_tool(self) -> None:
        result = self.mgr.execute("system_info", {})
        self.assertTrue(result.success)
        self.assertIn("platform", result.result)

    def test_tool_not_found(self) -> None:
        result = self.mgr.execute("nonexistent", {})
        self.assertFalse(result.success)

    def test_list_tools(self) -> None:
        tools = self.mgr.list_tools()
        self.assertGreater(len(tools), 0)
        self.assertIn("name", tools[0])

    def test_register_custom_tool(self) -> None:
        class EchoTool(BaseTool):
            @property
            def tool_name(self): return "echo"
            @property
            def description(self): return "Echo back"
            def execute(self, args):
                return ToolResult(result=args.get("text", ""))

        self.mgr.register(EchoTool())
        result = self.mgr.execute("echo", {"text": "hello"})
        self.assertTrue(result.success)
        self.assertEqual(result.result, "hello")

    def tearDown(self) -> None:
        self.mgr.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Plugin Manager
# ═══════════════════════════════════════════════════════════════════════════════


class _TestPlugin(BasePlugin):
    """Minimal test plugin."""
    def __init__(self):
        self._loaded = False

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="A test plugin",
        )

    def on_load(self) -> None:
        self._loaded = True

    def on_unload(self) -> None:
        self._loaded = False


class TestPluginManager(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = PluginManager()
        self.mgr.load()

    def test_register_plugin(self) -> None:
        plugin = _TestPlugin()
        self.assertTrue(self.mgr.register(plugin))
        self.assertIn("test_plugin", self.mgr.get_plugin_names())

    def test_unregister_plugin(self) -> None:
        self.mgr.register(_TestPlugin())
        self.assertTrue(self.mgr.unregister("test_plugin"))
        self.assertNotIn("test_plugin", self.mgr.get_plugin_names())

    def test_enable_disable(self) -> None:
        self.mgr.register(_TestPlugin())
        self.mgr.enable("test_plugin")
        self.assertTrue(self.mgr.is_enabled("test_plugin"))
        self.mgr.disable("test_plugin")
        self.assertFalse(self.mgr.is_enabled("test_plugin"))

    def test_list_plugins(self) -> None:
        self.mgr.register(_TestPlugin())
        plugins = self.mgr.list_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["name"], "test_plugin")

    def test_plugin_abc_enforced(self) -> None:
        with self.assertRaises(TypeError):
            BasePlugin()

    def tearDown(self) -> None:
        self.mgr.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Ollama Provider
# ═══════════════════════════════════════════════════════════════════════════════


class TestOllamaProvider(unittest.TestCase):
    def test_is_provider(self) -> None:
        self.assertIsInstance(OllamaProvider(), Provider)

    def test_load(self) -> None:
        provider = OllamaProvider()
        provider.load()
        # Note: is_available() depends on local Ollama instance
        # so we just verify it loads without error
        provider.shutdown()

    def test_provider_name(self) -> None:
        self.assertEqual(OllamaProvider().provider_name, "OllamaProvider")


# ═══════════════════════════════════════════════════════════════════════════════
#  NVIDIA Provider
# ═══════════════════════════════════════════════════════════════════════════════


class TestNVIDIAProvider(unittest.TestCase):
    def test_is_provider(self) -> None:
        from prototype.provider import NVIDIAProvider
        self.assertIsInstance(NVIDIAProvider(), Provider)

    def test_missing_api_key_returns_explicit_error(self) -> None:
        from prototype.provider import NVIDIAProvider
        provider = NVIDIAProvider()
        provider.load()
        self.assertFalse(provider.is_available())
        res = provider.generate("hello")
        self.assertFalse(res.success)
        self.assertIn("API key", res.error)

    def test_provider_name(self) -> None:
        from prototype.provider import NVIDIAProvider
        self.assertEqual(NVIDIAProvider().provider_name, "NVIDIAProvider")



# ═══════════════════════════════════════════════════════════════════════════════
#  Phase 2 Runtime
# ═══════════════════════════════════════════════════════════════════════════════


class TestPhase2Runtime(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        )
        self._tmpfile.close()
        os.unlink(self._tmpfile.name)
        settings = SettingsManager(config_path=self._tmpfile.name)
        settings.load()
        self.runtime = AlfaRuntime(settings=settings)
        self.runtime.load()

    def test_process_conversation(self) -> None:
        result = self.runtime.process("hello")
        self.assertTrue(result.success)

    def test_full_pipeline_reflection(self) -> None:
        self.runtime.process("hello")
        reflections = self.runtime.reflection.get_reflections()
        self.assertGreater(len(reflections), 0)

    def test_executive_tracks_execution(self) -> None:
        self.runtime.process("test message")
        history = self.runtime.executive.get_execution_history()
        self.assertGreater(len(history), 0)

    def test_memory_via_runtime(self) -> None:
        self.runtime.process("remember My project is Alfa COS")
        result = self.runtime.process("recall project")
        self.assertIn("Alfa", result.content)

    def test_get_stats(self) -> None:
        self.runtime.process("hello")
        stats = self.runtime.get_stats()
        self.assertIn("provider", stats)
        self.assertIn("executive", stats)
        self.assertIn("reflection", stats)

    def test_tool_manager_available(self) -> None:
        tools = self.runtime.tool_manager.list_tools()
        self.assertGreater(len(tools), 0)

    def test_plugin_manager_available(self) -> None:
        plugins = self.runtime.plugin_manager.list_plugins()
        self.assertIsInstance(plugins, list)

    def test_switch_provider(self) -> None:
        self.runtime.switch_provider("mock")
        self.assertEqual(self.runtime.provider_name, "mock")

    def tearDown(self) -> None:
        self.runtime.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)
        # Clean up test DB
        data_dir = os.path.join(
            os.path.dirname(__file__), "..", "data"
        )
        db_path = os.path.join(data_dir, "memory.db")
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
