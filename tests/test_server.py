"""Integration tests for Alfa COS FastAPI Server."""

import unittest
from fastapi.testclient import TestClient

from prototype.server import app


class TestAlfaServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_healthcheck(self):
        with TestClient(app) as client:
            resp = client.get("/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("provider", data)

            resp_z = client.get("/healthz")
            self.assertEqual(resp_z.status_code, 200)

    def test_chat_endpoint(self):
        with TestClient(app) as client:
            resp = client.post("/chat", json={"message": "Hello Alfa!"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["success"])
            self.assertIsNotNone(data["reply"])
            self.assertIn("provider_used", data)
            self.assertIn("latency_ms", data)

    def test_status_endpoint(self):
        with TestClient(app) as client:
            resp = client.get("/status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("provider", data)
            self.assertIn("executive", data)
            self.assertIn("memory", data)

    def test_memory_endpoints(self):
        with TestClient(app) as client:
            # Memory view
            resp = client.get("/memory")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("working_memory", resp.json())

            # Memory history
            resp_hist = client.get("/memory/history")
            self.assertEqual(resp_hist.status_code, 200)

            # Memory search
            resp_search = client.get("/memory/search?query=hello")
            self.assertEqual(resp_search.status_code, 200)

            # Clear memory
            resp_clear = client.post("/memory/clear", json={"target": "working"})
            self.assertEqual(resp_clear.status_code, 200)
            self.assertTrue(resp_clear.json()["success"])

    def test_providers_endpoints(self):
        with TestClient(app) as client:
            resp = client.get("/providers")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("active_provider", data)
            self.assertIn("valid_providers", data)

            # Switch to mock provider
            resp_switch = client.post("/providers/switch", json={"provider": "mock"})
            self.assertEqual(resp_switch.status_code, 200)
            self.assertEqual(resp_switch.json()["provider"], "mock")

    def test_plugins_endpoints(self):
        with TestClient(app) as client:
            resp = client.get("/plugins")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("tools", resp.json())

    def test_settings_endpoints(self):
        with TestClient(app) as client:
            resp = client.get("/settings")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("provider", resp.json())

            resp_update = client.post("/settings", json={"temperature": 0.8, "theme": "dark"})
            self.assertEqual(resp_update.status_code, 200)
            self.assertTrue(resp_update.json()["success"])

    def test_goal_and_task_endpoints(self):
        with TestClient(app) as client:
            resp_goal = client.post("/goal", json={"name": "test_goal", "parameters": {}})
            self.assertEqual(resp_goal.status_code, 200)
            self.assertTrue(resp_goal.json()["success"])

            resp_task = client.post("/task", json={"action": "create", "name": "test_task"})
            self.assertEqual(resp_task.status_code, 200)

            resp_tasks_list = client.get("/tasks/list")
            self.assertEqual(resp_tasks_list.status_code, 200)
            self.assertIn("history", resp_tasks_list.json())

    def test_workers_endpoints(self):
        with TestClient(app) as client:
            resp_workers = client.get("/workers")
            self.assertEqual(resp_workers.status_code, 200)
            data = resp_workers.json()
            self.assertIn("workers", data)

            resp_exec = client.post("/workers/execute", json={"worker_name": "echo_worker", "parameters": {"message": "hello"}})
            self.assertEqual(resp_exec.status_code, 200)
            self.assertTrue(resp_exec.json()["success"])

    def test_reflection_and_learn_endpoints(self):
        with TestClient(app) as client:
            resp_learn = client.post("/learn", json={"insight": "Always double-check configurations", "confidence": 0.95})
            self.assertEqual(resp_learn.status_code, 200)
            self.assertTrue(resp_learn.json()["success"])


if __name__ == "__main__":
    unittest.main()
