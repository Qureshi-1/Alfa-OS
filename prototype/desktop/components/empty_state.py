"""Empty State — placeholder when a view has no data."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography


class EmptyState(QWidget):
    """Centered empty state with icon, title, and description."""

    def __init__(self, icon: str = "", title: str = "No data",
                 description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        if icon:
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"font-size: 32px; color: {colors.TEXT_MUTED};")
            layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: {typography.SIZE_LG}; font-weight: 600;")
        layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: {typography.SIZE_SM};")
            layout.addWidget(desc_label)
