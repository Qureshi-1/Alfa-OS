"""Memory Workspace — short-term, long-term, graph, and vector memory."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QLineEdit, QComboBox, QSplitter,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class MemoryView(BaseView):
    """Memory workspace with search, CRUD, and statistics."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("panelHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Memory")
        title.setObjectName("heading")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search memories...")
        self._search.setFixedWidth(250)
        self._search.textChanged.connect(lambda: self.refresh())
        h_layout.addWidget(self._search)

        self._remember_input = QLineEdit()
        self._remember_input.setPlaceholderText("Remember something...")
        self._remember_input.setFixedWidth(250)
        h_layout.addWidget(self._remember_input)

        remember_btn = QPushButton("Remember")
        remember_btn.setObjectName("primary")
        remember_btn.clicked.connect(self._remember)
        h_layout.addWidget(remember_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear)
        h_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        # Metrics
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_working = MetricCard("Working", "0")
        self.metric_persistent = MetricCard("Persistent", "0")
        self.metric_total = MetricCard("Total", "0")
        for card in [self.metric_working, self.metric_persistent, self.metric_total]:
            metrics.addWidget(card)
        content_layout.addLayout(metrics)

        # Table
        self._table = DataTable(["ID", "Content", "Tags", "Importance", "Type"])
        self._table.set_column_width(0, 80)
        self._table.set_column_width(2, 120)
        self._table.set_column_width(3, 80)
        self._table.set_column_width(4, 80)
        content_layout.addWidget(self._table, 1)

        self._empty = EmptyState("\u2637", "No memories found", "Use 'Remember' to store information")
        content_layout.addWidget(self._empty)

        layout.addWidget(content, 1)

    def _remember(self) -> None:
        text = self._remember_input.text().strip()
        if not text or not self.runtime:
            return
        try:
            self.runtime.memory_manager.remember(text, persist=True)
            self._remember_input.clear()
            self.refresh()
        except Exception:
            pass

    def _clear(self) -> None:
        if not self.runtime:
            return
        try:
            self.runtime.memory_manager.clear(persistent=True)
            self.refresh()
        except Exception:
            pass

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            query = self._search.text().strip()
            results = self.runtime.memory_manager.recall(query, limit=100)

            stats = self.runtime.memory_manager.get_stats()
            working = stats.get("working_count", 0)
            persistent = stats.get("persistent_count", 0)
            self.metric_working.set_value(str(working))
            self.metric_persistent.set_value(str(persistent))
            self.metric_total.set_value(str(working + persistent))

            self._table.clear_data()
            if results:
                self._table.show()
                self._empty.hide()
                rows = []
                for ep in results:
                    rows.append([
                        ep.id[:8] if hasattr(ep, 'id') else "",
                        (ep.content[:60] + "...") if len(getattr(ep, 'content', '')) > 60 else getattr(ep, 'content', ''),
                        ", ".join(getattr(ep, 'tags', [])),
                        str(getattr(ep, 'importance', 0)),
                        "working",
                    ])
                self._table.populate(rows)
            else:
                self._table.hide()
                self._empty.show()
        except Exception:
            pass
