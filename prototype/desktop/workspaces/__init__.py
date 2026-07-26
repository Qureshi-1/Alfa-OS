"""ALFA COS Desktop Workspaces."""

from .dashboard import DashboardView
from .chat import ChatView
from .model_hub import ModelHubView
from .memory import MemoryView
from .agents import AgentWorkspaceView
from .workers import WorkersView
from .settings import SettingsView
from .notifications import NotificationsView

__all__ = [
    "DashboardView", "ChatView", "ModelHubView", "MemoryView",
    "AgentWorkspaceView", "WorkersView", "SettingsView", "NotificationsView",
]
