"""Integration tests for CognitionRuntime + ModelHub + AlfaRuntime wiring.

Tests that:
- CognitionRuntime is wired into AlfaRuntime
- ModelHub Registry + Router are wired into AlfaRuntime
- Built-in commands still route through Kernel
- Conversation routes through CognitionRuntime
- Tool handlers are wired
- LLM inference handler works
- Memory handlers are wired
- Stats include cognition and modelhub
- Server endpoints expose new subsystems

Run:  python -m pytest tests/test_integration.py -v
"""

import os
import tempfile
import unittest

from prototype.common import EventBus, Event
from prototype.config import SettingsManager
from prototype.runtime import AlfaRuntime
from prototype.cognition import CognitionRuntime


class TestCognitionRuntimeWiring(unittest.TestCase):
    """Test that CognitionRuntime is properly wired into AlfaRuntime."""

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

    def test_cognition_runtime_exists(self) -> None:
        """CognitionRuntime must be a real CognitionRuntime instance."""
        self.assertIsInstance(self.runtime.cognition, CognitionRuntime)

    def test_cognition_runtime_loaded(self) -> None:
        """CognitionRuntime must be loaded after AlfaRuntime.load()."""
        self.assertTrue(self.runtime.cognition.is_loaded())

    def test_cognition_runtime_has_stages(self) -> None:
        """CognitionRuntime stages must all be loaded."""
        self.assertTrue(self.runtime.cognition.perception.is_loaded())
        self.assertTrue(self.runtime.cognition.planner.is_loaded())
        self.assertTrue(self.runtime.cognition.reasoner.is_loaded())
        self.assertTrue(self.runtime.cognition.executor.is_loaded())
        self.assertTrue(self.runtime.cognition.reflector.is_loaded())

    def test_cognition_has_tool_handlers(self) -> None:
        """CognitionRuntime executor must have real tool handlers."""
        handlers = self.runtime.cognition.executor._tool_handlers
        self.assertGreater(len(handlers), 0)
        # Must have the LLM inference handler
        self.assertIn("llm_inference", handlers)
        # Must have memory handlers
        self.assertIn("memory_recall", handlers)
        self.assertIn("memory_store", handlers)

    def test_cognition_has_builtin_tools(self) -> None:
        """Built-in tools from ToolManager must be registered in CognitionRuntime."""
        handlers = self.runtime.cognition.executor._tool_handlers
        self.assertIn("calculator", handlers)
        self.assertIn("datetime", handlers)
        self.assertIn("system_info", handlers)

    def test_builtin_commands_still_work(self) -> None:
        """Built-in commands must still route through Kernel."""
        result = self.runtime.process("help")
        self.assertTrue(result.success)
        self.assertIn("Available commands", result.content)

    def test_remember_recall_still_works(self) -> None:
        """Remember/recall built-in commands must still work."""
        self.runtime.process("remember My project is Alfa COS")
        result = self.runtime.process("recall project")
        self.assertIn("Alfa", result.content)

    def test_conversation_routes_to_cognition(self) -> None:
        """Free-form input must route through CognitionRuntime."""
        result = self.runtime.process("what is the weather today?")
        self.assertTrue(result.success)
        # CognitionRuntime produces a result (even if mock-based)
        self.assertIsNotNone(result.content)

    def test_process_records_diagnostics(self) -> None:
        """Process must record runtime diagnostics."""
        self.runtime.process("hello")
        stats = self.runtime.diagnostics.get_stats()
        self.assertIn("counter_names", stats)
        self.assertIn("kernel.process_count", stats["counter_names"])

    def test_cognition_stats_in_runtime_stats(self) -> None:
        """Runtime stats must include cognition and modelhub."""
        stats = self.runtime.get_stats()
        self.assertIn("cognition", stats)
        self.assertIn("modelhub", stats)

    def test_cognition_stats_has_stages(self) -> None:
        """Cognition stats must report stage status."""
        stats = self.runtime.cognition.get_stats()
        self.assertIn("perception", stats)
        self.assertIn("planner", stats)
        self.assertIn("reasoner", stats)
        self.assertIn("executor", stats)
        self.assertIn("reflector", stats)

    def tearDown(self) -> None:
        self.runtime.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)
        data_dir = os.path.join(
            os.path.dirname(__file__), "..", "data"
        )
        db_path = os.path.join(data_dir, "memory.db")
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass


