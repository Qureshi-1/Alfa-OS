"""Section Header — title with optional action buttons."""

from typing import Optional

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography, spacing


class SectionHeader(QWidget):
    """Header bar for a section with title and optional right-side actions."""

    def __init__(self, title: str, subtitle: str = "",
                 actions: Optional[QWidget] = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(8)

        self._title = QLabel(title)
        self._title.setObjectName("heading")
        layout.addWidget(self._title)

        if subtitle:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setObjectName("subheading")
            layout.addWidget(self._subtitle)
        else:
            self._subtitle = None

        layout.addStretch()

        if actions:
            layout.addWidget(actions)

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    def set_subtitle(self, text: str) -> None:
        if self._subtitle:
            self._subtitle.setText(text)
