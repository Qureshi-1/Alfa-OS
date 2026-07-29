"""Data Table — styled QTableWidget with helper methods."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography


class DataTable(QTableWidget):
    """Pre-styled table with helper methods for data population."""

    def __init__(self, headers: List[str], parent=None):
        super().__init__(parent)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(36)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def populate(self, rows: List[List[str]], data: Optional[List[Dict[str, Any]]] = None) -> None:
        """Fill the table with row data.

        Args:
            rows: List of cell values per row.
            data: Optional metadata per row (stored in userData).
        """
        self.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                item = QTableWidgetItem(str(cell))
                item.setForeground(self._default_fg())
                if data and i < len(data):
                    item.setData(Qt.UserRole, data[i])
                self.setItem(i, j, item)

    set_data = populate

    def add_row(self, row: List[str], data: Optional[Dict[str, Any]] = None) -> None:
        """Append a single row to the table."""
        r = self.rowCount()
        self.insertRow(r)
        for j, cell in enumerate(row):
            item = QTableWidgetItem(str(cell))
            item.setForeground(self._default_fg())
            if data:
                item.setData(Qt.UserRole, data)
            self.setItem(r, j, item)

    def clear_data(self) -> None:
        self.setRowCount(0)

    def selected_row_data(self) -> Optional[Dict[str, Any]]:
        """Return the UserRole data of the selected row."""
        row = self.currentRow()
        if row < 0:
            return None
        item = self.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _default_fg(self):
        from PySide6.QtGui import QColor
        return QColor(colors.TEXT_PRIMARY)

    def set_column_width(self, col: int, width: int) -> None:
        self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
        self.setColumnWidth(col, width)
