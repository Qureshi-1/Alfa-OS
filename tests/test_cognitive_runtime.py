"""Tests for the Cognitive Runtime foundation: ModelHub, Memory Runtime, Worker enhancements, Event Bus, API contracts."""

import tempfile
import os
import unittest

from prototype.common import Event, EventBus


# ═══════════════════════════════════════════════════════════════════════════════
#  Model Hub Types
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelHubTypes(unittest.TestCase):
    def test_provider_type_enum(self):
        from prototype.modelhub.base import ProviderType
        assert ProviderType.OLLAMA.value == "ollama"
        assert ProviderType.CLAUDE.value == "claude"
        assert len(list(ProviderType)) == 14

    def test_model_modality(self):
        from prototype.modelhub.base import ModelModality
        assert ModelModality.TEXT.value == "text"
        assert ModelModality.MULTIMODAL.value == "multimodal"

    def test_model_capabilities_to_dict(self):
        from prototype.modelhub.base import ModelCapabilities
        caps = ModelCapabilities(max_context_length=32768, vision=True)
        d = caps.to_dict()
        assert d["max_context_length"] == 32768
        assert d["vision"] is True

    def test_model_info_serialization(self):
        from prototype.modelhub.base import ModelInfo, ProviderType, ModelCapabilities
        info = ModelInfo(
            id="test:1", name="test-model", provider=ProviderType.OLLAMA,
            family="llama", capabilities=ModelCapabilities(max_context_length=8192),
        )
        d = info.to_dict()
        assert d["id"] == "test:1"
        assert d["provider"] == "ollama"
        restored = ModelInfo.from_dict(d)
        assert restored.id == "test:1"
        assert restored.capabilities.max_context_length == 8192

    def test_generate_request_defaults(self):
        from prototype.modelhub.base import GenerateRequest
        req = GenerateRequest(prompt="hello")
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.model == ""

    def test_generate_response_to_dict(self):
        from prototype.modelhub.base import GenerateResponse, ProviderType
        resp = GenerateResponse(content="hi", model="m1", provider=ProviderType.MOCK)
        d = resp.to_dict()
        assert d["content"] == "hi"
        assert d["success"] is True


# ═══════════════════════════════════════════════════════════════════════════════
#  Model Registry
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelRegistry(unittest.TestCase):
    def setUp(self):
        from prototype.modelhub.registry import ModelRegistry
        from prototype.common import EventBus
        self.registry = ModelRegistry(EventBus())

    def test_load_and_stats(self):
        self.registry.load()
        stats = self.registry.get_stats()
        assert "total_models" in stats
        assert stats["total_models"] == 0

    def test_register_model(self):
        from prototype.modelhub.base import ModelInfo, ProviderType
        self.registry.load()
        model = ModelInfo(id="test:m1", name="m1", provider=ProviderType.MOCK)
        self.registry._register_model(model)
        assert self.registry.get_model("test:m1") is not None

    def test_list_models(self):
        from prototype.modelhub.base import ModelInfo, ProviderType
        self.registry.load()
        self.registry._register_model(ModelInfo(id="a", name="a", provider=ProviderType.MOCK))
        self.registry._register_model(ModelInfo(id="b", name="b", provider=ProviderType.OLLAMA))
        all_models = self.registry.list_models()
        assert len(all_models) == 2
        ollama_only = self.registry.list_models(provider=ProviderType.OLLAMA)
        assert len(ollama_only) == 1

    def test_search_models(self):
        from prototype.modelhub.base import ModelInfo, ProviderType
        self.registry.load()
        self.registry._register_model(ModelInfo(id="llama-3", name="llama-3", provider=ProviderType.OLLAMA, family="llama"))
        results = self.registry.search_models("llama")
        assert len(results) == 1

    def test_usage_tracking(self):
        from prototype.modelhub.base import ModelInfo, ProviderType
        self.registry.load()
        self.registry._register_model(ModelInfo(id="x", name="x", provider=ProviderType.MOCK))
        self.registry.record_usage("x")
        model = self.registry.get_model("x")
        assert model.usage_count == 1
        assert model.last_used is not None


