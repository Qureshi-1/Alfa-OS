"""Workers workspace — worker registry, queue, execution, and lifecycle."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors


class WorkersView(BaseView):
    """Workers workspace with registry, scheduling, and lifecycle monitoring."""

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
        title = QLabel("Workers")
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
        self.metric_total = MetricCard("Workers", "0")
        self.metric_running = MetricCard("Running", "0")
        self.metric_completed = MetricCard("Completed", "0")
        self.metric_failed = MetricCard("Failed", "0")
        self.metric_scheduled = MetricCard("Scheduled", "0")
        for card in [self.metric_total, self.metric_running, self.metric_completed,
                     self.metric_failed, self.metric_scheduled]:
            metrics.addWidget(card)
        layout.addLayout(metrics)

        # Worker table
        self._table = DataTable(["Worker", "Status", "Task ID", "Execution Time"])
        self._table.set_column_width(0, 150)
        self._table.set_column_width(1, 100)
        self._table.set_column_width(2, 120)
        layout.addWidget(self._table, 1)

        self._empty = EmptyState("\u2630", "No workers registered", "Workers appear here when registered")
        layout.addWidget(self._empty)

        # Schedules table
        sched_title = QLabel("Scheduled Tasks")
        sched_title.setObjectName("subheading")
        layout.addWidget(sched_title)

        self._sched_table = DataTable(["Schedule ID", "Worker", "Interval", "Enabled", "Run Count"])
        self._sched_table.set_column_width(0, 160)
        self._sched_table.set_column_width(1, 120)
        self._sched_table.set_column_width(2, 80)
        self._sched_table.set_column_width(3, 70)
        layout.addWidget(self._sched_table)

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            workers = stats.get("workers", {})

            self.metric_total.set_value(str(workers.get("worker_count", 0)))
            self.metric_running.set_value(str(workers.get("running", 0)))
            self.metric_completed.set_value(str(workers.get("completed", 0)))
            self.metric_failed.set_value(str(workers.get("failed", 0)))
            self.metric_scheduled.set_value(str(workers.get("schedules", 0)))

            # Worker list
            registered = workers.get("registered_workers", [])
            self._table.clear_data()
            if registered:
                self._table.show()
                self._empty.hide()
                rows = [[w, "Registered", "---", "---"] for w in registered]
                self._table.populate(rows)
            else:
                self._table.hide()
                self._empty.show()

            # Schedules
            self._sched_table.clear_data()

        except Exception:
            pass
