"""Dashboard workspace — system overview with metrics, health, execution graph, and activity."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.status_indicator import StatusIndicator
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.components.chart_widget import ExecutionGraphWidget
from prototype.desktop.tokens import colors, typography, spacing, radii


class DashboardView(BaseView):
    """System overview dashboard with real-time metrics, activity graph, and quick actions."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header = self._make_header("Dashboard", "ALFA COS System Overview & Intelligence Control")
        layout.addWidget(header)

        # Metrics row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        self.metric_provider = MetricCard("Provider", "Ready")
        self.metric_model = MetricCard("Model", "---")
        self.metric_executions = MetricCard("Executions", "0")
        self.metric_quality = MetricCard("Quality Score", "---")
        self.metric_memory = MetricCard("Knowledge Size", "0")
        self.metric_agents = MetricCard("Active Agents", "0")

        for card in [self.metric_provider, self.metric_model, self.metric_executions,
                     self.metric_quality, self.metric_memory, self.metric_agents]:
            metrics_row.addWidget(card)
        layout.addLayout(metrics_row)

        # Quick Actions Bar
        actions_card = QFrame()
        actions_card.setObjectName("card")
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(16, 10, 16, 10)
        actions_layout.setSpacing(12)

        lbl = QLabel("Quick Actions:")
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-weight: {typography.WEIGHT_SEMIBOLD}; font-size: {typography.SIZE_SM};")
        actions_layout.addWidget(lbl)

        btn_run = QPushButton("+ New Task")
        btn_run.setObjectName("primary")
        actions_layout.addWidget(btn_run)

        btn_diag = QPushButton("Run Diagnostics")
        actions_layout.addWidget(btn_diag)

        btn_mem = QPushButton("Memory Inspector")
        actions_layout.addWidget(btn_mem)

        btn_ref = QPushButton("Refresh Status")
        btn_ref.clicked.connect(self.refresh)
        actions_layout.addWidget(btn_ref)

        actions_layout.addStretch()
        layout.addWidget(actions_card)

        # Execution Graph + System Health Row
        graph_health_row = QHBoxLayout()
        graph_health_row.setSpacing(16)

        # Left: Execution Activity Graph
        graph_card = QFrame()
        graph_card.setObjectName("card")
        graph_layout = QVBoxLayout(graph_card)
        graph_layout.setContentsMargins(16, 14, 16, 14)
        graph_layout.setSpacing(10)

        graph_title = QLabel("Execution Activity Graph")
        graph_title.setObjectName("subheading")
        graph_layout.addWidget(graph_title)

        self.exec_graph = ExecutionGraphWidget()
        graph_layout.addWidget(self.exec_graph)
        graph_health_row.addWidget(graph_card, 2)

        # Right: System Health Indicators
        health_card = QFrame()
        health_card.setObjectName("card")
        health_layout = QVBoxLayout(health_card)
        health_layout.setContentsMargins(16, 14, 16, 14)
        health_layout.setSpacing(8)

        health_title = QLabel("System Health")
        health_title.setObjectName("subheading")
        health_layout.addWidget(health_title)

        self.status_items = {}
        for name in ["kernel", "memory", "provider", "tools", "plugins", "workers", "agents"]:
            si = StatusIndicator(name.capitalize())
            health_layout.addWidget(si)
            self.status_items[name] = si

        health_layout.addStretch()
        graph_health_row.addWidget(health_card, 1)

        layout.addLayout(graph_health_row)

        # Bottom Row: Recent Activity
        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(16, 14, 16, 14)
        activity_layout.setSpacing(8)

        activity_title = QLabel("Recent System Activity")
        activity_title.setObjectName("subheading")
        activity_layout.addWidget(activity_title)

        self._activity_container = QVBoxLayout()
        self._activity_container.setSpacing(4)
        activity_layout.addLayout(self._activity_container)

        self._empty_activity = EmptyState("No recent activity recorded", "Events will stream here automatically")
        self._activity_container.addWidget(self._empty_activity)

        layout.addWidget(activity_card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()

            # Metrics
            self.metric_provider.set_value(stats.get("provider", "Ready"))
            model = stats.get("model", "Default")
            self.metric_model.set_value(model[:18] if model else "Standard")

            exec_s = stats.get("executive", {})
            self.metric_executions.set_value(str(exec_s.get("total_history", 0)))

            ref_s = stats.get("reflection", {})
            avg = ref_s.get("avg_quality", 0)
            if avg > 0:
                self.metric_quality.set_value(f"{avg:.2f}")
                self.metric_quality.set_value_color(colors.TEXT_SUCCESS if avg >= 0.8 else colors.TEXT_WARNING)
            else:
                self.metric_quality.set_value("N/A")
                self.metric_quality.set_value_color(colors.TEXT_MUTED)

            mem_s = stats.get("memory", {})
            total = mem_s.get("working_count", 0) + mem_s.get("persistent_count", 0)
            self.metric_memory.set_value(f"{total} items")

            agent_s = stats.get("agents", {})
            self.metric_agents.set_value(str(agent_s.get("agent_count", 0)))

            # Service health
            services = stats.get("services", [])
            svc_map = {s["name"]: s.get("health_ok", False) for s in services}
            for name, si in self.status_items.items():
                ok = svc_map.get(name, True)
                si.set_status("online" if ok else "offline")

            # Recent activity stream
            self._clear_activity()
            events = self.runtime.event_bus.get_history(limit=8)
            if not events:
                self._activity_container.addWidget(self._empty_activity)
            else:
                for event in reversed(events):
                    self._add_activity(event.event_type, event.source)

            # Update activity graph
            hist_count = exec_s.get("total_history", 0)
            self.exec_graph.set_data([
                ("Kernel", 25.0),
                ("Planner", 45.0),
                ("Exec", max(15.0, float(hist_count * 10))),
                ("Memory", float(total * 5)),
                ("Reflect", 60.0),
            ])

        except Exception:
            pass

    def _clear_activity(self) -> None:
        while self._activity_container.count():
            item = self._activity_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_activity(self, event_type: str, source: str) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)

        etype = QLabel(f" \u25B8  {event_type}")
        etype.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_SM}; font-weight: 500;")
        row.addWidget(etype)
        row.addStretch()

        src = QLabel(f"Source: {source}")
        src.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_XS};")
        row.addWidget(src)

        container = QWidget()
        container.setLayout(row)
        self._activity_container.addWidget(container)

