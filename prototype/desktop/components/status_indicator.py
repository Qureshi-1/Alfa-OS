"""Status Indicator — dot + label for system health display."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors


class StatusDot(QLabel):
    """8px colored dot indicating status."""

    def __init__(self, status: str = "online", parent=None):
        super().__init__(parent)
        self.setObjectName("statusDot")
        self._set_status(status)
        self.setFixedSize(8, 8)

    def _set_status(self, status: str) -> None:
        if status == "online":
            self.setObjectName("statusDot")
            self.setStyleSheet(f"background-color: {colors.SUCCESS}; border-radius: 4px;")
        elif status == "offline":
            self.setStyleSheet(f"background-color: {colors.DANGER}; border-radius: 4px;")
        elif status == "warning":
            self.setStyleSheet(f"background-color: {colors.WARNING}; border-radius: 4px;")
        else:
            self.setStyleSheet(f"background-color: {colors.TEXT_MUTED}; border-radius: 4px;")

    def set_status(self, status: str) -> None:
        self._set_status(status)


class StatusIndicator(QWidget):
    """Dot + text label for status display."""

    def __init__(self, label: str = "", status: str = "online", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.dot = StatusDot(status)
        layout.addWidget(self.dot)

        self.label = QLabel(label)
        self.label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.label)

        layout.addStretch()

    def set_status(self, status: str, text: str = "") -> None:
        self.dot.set_status(status)
        if text:
            self.label.setText(text)

    def set_text(self, text: str) -> None:
        self.label.setText(text)
