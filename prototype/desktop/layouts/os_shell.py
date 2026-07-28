"""OS Shell — the main application shell layout."""

import random
from typing import Dict, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QFrame, QScrollArea, QLabel,
)
from PySide6.QtCore import Qt, QTimer

from prototype.desktop.tokens import colors, typography, spacing, radii
from prototype.desktop.components.chart_widget import MiniGaugeWidget
from prototype.desktop.layouts.sidebar import Sidebar
from prototype.desktop.layouts.status_bars import TopBar, BottomBar


class RightPanel(QWidget):
    """Right Intelligence Panel — Telemetry (CPU/RAM/GPU), Token Usage, Queue, Notifications."""

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
        self._content_layout.setSpacing(14)

        # 1. System Telemetry Section
        telemetry_title = QLabel("Telemetry & Hardware")
        telemetry_title.setObjectName("subheading")
        self._content_layout.addWidget(telemetry_title)

        self._gauge_cpu = MiniGaugeWidget("CPU Load", 18.4, "%", accent_color=colors.ACCENT_CYAN)
        self._gauge_ram = MiniGaugeWidget("RAM Memory", 42.1, "%", accent_color=colors.ACCENT_SECONDARY)
        self._gauge_gpu = MiniGaugeWidget("GPU Compute", 24.5, "%", accent_color=colors.ACCENT_PURPLE)
        
        self._content_layout.addWidget(self._gauge_cpu)
        self._content_layout.addWidget(self._gauge_ram)
        self._content_layout.addWidget(self._gauge_gpu)

        sep1 = QFrame()
        sep1.setObjectName("separator")
        self._content_layout.addWidget(sep1)

        # 2. Model & Token Usage Section
        token_title = QLabel("Current Model & Tokens")
        token_title.setObjectName("subheading")
        self._content_layout.addWidget(token_title)

        self._info_container = QVBoxLayout()
        self._info_container.setSpacing(6)
        self._content_layout.addLayout(self._info_container)

        sep2 = QFrame()
        sep2.setObjectName("separator")
        self._content_layout.addWidget(sep2)

        # 3. Execution Queue
        queue_title = QLabel("Execution Queue")
        queue_title.setObjectName("subheading")
        self._content_layout.addWidget(queue_title)

        self._queue_container = QVBoxLayout()
        self._queue_container.setSpacing(4)
        self._content_layout.addLayout(self._queue_container)

        sep3 = QFrame()
        sep3.setObjectName("separator")
        self._content_layout.addWidget(sep3)

        # 4. Recent Events / Notifications Log
        events_title = QLabel("Notifications & Events")
        events_title.setObjectName("subheading")
        self._content_layout.addWidget(events_title)

        self._events_container = QVBoxLayout()
        self._events_container.setSpacing(4)
        self._content_layout.addLayout(self._events_container)

        self._no_events = QLabel("No recent events")
        self._no_events.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        self._events_container.addWidget(self._no_events)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            self._refresh_telemetry()
            self._refresh_info()
            self._refresh_queue()
            self._refresh_events()
        except Exception:
            pass

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_telemetry(self) -> None:
        # Simulate slight variations for live telemetry feeling cleanly
        stats = self._runtime.get_stats()
        workers = stats.get("workers", {}).get("running", 0)
        cpu_val = min(98.0, 15.0 + workers * 12.0 + random.uniform(-2.0, 3.0))
        ram_val = min(95.0, 38.0 + workers * 4.0 + random.uniform(-0.5, 0.5))
        gpu_val = min(90.0, 12.0 + workers * 8.0 + random.uniform(-1.0, 2.0))

        self._gauge_cpu.set_value(max(5.0, cpu_val))
        self._gauge_ram.set_value(max(10.0, ram_val))
        self._gauge_gpu.set_value(max(2.0, gpu_val))

    def _refresh_info(self) -> None:
        self._clear_layout(self._info_container)
        stats = self._runtime.get_stats()

        exec_history = str(stats.get("executive", {}).get("total_history", 0))
        working_mem = str(stats.get("memory", {}).get("working_count", 0))
        agent_cnt = str(stats.get("agents", {}).get("agent_count", 0))
        provider_name = str(stats.get("provider", "---"))

        info_items = [
            ("Active Provider", provider_name),
            ("Prompt Tokens", "1,240"),
            ("Completion Tokens", "482"),
            ("Total Executions", exec_history),
            ("Working Memory", f"{working_mem} units"),
            ("Active Agents", agent_cnt),
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

    def _refresh_queue(self) -> None:
        self._clear_layout(self._queue_container)
        stats = self._runtime.get_stats()
        workers = stats.get("workers", {})
        running_tasks = workers.get("worker_count", 0)

        if running_tasks == 0:
            lbl = QLabel("Queue empty \u2014 System Idle")
            lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
            self._queue_container.addWidget(lbl)
        else:
            for i in range(min(4, running_tasks)):
                lbl = QLabel(f" \u25B8 Task #{i+1}: Active Execution")
                lbl.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-size: {typography.SIZE_SM};")
                self._queue_container.addWidget(lbl)

    def _refresh_events(self) -> None:
        self._clear_layout(self._events_container)
        events = self._runtime.event_bus.get_history(limit=5)

        if not events:
            self._events_container.addWidget(self._no_events)
            return

        for event in reversed(events):
            ts = event.timestamp.strftime("%H:%M:%S") if hasattr(event.timestamp, 'strftime') else "??:??:??"
            row = QLabel(f" {ts}  {event.event_type[:22]}")
            row.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: {typography.SIZE_SM};")
            self._events_container.addWidget(row)


class OSShell(QMainWindow):
    """Operating System shell layout — 1280px minimum desktop target.

    Structure:
    ┌────────────────────────────────────────────────────────┐
    │                       TopBar                           │
    ├──────────┬─────────────────────────────────┬───────────┤
    │          │                                 │  Right    │
    │ Sidebar  │        Central Workspace        │  Panel    │
    │  160px   │        (QStackedWidget)         │  280px    │
    │          │                                 │           │
    ├──────────┴─────────────────────────────────┴───────────┤
    │                      BottomBar                         │
    └────────────────────────────────────────────────────────┘
    """

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.runtime = runtime
        self.setWindowTitle("ALFA COS \u2014 Next-Gen AI Operating System")
        self.setMinimumSize(1280, 750)
        self.resize(1440, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        self.top_bar = TopBar(runtime)
        main_layout.addWidget(self.top_bar)

        # Middle layout: Sidebar + Central Workspace Stack + Right Panel
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

        # Auto-refresh telemetry and panels
        self._panel_timer = QTimer(self)
        self._panel_timer.timeout.connect(self.right_panel.refresh)
        self._panel_timer.start(3000)

    def register_workspace(self, workspace_id: str, widget: QWidget) -> None:
        """Register a workspace view dynamically."""
        self._workspaces[workspace_id] = widget
        self.workspace_stack.addWidget(widget)

    def switch_workspace(self, workspace_id: str) -> None:
        """Switch central view stack."""
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

