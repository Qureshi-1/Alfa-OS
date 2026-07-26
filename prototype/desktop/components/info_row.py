"""Info Row — label: value pair for sidebar/panel display."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from prototype.desktop.tokens import colors, typography


class InfoRow(QWidget):
    """Horizontal row displaying label and value."""

    def __init__(self, label: str = "", value: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        layout.addWidget(self._label)

        layout.addStretch()

        self._value = QLabel(value)
        self._value.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_SM}; font-weight: 500;")
        layout.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)

    def set_value_color(self, color: str) -> None:
        self._value.setStyleSheet(f"color: {color}; font-size: {typography.SIZE_SM}; font-weight: 500;")

    def set_label(self, text: str) -> None:
        self._label.setText(text)
