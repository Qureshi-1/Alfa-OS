"""Metric Card — displays a single metric with label and value."""

from typing import Optional

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography, spacing, radii


class MetricCard(QFrame):
    """Card displaying a metric label, value, and optional subtitle."""

    def __init__(self, label: str = "", value: str = "0",
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setMinimumWidth(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        layout.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setObjectName("value")
        layout.addWidget(self._value)

        if subtitle:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_XS};")
            layout.addWidget(self._subtitle)
        else:
            self._subtitle = None

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_label(self, text: str) -> None:
        self._label.setText(text)

    def set_subtitle(self, text: str) -> None:
        if self._subtitle:
            self._subtitle.setText(text)

    def set_value_color(self, color: str) -> None:
        self._value.setStyleSheet(f"color: {color}; font-size: {typography.SIZE_2XL}; font-weight: bold;")
