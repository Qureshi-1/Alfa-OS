"""Plugins Workspace — extensions manager, enable/disable controls, and marketplace."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class PluginsView(BaseView):
    """Plugins workspace — installed extension modules manager."""

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
        header = self._make_header("Extensions & Plugin Architecture", "Manage loaded workspace extensions, custom tools, and ecosystem plugins")
        layout.addWidget(header)

        # Card
        card = QFrame()
        card.setObjectName("card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(10)

        c_header = QHBoxLayout()
        title = QLabel("Loaded Workspace Extensions")
        title.setObjectName("subheading")
        c_header.addWidget(title)
        c_header.addStretch()

        btn_ref = QPushButton("Scan Extensions")
        btn_ref.clicked.connect(self.refresh)
        c_header.addWidget(btn_ref)
        c_layout.addLayout(c_header)

        self.table = DataTable(headers=["Plugin ID", "Version", "Scope", "State", "Action"])
        c_layout.addWidget(self.table)

        self.empty = EmptyState("No plugin extensions loaded", "Plugins installed in prototype/plugins will appear here.")
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
            plugins = stats.get("plugins", [])

            if not plugins:
                self.table.hide()
                self.empty.show()
            else:
                self.empty.hide()
                self.table.show()
                rows = []
                for p in plugins:
                    p_name = p.get("name", "Plugin") if isinstance(p, dict) else str(p)
                    rows.append([p_name, "v1.0", "Workspace", "ACTIVE", "Configure"])
                self.table.populate(rows)
        except Exception:
            pass
