"""Agent Workspace — agent registry, execution, planning, and reflection."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QLineEdit, QGridLayout,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.status_indicator import StatusIndicator
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class AgentWorkspaceView(BaseView):
    """Agent workspace with registry, execution, and monitoring."""

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
        header_row = QHBoxLayout()
        title = QLabel("Agents")
        title.setObjectName("heading")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("\u21bb Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        # Metrics
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_registered = MetricCard("Registered", "0")
        self.metric_enabled = MetricCard("Enabled", "0")
        self.metric_score = MetricCard("Avg Score", "---")
        self.metric_reflections = MetricCard("Reflections", "0")
        for card in [self.metric_registered, self.metric_enabled, self.metric_score, self.metric_reflections]:
            metrics.addWidget(card)
        layout.addLayout(metrics)

        # Agent list
        self._table = DataTable(["ID", "Name", "Role", "Capabilities", "Status"])
        self._table.set_column_width(0, 120)
        self._table.set_column_width(1, 150)
        self._table.set_column_width(2, 100)
        self._table.set_column_width(3, 200)
        layout.addWidget(self._table, 1)

        self._empty = EmptyState("\u2606", "No agents registered", "Agents will appear here when registered")
        layout.addWidget(self._empty)

        # Reflection history
        ref_title = QLabel("Recent Reflections")
        ref_title.setObjectName("subheading")
        layout.addWidget(ref_title)

        self._reflection_table = DataTable(["Agent", "Score", "Issues", "Recommendations"])
        self._reflection_table.set_column_width(0, 120)
        self._reflection_table.set_column_width(1, 80)
        self._reflection_table.set_column_width(2, 200)
        layout.addWidget(self._reflection_table)

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            agent_stats = stats.get("agents", {})
            agents = agent_stats.get("agents", [])

            self.metric_registered.set_value(str(len(agents)))

            enabled = sum(1 for a in agents if a.get("healthy", True))
            self.metric_enabled.set_value(str(enabled))

            ref_stats = agent_stats.get("reflection", {})
            avg = ref_stats.get("average_score", 0)
            self.metric_score.set_value(f"{avg:.2f}")
            self.metric_reflections.set_value(str(ref_stats.get("total_reflections", 0)))

            self._table.clear_data()
            if agents:
                self._table.show()
                self._empty.hide()
                rows = []
                for a in agents:
                    rows.append([
                        a.get("agent_id", "")[:12],
                        a.get("name", ""),
                        a.get("role", ""),
                        ", ".join(a.get("capabilities", [])),
                        "Healthy" if a.get("healthy", True) else "Unhealthy",
                    ])
                self._table.populate(rows)
            else:
                self._table.hide()
                self._empty.show()

        except Exception:
            pass
