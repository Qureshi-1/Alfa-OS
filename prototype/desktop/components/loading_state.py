"""Loading State — spinner animation for async operations."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Property

from prototype.desktop.tokens import colors, typography


class LoadingState(QWidget):
    """Animated loading indicator with optional message."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self._frame = 0
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self._spinner = QLabel(self.FRAMES[0])
        self._spinner.setAlignment(Qt.AlignCenter)
        self._spinner.setStyleSheet(f"font-size: 20px; color: {colors.ACCENT_SECONDARY}; font-family: monospace;")
        layout.addWidget(self._spinner)

        self._message = QLabel(message)
        self._message.setAlignment(Qt.AlignCenter)
        self._message.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
        layout.addWidget(self._message)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(80)

    def _advance(self) -> None:
        self._frame = (self._frame + 1) % len(self.FRAMES)
        self._spinner.setText(self.FRAMES[self._frame])

    def set_message(self, msg: str) -> None:
        self._message.setText(msg)

    def stop(self) -> None:
        self._timer.stop()

    def start(self) -> None:
        self._timer.start(80)
