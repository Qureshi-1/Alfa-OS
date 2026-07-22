"""Comprehensive test suite for Alfa COS v0.1.

Run:  python -m pytest tests/ -v
"""

import json
import os
import tempfile
import unittest

from prototype.common import Context, Goal, EngineResult, Episode
from prototype.config import SettingsManager, reset_settings_manager
from prototype.context import ContextManager
from prototype.kernel import Kernel
from prototype.kernel.goal_interpreter import GoalInterpreter
from prototype.memory import Memory
from prototype.planner import Planner
from prototype.provider import MockProvider, Provider
from prototype.runtime import AlfaRuntime


# ═══════════════════════════════════════════════════════════════════════════════
#  Settings / Config
# ═══════════════════════════════════════════════════════════════════════════════


class TestSettingsManager(unittest.TestCase):
    """Settings persistence, defaults, masking, and provider config."""

    def setUp(self) -> None:
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        )
        self._tmpfile.close()
        os.unlink(self._tmpfile.name)  # start clean
        self.settings = SettingsManager(config_path=self._tmpfile.name)
        self.settings.load()

    def tearDown(self) -> None:
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)

    def test_defaults_applied(self) -> None:
        self.assertEqual(self.settings.get_provider(), "mock")
        self.assertEqual(self.settings.get("temperature"), 0.7)
        self.assertEqual(self.settings.get("max_tokens"), 4096)
        self.assertEqual(self.settings.get("timeout"), 30)

    def test_set_and_get(self) -> None:
        self.settings.set("provider", "nvidia")
        self.assertEqual(self.settings.get("provider"), "nvidia")

    def test_persists_to_disk(self) -> None:
        self.settings.set("model", "test-model")
        # Reload from disk.
        s2 = SettingsManager(config_path=self._tmpfile.name)
        s2.load()
        self.assertEqual(s2.get("model"), "test-model")

    def test_masks_api_keys(self) -> None:
        self.settings.set("api_key", "sk-test1234567890abcdef")
        self.settings.set("openrouter_api_key", "or-key-xyz789")
        safe = self.settings.get_all()
        self.assertTrue(safe["api_key"].startswith("***"))
        self.assertNotIn("sk-test", safe["api_key"])
        self.assertTrue(safe["openrouter_api_key"].startswith("***"))

    def test_mask_secret_short(self) -> None:
        self.assertEqual(SettingsManager.mask_secret(""), "(not set)")
        self.assertEqual(SettingsManager.mask_secret("abc"), "***")
        self.assertEqual(SettingsManager.mask_secret("abcde"), "***bcde")

    def test_set_provider_validates(self) -> None:
        with self.assertRaises(ValueError):
            self.settings.set_provider("invalid")

    def test_get_provider_config_nvidia(self) -> None:
        self.settings.set("provider", "nvidia")
        self.settings.set("api_key", "nv-key")
        cfg = self.settings.get_provider_config()
        self.assertEqual(cfg["provider"], "nvidia")
        self.assertEqual(cfg["api_key"], "nv-key")

    def test_get_provider_config_openrouter(self) -> None:
        self.settings.set("provider", "openrouter")
        self.settings.set("openrouter_api_key", "or-key")
        cfg = self.settings.get_provider_config()
        self.assertEqual(cfg["provider"], "openrouter")
        self.assertEqual(cfg["api_key"], "or-key")

    def test_get_model_per_provider(self) -> None:
        self.settings.set("provider", "nvidia")
        self.settings.set("model", "nvidia-model")
        self.assertEqual(self.settings.get_model(), "nvidia-model")

        self.settings.set("provider", "openrouter")
        self.settings.set("openrouter_model", "or-model")
        self.assertEqual(self.settings.get_model(), "or-model")

    def test_set_api_key_per_provider(self) -> None:
        self.settings.set("provider", "nvidia")
        self.settings.set_api_key("nv-123")
        self.assertEqual(self.settings.get("api_key"), "nv-123")

        self.settings.set("provider", "openrouter")
        self.settings.set_api_key("or-456")
        self.assertEqual(self.settings.get("openrouter_api_key"), "or-456")

    def test_corrupt_json_resets(self) -> None:
        with open(self._tmpfile.name, "w") as f:
            f.write("{invalid json")
        s = SettingsManager(config_path=self._tmpfile.name)
        s.load()
        self.assertEqual(s.get_provider(), "mock")  # defaults applied

    def test_test_connection_mock(self) -> None:
        result = self.settings.test_connection()
        self.assertTrue(result["connected"])
        self.assertEqual(result["provider"], "mock")


