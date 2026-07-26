"""Dashboard workspace — system overview with metrics, health, and activity."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.status_indicator import StatusIndicator
from prototype.desktop.tokens import colors, typography


class DashboardView(BaseView):
    """System overview dashboard with real-time metrics."""

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
        header = self._make_header("Dashboard", "System Overview")
        layout.addWidget(header)

        # Metrics row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        self.metric_provider = MetricCard("Provider", "---")
        self.metric_model = MetricCard("Model", "---")
        self.metric_executions = MetricCard("Executions", "0")
        self.metric_quality = MetricCard("Quality", "---")
        self.metric_memory = MetricCard("Memory", "0")
        self.metric_agents = MetricCard("Agents", "0")
        for card in [self.metric_provider, self.metric_model, self.metric_executions,
                     self.metric_quality, self.metric_memory, self.metric_agents]:
            metrics_row.addWidget(card)
        layout.addLayout(metrics_row)

        # Two columns: Health + Activity
        columns = QHBoxLayout()
        columns.setSpacing(16)

        # Left: System Health
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 12, 16, 12)
        left_layout.setSpacing(8)

        left_title = QLabel("System Health")
        left_title.setObjectName("subheading")
        left_layout.addWidget(left_title)

        self.status_items = {}
        for name in ["kernel", "memory", "provider", "tools", "plugins", "workers", "agents"]:
            si = StatusIndicator(name.capitalize())
            left_layout.addWidget(si)
            self.status_items[name] = si

        left_layout.addStretch()
        columns.addWidget(left_card, 1)

        # Right: Recent Activity
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(8)

        right_title = QLabel("Recent Activity")
        right_title.setObjectName("subheading")
        right_layout.addWidget(right_title)

        self._activity_container = QVBoxLayout()
        self._activity_container.setSpacing(4)
        right_layout.addLayout(self._activity_container)

        self._no_activity = QLabel("No recent activity")
        self._no_activity.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        self._no_activity.setAlignment(Qt.AlignCenter)
        self._activity_container.addWidget(self._no_activity)

        right_layout.addStretch()
        columns.addWidget(right_card, 1)

        layout.addLayout(columns)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()

            # Metrics
            self.metric_provider.set_value(stats.get("provider", "---"))
            model = stats.get("model", "---")
            self.metric_model.set_value(model[:24] if model else "---")

            exec_s = stats.get("executive", {})
            self.metric_executions.set_value(str(exec_s.get("total_history", 0)))

            ref_s = stats.get("reflection", {})
            avg = ref_s.get("avg_quality", 0)
            self.metric_quality.set_value(f"{avg:.2f}")
            if avg >= 0.8:
                self.metric_quality.set_value_color(colors.TEXT_SUCCESS)
            elif avg >= 0.5:
                self.metric_quality.set_value_color(colors.TEXT_WARNING)
            else:
                self.metric_quality.set_value_color(colors.TEXT_DANGER)

            mem_s = stats.get("memory", {})
            total = mem_s.get("working_count", 0) + mem_s.get("persistent_count", 0)
            self.metric_memory.set_value(str(total))

            agent_s = stats.get("agents", {})
            self.metric_agents.set_value(str(agent_s.get("agent_count", 0)))

            # Service health — from services list
            services = stats.get("services", [])
            svc_map = {s["name"]: s.get("health_ok", False) for s in services}
            for name, si in self.status_items.items():
                ok = svc_map.get(name, False)
                si.set_status("online" if ok else "offline")

            # Recent activity
            self._clear_activity()
            events = self.runtime.event_bus.get_history(limit=10)
            for event in reversed(events):
                self._add_activity(event.event_type, event.source)

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

        etype = QLabel(event_type)
        etype.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_SM};")
        row.addWidget(etype)
        row.addStretch()

        src = QLabel(source)
        src.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_XS};")
        row.addWidget(src)

        container = QWidget()
        container.setLayout(row)
        self._activity_container.addWidget(container)
