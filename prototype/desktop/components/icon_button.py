"""Icon Button — compact button with icon character and optional tooltip."""

from typing import Optional

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors


class IconButton(QPushButton):
    """Compact icon button using Unicode symbols."""

    def __init__(self, icon: str, tooltip: str = "", parent=None):
        super().__init__(icon, parent)
        self.setToolTip(tooltip)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {colors.TEXT_SECONDARY};
                font-size: 14px;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {colors.BG_ACTIVE};
            }}
        """)
