"""Alfa COS Desktop — main window using OS shell architecture."""

import logging
from typing import Optional, Tuple

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer

from prototype.runtime.alfa_runtime import AlfaRuntime
from prototype.desktop.tokens.stylesheet import build_stylesheet
from prototype.desktop.layouts.os_shell import OSShell
from prototype.desktop.workspaces import (
    DashboardView, ChatView, ModelHubView, MemoryView,
    AgentWorkspaceView, WorkersView, SettingsView, NotificationsView,
    PlannerView, TasksView, KnowledgeView, RuntimeView,
    ToolsView, FilesView, PluginsView,
)

logger = logging.getLogger("alfa.desktop")


class AlfaDesktopWindow(OSShell):
    """Main desktop window using the OS shell layout.

    Registers all 13 AI Operating System workspaces and manages lifecycle.
    """

    def __init__(self, runtime: AlfaRuntime, parent=None):
        super().__init__(runtime, parent)

        # Apply theme
        self.setStyleSheet(build_stylesheet())

        # Register standard 13 AI OS workspace modules
        self.register_workspace("dashboard", DashboardView(runtime))
        self.register_workspace("chat", ChatView(runtime))
        self.register_workspace("memory", MemoryView(runtime))
        self.register_workspace("planner", PlannerView(runtime))
        self.register_workspace("tasks", TasksView(runtime))
        self.register_workspace("knowledge", KnowledgeView(runtime))
        self.register_workspace("runtime", RuntimeView(runtime))
        self.register_workspace("model_hub", ModelHubView(runtime))
        self.register_workspace("agents", AgentWorkspaceView(runtime))
        self.register_workspace("tools", ToolsView(runtime))
        self.register_workspace("files", FilesView(runtime))
        self.register_workspace("plugins", PluginsView(runtime))
        self.register_workspace("settings", SettingsView(runtime))
        self.register_workspace("notifications", NotificationsView(runtime))

        # Start on dashboard
        self.switch_workspace("dashboard")


        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(5000)

        logger.info("Desktop window initialized")

    def _auto_refresh(self) -> None:
        """Periodically refresh status bars and current workspace."""
        self.top_bar.refresh()
        self.bottom_bar.refresh()

    def closeEvent(self, event) -> None:
        """Clean shutdown."""
        self._refresh_timer.stop()
        if self.runtime:
            self.runtime.shutdown()
        event.accept()


def launch_desktop(runtime: AlfaRuntime) -> Tuple[QApplication, AlfaDesktopWindow]:
    """Create and show the desktop application.

    Returns:
        Tuple of (QApplication, AlfaDesktopWindow) for the caller to manage the event loop.
    """
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

    window = AlfaDesktopWindow(runtime)
    window.show()

    return app, window
