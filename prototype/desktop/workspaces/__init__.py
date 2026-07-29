"""ALFA COS Desktop Workspaces."""

from .dashboard import DashboardView
from .chat import ChatView
from .model_hub import ModelHubView
from .memory import MemoryView
from .agents import AgentWorkspaceView
from .workers import WorkersView
from .settings import SettingsView
from .notifications import NotificationsView
from .planner import PlannerView
from .tasks import TasksView
from .knowledge import KnowledgeView
from .runtime import RuntimeView
from .tools import ToolsView
from .files import FilesView
from .plugins import PluginsView
from .hud.hud_view import HudView

__all__ = [
    "DashboardView", "ChatView", "ModelHubView", "MemoryView",
    "AgentWorkspaceView", "WorkersView", "SettingsView", "NotificationsView",
    "PlannerView", "TasksView", "KnowledgeView", "RuntimeView",
    "ToolsView", "FilesView", "PluginsView", "HudView",
]

