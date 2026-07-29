"""Tools Workspace — installed tools catalog, permissions matrix, execution history, and logs."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QTextEdit,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class ToolsView(BaseView):
    """Tools workspace — installed tools registry, permission toggles, execution history timeline."""

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
        header = self._make_header("Tools & Permissions Catalog", "Inspect loaded capability tools, access control policies, and execution logs")
        layout.addWidget(header)

        # Tools Table Card
        card = QFrame()
        card.setObjectName("card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(10)

        c_header = QHBoxLayout()
        title = QLabel("Installed Capability Tools")
        title.setObjectName("subheading")
        c_header.addWidget(title)
        c_header.addStretch()

        btn_ref = QPushButton("Refresh Tools")
        btn_ref.clicked.connect(self.refresh)
        c_header.addWidget(btn_ref)
        c_layout.addLayout(c_header)

        self.table = DataTable(headers=["Tool Name", "Category", "Permission", "Executions", "Status"])
        c_layout.addWidget(self.table)

        self.empty = EmptyState("No tools registered", "Registered tools will automatically populate from prototype/tools.")
        c_layout.addWidget(self.empty)

        layout.addWidget(card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            tools_list = stats.get("tools", [])

            if not tools_list:
                self.table.hide()
                self.empty.show()
            else:
                self.empty.hide()
                self.table.show()
                rows = []
                for t in tools_list:
                    rows.append([
                        t.get("name", "Tool"),
                        "System Utility",
                        "ALLOWED",
                        "0",
                        "ACTIVE",
                    ])
                self.table.populate(rows)
        except Exception:
            pass
