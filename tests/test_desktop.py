"""Tests for the PySide6 Desktop application."""

import sys
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from prototype.runtime.alfa_runtime import AlfaRuntime
from prototype.desktop.main_window import AlfaDesktopWindow


class TestDesktopApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.runtime = AlfaRuntime()
        self.runtime.load()
        self.window = AlfaDesktopWindow(self.runtime)

    def test_window_title(self):
        self.assertIn("ALFA COS", self.window.windowTitle())

    def test_workspace_count(self):
        self.assertEqual(self.window.workspace_stack.count(), 8)

    def test_sidebar_items(self):
        self.assertEqual(len(self.window.sidebar._buttons), 8)

    def test_stylesheet_applied(self):
        self.assertGreater(len(self.window.styleSheet()), 1000)

    def test_switch_workspace(self):
        self.window.switch_workspace("chat")
        self.assertEqual(self.window.sidebar.get_active(), "chat")

    def test_top_bar_refresh(self):
        self.window.top_bar.refresh()

    def test_bottom_bar_refresh(self):
        self.window.bottom_bar.refresh()

    def test_dashboard_refresh(self):
        ws = self.window._workspaces["dashboard"]
        ws.refresh()

    def test_chat_workspace_exists(self):
        ws = self.window._workspaces["chat"]
        self.assertIsNotNone(ws._input)
        self.assertIsNotNone(ws._send_btn)

    def test_memory_workspace_refresh(self):
        ws = self.window._workspaces["memory"]
        ws.refresh()

    def test_model_hub_workspace_refresh(self):
        ws = self.window._workspaces["model_hub"]
        ws.refresh()

    def test_agents_workspace_refresh(self):
        ws = self.window._workspaces["agents"]
        ws.refresh()

    def test_workers_workspace_refresh(self):
        ws = self.window._workspaces["workers"]
        ws.refresh()

    def test_settings_workspace_refresh(self):
        ws = self.window._workspaces["settings"]
        ws.refresh()

    def test_notifications_workspace_refresh(self):
        ws = self.window._workspaces["notifications"]
        ws.refresh()

    def tearDown(self):
        self.window.close()
        self.runtime.shutdown()


if __name__ == "__main__":
    unittest.main()