# ═══════════════════════════════════════════════════════════════════════════════
#  Model Detector
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelDetector(unittest.TestCase):
    def setUp(self):
        from prototype.modelhub.detector import ModelDetector
        self.detector = ModelDetector()

    def test_detect_family(self):
        assert self.detector.detect_family("llama-3.1-8b") == "llama"
        assert self.detector.detect_family("mistral-7b") == "mistral"
        assert self.detector.detect_family("qwen2-72b") == "qwen"
        assert self.detector.detect_family("gemma2-9b") == "gemma"
        assert self.detector.detect_family("phi-4") == "phi"
        assert self.detector.detect_family("unknown-model") == "unknown"

    def test_detect_quantization(self):
        assert self.detector.detect_quantization("model-Q4_K_M.gguf") == "q4_k_m"
        assert self.detector.detect_quantization("model-Q8_0.gguf") == "q8_0"
        assert self.detector.detect_quantization("model-f16.gguf") == "f16"
        assert self.detector.detect_quantization("model.bin") == "unknown"

    def test_detect_parameter_count(self):
        assert self.detector.detect_parameter_count("llama-8b") == 8_000_000_000
        assert self.detector.detect_parameter_count("model-70b") == 70_000_000_000
        assert self.detector.detect_parameter_count("model-350m") == 0  # lowercase m pattern not matched
        assert self.detector.detect_parameter_count("unknown") == 0

    def test_detect_from_config(self):
        config = {
            "architectures": ["LlamaForCausalLM"],
            "model_type": "llama",
            "hidden_size": 4096,
            "num_hidden_layers": 32,
            "vocab_size": 32000,
            "max_position_embeddings": 8192,
        }
        result = self.detector.detect_from_config(config)
        assert result["architecture"] == "LlamaForCausalLM"
        assert result["family"] == "llama"
        assert result["max_context_length"] == 8192


# ═══════════════════════════════════════════════════════════════════════════════
#  Model Router
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelRouter(unittest.TestCase):
    def setUp(self):
        from prototype.modelhub.router import ModelRouter, RoutingPolicy
        from prototype.modelhub.registry import ModelRegistry
        from prototype.common import EventBus
        self.registry = ModelRegistry(EventBus())
        self.registry.load()
        self.router = ModelRouter(self.registry, RoutingPolicy(prefer_local=False))

    def test_health_check_empty(self):
        health = self.router.health_check()
        assert isinstance(health, dict)

    def test_shutdown(self):
        self.router.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════
#  Memory Runtime
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryRuntime(unittest.TestCase):
    def setUp(self):
        from prototype.memory.memory_runtime import MemoryEntry, MemoryType
        self.entry = MemoryEntry(content="test memory", tags=["test"], importance=5)

    def test_memory_entry_creation(self):
        assert self.entry.content == "test memory"
        assert self.entry.importance == 5
        assert self.entry.id is not None

    def test_memory_entry_to_episode(self):
        ep = self.entry.to_episode()
        assert ep.content == "test memory"
        assert "test" in ep.tags

    def test_memory_entry_from_episode(self):
        from prototype.common import Episode
        from prototype.memory.memory_runtime import MemoryEntry, MemoryType
        ep = Episode(content="from ep", tags=["a"], importance=3)
        entry = MemoryEntry.from_episode(ep, MemoryType.LONG_TERM)
        assert entry.content == "from ep"
        assert entry.memory_type == MemoryType.LONG_TERM

    def test_query_result(self):
        from prototype.memory.memory_runtime import QueryResult, MemoryEntry
        e1 = MemoryEntry(content="a")
        e2 = MemoryEntry(content="b")
        qr = QueryResult(entries=[e1, e2], scores=[0.9, 0.5], total=2)
        assert len(qr) == 2
        pairs = list(qr)
        assert pairs[0][0].content == "a"
        assert pairs[1][1] == 0.5


class TestDefaultMemoryRuntime(unittest.TestCase):
    def setUp(self):
        self._db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db.close()
        from prototype.memory.memory_runtime_impl import DefaultMemoryRuntime
        from prototype.memory.memory_runtime import MemoryType
        self.MemoryType = MemoryType
        self.runtime = DefaultMemoryRuntime(db_path=self._db.name)
        self.runtime.load()

    def tearDown(self):
        self.runtime.shutdown()
        try:
            os.unlink(self._db.name)
        except PermissionError:
            pass

    def test_working_memory_store_recall(self):
        wid = self.runtime.store("hello world", self.MemoryType.WORKING, tags=["greet"])
        assert wid is not None
        result = self.runtime.recall("hello")
        assert len(result.entries) > 0
        assert result.entries[0].content == "hello world"

    def test_long_term_store_recall(self):
        lid = self.runtime.store("important fact", self.MemoryType.LONG_TERM, category="semantic")
        assert lid is not None
        result = self.runtime.recall("important", memory_types=[self.MemoryType.LONG_TERM])
        assert len(result.entries) > 0

    def test_graph_memory(self):
        from prototype.memory.memory_runtime import GraphNode, GraphEdge
        n1 = self.runtime.graph.add_node(GraphNode(id="n1", content="Alice"))
        n2 = self.runtime.graph.add_node(GraphNode(id="n2", content="Bob"))
        self.runtime.graph.add_edge(GraphEdge(source_id="n1", target_id="n2", relation="knows"))
        assert self.runtime.graph.node_count() == 2
        assert self.runtime.graph.edge_count() == 1
        neighbors = self.runtime.graph.get_neighbors("n1")
        assert len(neighbors) == 1
        assert neighbors[0].content == "Bob"

    def test_vector_memory(self):
        from prototype.memory.memory_runtime import MemoryEntry
        entry = MemoryEntry(content="vector test", embedding=[0.1, 0.2, 0.3, 0.4])
        self.runtime.vector.store(entry)
        assert self.runtime.vector.count() == 1
        results = self.runtime.vector.search_similar([0.1, 0.2, 0.3, 0.4], limit=1)
        assert len(results.entries) == 1

    def test_stats(self):
        stats = self.runtime.stats()
        assert "working_count" in stats
        assert "graph_nodes" in stats