# ═══════════════════════════════════════════════════════════════════════════════
#  Goal Interpreter
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoalInterpreter(unittest.TestCase):
    def setUp(self) -> None:
        self.interp = GoalInterpreter()

    def test_empty_input(self) -> None:
        goal = self.interp.interpret("")
        self.assertEqual(goal.name, "EMPTY")

    def test_remember(self) -> None:
        goal = self.interp.interpret("remember My cat is Luna")
        self.assertEqual(goal.name, "REMEMBER")
        self.assertEqual(goal.parameters["content"], "My cat is Luna")

    def test_recall(self) -> None:
        goal = self.interp.interpret("recall cat")
        self.assertEqual(goal.name, "RECALL")
        self.assertEqual(goal.parameters["query"], "cat")

    def test_forget(self) -> None:
        goal = self.interp.interpret("forget abc123")
        self.assertEqual(goal.name, "FORGET")
        self.assertEqual(goal.parameters["memory_id"], "abc123")

    def test_list(self) -> None:
        goal = self.interp.interpret("list")
        self.assertEqual(goal.name, "LIST")

    def test_clear(self) -> None:
        goal = self.interp.interpret("clear")
        self.assertEqual(goal.name, "CLEAR")

    def test_help(self) -> None:
        goal = self.interp.interpret("help")
        self.assertEqual(goal.name, "HELP")

    def test_exit(self) -> None:
        goal = self.interp.interpret("exit")
        self.assertEqual(goal.name, "EXIT")

    def test_freeform(self) -> None:
        goal = self.interp.interpret("What is the weather?")
        self.assertEqual(goal.name, "USER_REQUEST")
        self.assertIn("weather", goal.parameters["input"])


# ═══════════════════════════════════════════════════════════════════════════════
#  Memory
# ═══════════════════════════════════════════════════════════════════════════════


class TestMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.mem = Memory()
        self.mem.load()

    def test_remember_and_recall(self) -> None:
        ep = self.mem.remember("My name is Sohail")
        self.assertIsInstance(ep, Episode)
        results = self.mem.recall("name")
        self.assertTrue(any("Sohail" in r.content for r in results))

    def test_recall_empty(self) -> None:
        self.assertEqual(self.mem.recall("anything"), [])

    def test_list_working_memory(self) -> None:
        self.mem.remember("fact one")
        self.mem.remember("fact two")
        all_mems = self.mem.get_working_memory()
        self.assertEqual(len(all_mems), 2)

    def test_forget(self) -> None:
        ep = self.mem.remember("temporary")
        self.assertTrue(self.mem.forget(ep.id[:8]))
        self.assertEqual(self.mem.get_working_memory(), [])

    def test_forget_not_found(self) -> None:
        self.assertFalse(self.mem.forget("nonexistent"))

    def test_clear(self) -> None:
        self.mem.remember("one")
        self.mem.remember("two")
        self.mem.clear()
        self.assertEqual(self.mem.get_working_memory(), [])


