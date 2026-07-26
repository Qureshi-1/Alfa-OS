"""Notifications workspace — system alerts, events, and logs."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QComboBox, QTextEdit,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.tokens import colors, typography


class NotificationsView(BaseView):
    """Notifications workspace showing system events and alerts."""

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

        title = QLabel("Notifications")
        title.setObjectName("heading")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self._filter = QComboBox()
        self._filter.addItems(["All Events", "Runtime", "Workers", "Plugins", "Memory"])
        self._filter.currentTextChanged.connect(lambda: self.refresh())
        h_layout.addWidget(self._filter)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ghost")
        clear_btn.clicked.connect(self._clear)
        h_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Events table
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)

        self._table = DataTable(["Time", "Event", "Source", "Details"])
        self._table.set_column_width(0, 100)
        self._table.set_column_width(1, 180)
        self._table.set_column_width(2, 120)
        content_layout.addWidget(self._table, 1)

        layout.addWidget(content, 1)

    def _clear(self) -> None:
        if self.runtime:
            self.runtime.event_bus.clear_history()
        self._table.clear_data()

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            filter_text = self._filter.currentText().lower()
            events = self.runtime.event_bus.get_history(limit=100)

            self._table.clear_data()
            rows = []
            for event in reversed(events):
                if filter_text != "all events" and filter_text not in event.source.lower():
                    continue
                ts = event.timestamp.strftime("%H:%M:%S") if hasattr(event.timestamp, 'strftime') else str(event.timestamp)[:8]
                rows.append([
                    ts,
                    event.event_type,
                    event.source,
                    str(event.payload)[:80] if event.payload else "",
                ])
            self._table.populate(rows)

        except Exception:
            pass
