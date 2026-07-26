"""Badge — small labeled indicator."""

from PySide6.QtWidgets import QLabel

from prototype.desktop.tokens import colors


class Badge(QLabel):
    """Colored badge label for status/category display."""

    STYLES = {
        "default": ("badge", f"background-color: {colors.ACCENT_SUBTLE}; color: {colors.ACCENT_SECONDARY};"),
        "danger": ("badgeDanger", f"background-color: {colors.DANGER_BG}; color: {colors.DANGER};"),
        "success": ("badgeSuccess", f"background-color: {colors.SUCCESS_BG}; color: {colors.SUCCESS};"),
        "warning": ("badgeWarning", f"background-color: {colors.WARNING_BG}; color: {colors.WARNING};"),
    }

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        super().__init__(text, parent)
        name, style = self.STYLES.get(variant, self.STYLES["default"])
        self.setObjectName(name)
        self.setStyleSheet(style)

    def set_variant(self, variant: str) -> None:
        name, style = self.STYLES.get(variant, self.STYLES["default"])
        self.setObjectName(name)
        self.setStyleSheet(style)

    def set_text(self, text: str) -> None:
        self.setText(text)
