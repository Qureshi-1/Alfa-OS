"""Sidebar — left navigation rail for workspace switching."""

from typing import Dict, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt

from prototype.desktop.tokens import colors, sizes


class Sidebar(QWidget):
    """Left navigation rail with icon buttons for workspace switching."""

    workspace_changed = Signal(str)

    NAV_ITEMS = [
        ("dashboard", "\u2302", "Dashboard"),
        ("chat", "\u2709", "Chat"),
        ("model_hub", "\u2699", "Models"),
        ("memory", "\u2637", "Memory"),
        ("agents", "\u2606", "Agents"),
        ("workers", "\u2630", "Workers"),
        ("settings", "\u2692", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(52)
        self._buttons: Dict[str, QPushButton] = {}
        self._active: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)

        for workspace_id, icon, tooltip in self.NAV_ITEMS:
            btn = QPushButton(icon)
            btn.setObjectName("sidebarBtn")
            btn.setToolTip(tooltip)
            btn.setCheckable(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, wid=workspace_id: self._on_click(wid))
            layout.addWidget(btn)
            self._buttons[workspace_id] = btn

        layout.addStretch()

        # Bottom: notifications + settings quick access
        notif_btn = QPushButton("\U0001F514")
        notif_btn.setToolTip("Notifications")
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_btn.clicked.connect(lambda: self._on_click("notifications"))
        layout.addWidget(notif_btn)
        self._buttons["notifications"] = notif_btn

    def _on_click(self, workspace_id: str) -> None:
        self.set_active(workspace_id)
        self.workspace_changed.emit(workspace_id)

    def set_active(self, workspace_id: str) -> None:
        for wid, btn in self._buttons.items():
            btn.setProperty("active", wid == workspace_id)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._active = workspace_id

    def get_active(self) -> Optional[str]:
        return self._active
