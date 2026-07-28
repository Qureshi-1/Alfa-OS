"""Chart Widget — lightweight native QPainter visual meters and mini charts."""

from typing import List, Optional, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

from prototype.desktop.tokens import colors, typography, radii, spacing


class MiniGaugeWidget(QWidget):
    """Horizontal metric meter gauge (e.g. CPU, RAM, GPU usage)."""

    def __init__(self, label: str = "Metric", value: float = 0.0,
                 unit: str = "%", accent_color: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.label = label
        self.value = max(0.0, min(100.0, value))
        self.unit = unit
        self.accent_color = accent_color or colors.ACCENT_CYAN

        self.setFixedHeight(38)

    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(100.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Background track
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(colors.BG_TERTIARY))
        painter.drawRoundedRect(0, h - 8, w, 6, 3, 3)

        # Fill bar width
        fill_w = max(4, int(w * (self.value / 100.0)))
        gradient = QLinearGradient(0, 0, fill_w, 0)
        c_start = QColor(self.accent_color)
        c_end = QColor(colors.ACCENT_SECONDARY)
        gradient.setColorAt(0, c_start)
        gradient.setColorAt(1, c_end)

        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(0, h - 8, fill_w, 6, 3, 3)

        # Label & text
        painter.setPen(QColor(colors.TEXT_MUTED))
        font = QFont("Inter", 9, QFont.Medium)
        painter.setFont(font)
        painter.drawText(0, h - 14, self.label)

        # Value text
        val_str = f"{self.value:.1f}{self.unit}"
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        font_bold = QFont("Inter", 9, QFont.Bold)
        painter.setFont(font_bold)
        painter.drawText(QRectF(0, h - 28, w, 14), Qt.AlignRight | Qt.AlignVCenter, val_str)

        painter.end()


class ExecutionGraphWidget(QWidget):
    """Mini bar chart visualizer for execution timeline or task distribution."""

    def __init__(self, data: Optional[List[Tuple[str, float]]] = None, parent=None):
        super().__init__(parent)
        self._data = data or [("Idle", 10), ("Plan", 35), ("Exec", 80), ("Mem", 45), ("Reflect", 65)]
        self.setFixedHeight(110)

    def set_data(self, data: List[Tuple[str, float]]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        chart_h = h - 22

        if not self._data:
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.setFont(QFont("Inter", 9))
            painter.drawText(rect, Qt.AlignCenter, "No execution metrics recorded")
            painter.end()
            return

        max_val = max(100.0, max(val for _, val in self._data))
        n = len(self._data)
        bar_gap = 8
        bar_w = max(12, int((w - (n + 1) * bar_gap) / n))

        for i, (label, val) in enumerate(self._data):
            x = bar_gap + i * (bar_w + bar_gap)
            bar_height = int((val / max_val) * (chart_h - 10))
            bar_y = chart_h - bar_height

            # Background column line
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(colors.BG_TERTIARY))
            painter.drawRoundedRect(x, 4, bar_w, chart_h - 4, 4, 4)

            # Active column bar gradient
            grad = QLinearGradient(x, bar_y, x, chart_h)
            grad.setColorAt(0, QColor(colors.ACCENT_CYAN))
            grad.setColorAt(1, QColor(colors.ACCENT_SECONDARY))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(x, bar_y, bar_w, bar_height, 4, 4)

            # Label below bar
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.setFont(QFont("Inter", 8))
            painter.drawText(QRectF(x - 4, chart_h + 2, bar_w + 8, 18), Qt.AlignCenter, label[:6])

        painter.end()
