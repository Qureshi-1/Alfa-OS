"""Tasks Workspace — background worker tasks, queue, and priority monitor."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class TasksView(BaseView):
    """Tasks workspace — displays background worker task queue and active workers."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header = self._make_header("Task Queue & Worker Swarm", "Manage active background tasks, worker threads, and queue priority")
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        c_header = QHBoxLayout()
        title = QLabel("Active Worker Tasks")
        title.setObjectName("subheading")
        c_header.addWidget(title)
        c_header.addStretch()

        btn_refresh = QPushButton("Refresh Queue")
        btn_refresh.clicked.connect(self.refresh)
        c_header.addWidget(btn_refresh)
        card_layout.addLayout(c_header)

        self.table = DataTable(headers=["Task ID", "Worker", "Priority", "Status", "Payload / State"])
        card_layout.addWidget(self.table)

        self.empty = EmptyState("No background tasks running", "Background tasks automatically queue when heavy work is initiated.")
        card_layout.addWidget(self.empty)

        layout.addWidget(card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            workers_info = stats.get("workers", {})
            worker_list = workers_info.get("active", [])

            if not worker_list:
                self.table.hide()
                self.empty.show()
            else:
                self.empty.hide()
                self.table.show()
                rows = []
                for w in worker_list:
                    rows.append([
                        w.get("task_id", "t-0"),
                        w.get("worker_id", "w-0"),
                        "NORMAL",
                        w.get("status", "RUNNING"),
                        w.get("name", "Execution Worker"),
                    ])
                self.table.populate(rows)
        except Exception:
            pass