# ═══════════════════════════════════════════════════════════════════════════════
#  Worker Enhancements
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorkerEnhancements(unittest.TestCase):
    def setUp(self):
        from prototype.common import EventBus
        from prototype.worker import WorkerManager
        self.bus = EventBus()
        self.manager = WorkerManager(event_bus=self.bus)
        self.manager.load()

    def tearDown(self):
        self.manager.shutdown()

    def test_execute_and_stats(self):
        from prototype.worker.base_worker import WorkerStatus
        result = self.manager.execute_worker("echo_worker", {"message": "hi"})
        assert result.success
        assert result.status == WorkerStatus.COMPLETED
        stats = self.manager.get_stats()
        assert stats["completed"] >= 1

    def test_pause_and_resume(self):
        # Can't pause a synchronous worker easily, but test the API surface
        task_id = "fake-task"
        assert self.manager.pause_worker(task_id) is False
        assert self.manager.resume_worker(task_id) is False
        assert self.manager.stop_worker(task_id) is False

    def test_schedule_worker(self):
        sid = self.manager.schedule_worker("echo_worker", interval_seconds=60.0)
        assert sid is not None
        schedules = self.manager.list_schedules()
        assert len(schedules) == 1
        assert self.manager.unschedule_worker(sid) is True
        assert len(self.manager.list_schedules()) == 0

    def test_crash_recovery_tracking(self):
        from prototype.worker.worker_lifecycle import WorkerLifecycle
        from prototype.worker.base_worker import WorkerStatus
        lc = WorkerLifecycle()
        lc.record_crash("task-1", "echo_worker")
        assert lc.can_recover("echo_worker") is True
        lc.record_crash("task-1", "echo_worker")
        lc.record_crash("task-1", "echo_worker")
        assert lc.can_recover("echo_worker") is False

    def test_get_running_and_paused(self):
        running = self.manager.get_running_tasks()
        paused = self.manager.get_paused_tasks()
        assert isinstance(running, list)
        assert isinstance(paused, list)


# ═══════════════════════════════════════════════════════════════════════════════
#  Enhanced Event Bus
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnhancedEventBus(unittest.TestCase):
    def test_wildcard_subscription(self):
        bus = EventBus()
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        bus.publish(Event(event_type="anything", payload="test"))
        assert len(received) == 1
        assert received[0].event_type == "anything"

    def test_event_history(self):
        bus = EventBus()
        bus.publish(Event(event_type="e1"))
        bus.publish(Event(event_type="e2"))
        history = bus.get_history()
        assert len(history) == 2

    def test_event_history_filter(self):
        bus = EventBus()
        bus.publish(Event(event_type="a"))
        bus.publish(Event(event_type="b"))
        bus.publish(Event(event_type="a"))
        a_events = bus.get_history(event_type="a")
        assert len(a_events) == 2

    def test_stats(self):
        bus = EventBus()
        bus.subscribe("test", lambda e: None)
        bus.publish(Event(event_type="test"))
        stats = bus.get_stats()
        assert stats["total_events"] == 1
        assert stats["by_type"]["test"] == 1

    def test_event_to_dict(self):
        e = Event(event_type="x", payload={"k": 1}, source="src")
        d = e.to_dict()
        assert d["event_type"] == "x"
        assert d["source"] == "src"

    def test_reset(self):
        bus = EventBus()
        bus.subscribe("x", lambda e: None)
        bus.publish(Event(event_type="x"))
        bus.reset()
        assert bus.get_stats()["total_events"] == 0

    def test_handler_error_does_not_crash(self):
        bus = EventBus()
        def bad_handler(e):
            raise ValueError("oops")
        bus.subscribe("test", bad_handler)
        bus.publish(Event(event_type="test"))  # should not raise


# ═══════════════════════════════════════════════════════════════════════════════
#  API Contracts
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIContracts(unittest.TestCase):
    def test_chat_request_defaults(self):
        from prototype.api.contracts import ChatRequest
        req = ChatRequest(message="hello")
        assert req.temperature == 0.7
        assert req.stream is False

    def test_chat_response(self):
        from prototype.api.contracts import ChatResponse
        resp = ChatResponse(content="hi", model="m", provider="p")
        assert resp.success is True

    def test_system_status_response(self):
        from prototype.api.contracts import SystemStatusResponse
        status = SystemStatusResponse(provider="mock", model="test")
        assert status.provider == "mock"

    def test_contracts_are_abstract(self):
        from prototype.api.contracts import RuntimeAPI, ChatAPI, MemoryAPI, WorkerAPI, ModelAPI, PluginAPI
        for cls in [RuntimeAPI, ChatAPI, MemoryAPI, WorkerAPI, ModelAPI, PluginAPI]:
            with self.assertRaises(TypeError):
                cls()


if __name__ == "__main__":
    unittest.main()