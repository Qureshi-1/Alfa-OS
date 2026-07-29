"""Empty State — placeholder when a view has no data."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography


class EmptyState(QWidget):
    """Centered empty state with icon, title, and description."""

    def __init__(self, arg1: str = "", arg2: str = "", arg3: str = "", parent=None):
        super().__init__(parent)

        # Smart positional argument resolution
        icon, title, description = "", "No data", ""
        if arg3:
            icon, title, description = arg1, arg2, arg3
        elif arg2:
            if len(arg1) <= 3:
                icon, title = arg1, arg2
            else:
                title, description = arg1, arg2
        elif arg1:
            if len(arg1) <= 3:
                icon = arg1
            else:
                title = arg1

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)

        if icon:
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"font-size: 28px; color: {colors.TEXT_MUTED};")
            layout.addWidget(icon_label)

        if title:
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
