"""OS Shell — the main application shell layout."""

from typing import Dict, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QFrame, QScrollArea, QLabel,
)
from PySide6.QtCore import Qt, QTimer

from prototype.desktop.tokens import colors, typography
from prototype.desktop.layouts.sidebar import Sidebar
from prototype.desktop.layouts.status_bars import TopBar, BottomBar


class RightPanel(QWidget):
    """Right intelligence panel — tools, recent events, system info."""

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self.setFixedWidth(280)
        self._runtime = runtime

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(12)

        # Tools section
        tools_title = QLabel("Tools")
        tools_title.setObjectName("subheading")
        self._content_layout.addWidget(tools_title)

        self._tools_container = QVBoxLayout()
        self._tools_container.setSpacing(4)
        self._content_layout.addLayout(self._tools_container)

        self._no_tools = QLabel("No tools loaded")
        self._no_tools.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        self._tools_container.addWidget(self._no_tools)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        self._content_layout.addWidget(sep)

        # Quick Info section
        info_title = QLabel("Quick Info")
        info_title.setObjectName("subheading")
        self._content_layout.addWidget(info_title)

        self._info_container = QVBoxLayout()
        self._info_container.setSpacing(4)
        self._content_layout.addLayout(self._info_container)

        # Separator
        sep2 = QFrame()
        sep2.setObjectName("separator")
        self._content_layout.addWidget(sep2)

        # Recent Events section
        events_title = QLabel("Recent Events")
        events_title.setObjectName("subheading")
        self._content_layout.addWidget(events_title)

        self._events_container = QVBoxLayout()
        self._events_container.setSpacing(4)
        self._content_layout.addLayout(self._events_container)

        self._no_events = QLabel("No events yet")
        self._no_events.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        self._events_container.addWidget(self._no_events)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            self._refresh_tools()
            self._refresh_info()
            self._refresh_events()
        except Exception:
            pass

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_tools(self) -> None:
        self._clear_layout(self._tools_container)
        stats = self._runtime.get_stats()
        tools = stats.get("tools", [])

        if not tools:
            self._tools_container.addWidget(self._no_tools)
            return

        for tool in tools[:8]:
            row = QLabel(f"  \u25B8 {tool['name']}")
            row.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_SM};")
            self._tools_container.addWidget(row)

    def _refresh_info(self) -> None:
        self._clear_layout(self._info_container)
        stats = self._runtime.get_stats()

        info_items = [
            ("Provider", stats.get("provider", "---")),
            ("Executions", str(stats.get("executive", {}).get("total_history", 0))),
            ("Memory", str(stats.get("memory", {}).get("working_count", 0) + stats.get("memory", {}).get("persistent_count", 0))),
            ("Workers", str(stats.get("workers", {}).get("worker_count", 0))),
            ("Agents", str(stats.get("agents", {}).get("agent_count", 0))),
        ]

        for label, value in info_items:
            row = QHBoxLayout()
            row.setSpacing(0)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
            row.addWidget(lbl)
            row.addStretch()
            val = QLabel(value)
            val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_SM}; font-weight: 500;")
            row.addWidget(val)
            container = QWidget()
            container.setLayout(row)
            self._info_container.addWidget(container)

    def _refresh_events(self) -> None:
        self._clear_layout(self._events_container)
        events = self._runtime.event_bus.get_history(limit=6)

        if not events:
            self._events_container.addWidget(self._no_events)
            return

        for event in reversed(events):
            ts = event.timestamp.strftime("%H:%M:%S") if hasattr(event.timestamp, 'strftime') else "??:??:??"
            row = QLabel(f"  {ts}  {event.event_type}")
            row.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: {typography.SIZE_SM};")
            self._events_container.addWidget(row)


class OSShell(QMainWindow):
    """Operating System shell layout.

    Structure:
    ┌────────────────────────────────────────────┐
    │                TopBar                       │
    ├────┬───────────────────────────┬───────────┤
    │    │                           │  Right    │
    │ S  │     Central Workspace     │  Panel    │
    │ i  │      (QStackedWidget)     │  280px    │
    │ d  │                           │           │
    │ e  │                           │           │
    │ b  │                           │           │
    ├────┴───────────────────────────┴───────────┤
    │              BottomBar                      │
    └────────────────────────────────────────────┘
    """

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.runtime = runtime
        self.setWindowTitle("ALFA COS \u2014 Cognition Operating System")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        self.top_bar = TopBar(runtime)
        main_layout.addWidget(self.top_bar)

        # Middle: sidebar + workspace + right panel
        middle = QWidget()
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.workspace_changed.connect(self._on_workspace_changed)
        middle_layout.addWidget(self.sidebar)

        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setObjectName("workspace")
        middle_layout.addWidget(self.workspace_stack, 1)

        self.right_panel = RightPanel(runtime)
        middle_layout.addWidget(self.right_panel)

        main_layout.addWidget(middle, 1)

        # Bottom bar
        self.bottom_bar = BottomBar(runtime)
        main_layout.addWidget(self.bottom_bar)

        self._workspaces: Dict[str, QWidget] = {}
        self._current_workspace: Optional[str] = None

        # Auto-refresh right panel
        self._panel_timer = QTimer(self)
        self._panel_timer.timeout.connect(self.right_panel.refresh)
        self._panel_timer.start(3000)

    def register_workspace(self, workspace_id: str, widget: QWidget) -> None:
        self._workspaces[workspace_id] = widget
        self.workspace_stack.addWidget(widget)

    def switch_workspace(self, workspace_id: str) -> None:
        if workspace_id in self._workspaces:
            self.workspace_stack.setCurrentWidget(self._workspaces[workspace_id])
            self.sidebar.set_active(workspace_id)
            self._current_workspace = workspace_id
            widget = self._workspaces[workspace_id]
            if hasattr(widget, "refresh"):
                widget.refresh()
            self.right_panel.refresh()

    def _on_workspace_changed(self, workspace_id: str) -> None:
        self.switch_workspace(workspace_id)

    def refresh_all(self) -> None:
        for widget in self._workspaces.values():
            if hasattr(widget, "refresh"):
                widget.refresh()
        self.top_bar.refresh()
        self.bottom_bar.refresh()
        self.right_panel.refresh()