# ═══════════════════════════════════════════════════════════════════════════════
#  Planner
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlanner(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = Planner()
        self.planner.load()

    def test_conversation_plan(self) -> None:
        goal = Goal(name="USER_REQUEST", parameters={"input": "hello"})
        plan = self.planner.plan(goal, Context())
        self.assertEqual(plan.steps[0]["action"], "conversation")

    def test_memory_plan(self) -> None:
        goal = Goal(name="REMEMBER")
        plan = self.planner.plan(goal, Context())
        self.assertEqual(plan.steps[0]["action"], "memory")


# ═══════════════════════════════════════════════════════════════════════════════
#  MockProvider
# ═══════════════════════════════════════════════════════════════════════════════


class TestMockProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MockProvider()
        self.provider.load()

    def test_generate(self) -> None:
        result = self.provider.generate("hello")
        self.assertTrue(result.success)
        self.assertTrue(len(result.content) > 0)

    def test_stream(self) -> None:
        tokens = list(self.provider.stream("hello"))
        self.assertTrue(len(tokens) > 0)

    def test_provider_name(self) -> None:
        self.assertEqual(self.provider.provider_name, "MockProvider")

    def test_shutdown(self) -> None:
        self.provider.shutdown()
        self.assertFalse(self.provider.is_loaded())


# ═══════════════════════════════════════════════════════════════════════════════
#  Kernel (full pipeline with MockProvider)
# ═══════════════════════════════════════════════════════════════════════════════


class TestKernel(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.planner = Planner()
        self.provider = MockProvider()
        self.kernel = Kernel()
        for c in (self.memory, self.planner, self.provider, self.kernel):
            c.load()
        self.kernel.set_dependencies(
            planner=self.planner, memory=self.memory, provider=self.provider
        )

    def test_remember_then_recall(self) -> None:
        r = self.kernel.process("remember My name is Sohail", Context())
        self.assertTrue(r.success)
        self.assertIn("Sohail", r.content)

        r2 = self.kernel.process("recall name", Context())
        self.assertIn("Sohail", r2.content)

    def test_natural_question_uses_memory(self) -> None:
        self.kernel.process("remember My name is Sohail", Context())
        r = self.kernel.process("What is my name?", Context())
        self.assertTrue(r.success)
        self.assertEqual("Your name is Sohail.", r.content)

    def test_forget_removes_memory(self) -> None:
        r = self.kernel.process("remember My project is Alfa COS", Context())
        memory_id = r.content.rsplit("id: ", 1)[1].rstrip(")")
        f = self.kernel.process(f"forget {memory_id}", Context())
        self.assertTrue(f.success)
        self.assertEqual([], self.memory.recall("project"))

    def test_list_memories(self) -> None:
        self.kernel.process("remember fact one", Context())
        self.kernel.process("remember fact two", Context())
        r = self.kernel.process("list", Context())
        self.assertIn("fact one", r.content)
        self.assertIn("fact two", r.content)

    def test_clear_memories(self) -> None:
        self.kernel.process("remember something", Context())
        r = self.kernel.process("clear", Context())
        self.assertIn("cleared", r.content.lower())
        self.assertEqual(self.memory.get_working_memory(), [])

    def test_help(self) -> None:
        r = self.kernel.process("help", Context())
        self.assertIn("remember", r.content)
        self.assertIn("exit", r.content)

    def test_empty_input(self) -> None:
        r = self.kernel.process("", Context())
        self.assertTrue(r.success)

    def test_freeform_chat(self) -> None:
        r = self.kernel.process("hello", Context())
        self.assertTrue(r.success)
        self.assertTrue(len(r.content) > 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  Context Manager
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextManager(unittest.TestCase):
    def setUp(self) -> None:
        self.cm = ContextManager()
        self.cm.load()

    def test_build_context(self) -> None:
        goal = Goal(name="TEST", parameters={"input": "hello"})
        ctx = self.cm.build_context(goal=goal)
        self.assertEqual(ctx.current_task, "TEST")
        self.assertIsNotNone(ctx.time)

    def test_update_and_clear(self) -> None:
        self.cm.update_context("current_project", "Alfa")
        goal = Goal(name="T")
        ctx = self.cm.build_context(goal=goal)
        self.assertEqual(ctx.active_project, "Alfa")
        self.cm.clear()
        ctx2 = self.cm.build_context(goal=goal)
        self.assertIsNone(ctx2.active_project)


# ═══════════════════════════════════════════════════════════════════════════════
#  Runtime
# ═══════════════════════════════════════════════════════════════════════════════


class TestRuntime(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.runtime.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)

    def test_process(self) -> None:
        result = self.runtime.process("hello")
        self.assertTrue(result.success)

    def test_memory_via_runtime(self) -> None:
        self.runtime.process("remember My pet is a dog")
        r = self.runtime.process("recall pet")
        self.assertIn("dog", r.content)


# ═══════════════════════════════════════════════════════════════════════════════
#  Event Bus
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventBus(unittest.TestCase):
    def test_publish_subscribe(self) -> None:
        from prototype.common import Event, EventBus

        bus = EventBus()
        received = []
        bus.subscribe("test.event", lambda e: received.append(e))
        bus.publish(Event(event_type="test.event", payload={"x": 1}))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["x"], 1)

    def test_unsubscribe(self) -> None:
        from prototype.common import Event, EventBus

        bus = EventBus()
        received = []
        unsub = bus.subscribe("test.event", lambda e: received.append(e))
        bus.unsubscribe(unsub)
        bus.publish(Event(event_type="test.event"))
        self.assertEqual(len(received), 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  Provider Abstraction
# ═══════════════════════════════════════════════════════════════════════════════


class TestProviderAbstraction(unittest.TestCase):
    def test_mock_is_provider(self) -> None:
        self.assertIsInstance(MockProvider(), Provider)

    def test_provider_abc_enforced(self) -> None:
        # Cannot instantiate Provider directly
        with self.assertRaises(TypeError):
            Provider()


if __name__ == "__main__":
    unittest.main()