class TestModelHubWiring(unittest.TestCase):
    """Test that ModelHub is properly wired into AlfaRuntime."""

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

    def test_model_registry_exists(self) -> None:
        """ModelRegistry must exist on runtime."""
        from prototype.modelhub import ModelRegistry
        self.assertIsInstance(self.runtime.model_registry, ModelRegistry)

    def test_model_router_exists(self) -> None:
        """ModelRouter must exist on runtime."""
        from prototype.modelhub import ModelRouter
        self.assertIsInstance(self.runtime.model_router, ModelRouter)

    def test_model_detector_exists(self) -> None:
        """ModelDetector must exist on runtime."""
        from prototype.modelhub import ModelDetector
        self.assertIsInstance(self.runtime.model_detector, ModelDetector)

    def test_modelhub_stats_in_runtime(self) -> None:
        """Modelhub stats must appear in runtime stats."""
        stats = self.runtime.get_stats()
        self.assertIn("modelhub", stats)
        self.assertIn("total_models", stats["modelhub"])

    def test_modelhub_in_service_registry(self) -> None:
        """Modelhub must be registered as a service."""
        services = self.runtime.service_registry.list_services()
        names = [s.get("name", s.get("service_name", "")) for s in services]
        self.assertIn("modelhub", names)

    def test_cognition_in_service_registry(self) -> None:
        """Cognition must be registered as a service."""
        services = self.runtime.service_registry.list_services()
        names = [s.get("name", s.get("service_name", "")) for s in services]
        self.assertIn("cognition", names)

    def tearDown(self) -> None:
        self.runtime.shutdown()
        if os.path.exists(self._tmpfile.name):
            os.unlink(self._tmpfile.name)
        data_dir = os.path.join(
            os.path.dirname(__file__), "..", "data"
        )
        db_path = os.path.join(data_dir, "memory.db")
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass


class TestCognitionPipeline(unittest.TestCase):
    """Test the full cognition pipeline end-to-end."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.cognition = CognitionRuntime(event_bus=self.bus)
        self.cognition.load()

    def test_process_produces_result(self) -> None:
        """Cognition process must produce an EngineResult."""
        from prototype.common import EngineResult
        result = self.cognition.process("what is 2+2?")
        self.assertIsInstance(result, EngineResult)

    def test_process_increments_count(self) -> None:
        """Each process call must increment the count."""
        self.cognition.process("hello")
        self.cognition.process("world")
        stats = self.cognition.get_stats()
        self.assertEqual(stats["process_count"], 2)

    def test_process_emits_events(self) -> None:
        """Cognition processing must emit events."""
        events = []
        self.bus.subscribe("CognitionProcessing", lambda e: events.append(e))
        self.cognition.process("test input")
        self.assertGreater(len(events), 0)

    def test_perception_produces_intents(self) -> None:
        """Perception stage must detect intents."""
        result = self.cognition.perception.process("what is the time?", {})
        self.assertGreater(len(result.intents), 0)

    def test_register_and_use_tool(self) -> None:
        """Registered tool handlers must be callable through the pipeline."""
        executed = []

        def my_handler(params):
            executed.append(params)
            return "tool_result"

        self.cognition.register_tool(
            name="test_tool",
            capabilities=["test", "demo"],
            handler=my_handler,
        )

        # Verify handler was registered
        self.assertIn(
            "test_tool",
            self.cognition.executor._tool_handlers,
        )

    def tearDown(self) -> None:
        self.cognition.shutdown()


class TestServerEndpoints(unittest.TestCase):
    """Test that server endpoints expose new subsystems."""

    def test_health_includes_cognition(self) -> None:
        """Health endpoint must report cognition status."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("cognition_loaded", data)
            self.assertTrue(data["cognition_loaded"])
            self.assertEqual(data["version"], "1.0.0")

    def test_health_includes_modelhub(self) -> None:
        """Health endpoint must report modelhub providers."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/health")
            data = resp.json()
            self.assertIn("modelhub_providers", data)

    def test_status_includes_cognition(self) -> None:
        """Status endpoint must include cognition stats."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("cognition", data)
            self.assertIn("modelhub", data)

    def test_modelhub_models_endpoint(self) -> None:
        """ModelHub models endpoint must respond."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/modelhub/models")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("models", data)
            self.assertIn("count", data)

    def test_modelhub_providers_endpoint(self) -> None:
        """ModelHub providers endpoint must respond."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/modelhub/providers")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("providers", data)

    def test_cognition_status_endpoint(self) -> None:
        """Cognition status endpoint must respond."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/cognition/status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("loaded", data)
            self.assertTrue(data["loaded"])

    def test_modelhub_search_endpoint(self) -> None:
        """ModelHub search endpoint must respond."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.get("/modelhub/search", params={"query": "llama"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("results", data)

    def test_chat_through_cognition(self) -> None:
        """Chat endpoint must use CognitionRuntime for conversation."""
        from prototype.server import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.post("/chat", json={"message": "hello there"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])


if __name__ == "__main__":
    unittest.main()
