"""Sidebar — left navigation rail for workspace switching."""

from typing import Dict, Optional, Tuple, List

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame
from PySide6.QtCore import Signal, Qt

from prototype.desktop.tokens import colors, sizes, typography, spacing


class Sidebar(QWidget):
    """Left navigation rail supporting all 13 AI OS workspace views and dynamic plugins."""

    workspace_changed = Signal(str)

    DEFAULT_NAV_ITEMS: List[Tuple[str, str, str]] = [
        ("dashboard", "\u25A6", "Dashboard"),
        ("chat", "\u2709", "Assistant"),
        ("memory", "\u25C8", "Memory"),
        ("planner", "\u25B3", "Planner"),
        ("tasks", "\u2630", "Tasks"),
        ("knowledge", "\u25A4", "Knowledge"),
        ("runtime", "\u26A1", "Runtime"),
        ("model_hub", "\u25C7", "Models"),
        ("agents", "\u2606", "Agents"),
        ("tools", "\u2692", "Tools"),
        ("files", "\U0001F4C1", "Files"),
        ("plugins", "\U0001F9E9", "Plugins"),
        ("settings", "\u2699", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(160)
        self._buttons: Dict[str, QPushButton] = {}
        self._active: Optional[str] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 12, 6, 12)
        main_layout.setSpacing(4)

        # Scroll area for navigation items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        nav_container = QWidget()
        self._nav_layout = QVBoxLayout(nav_container)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setSpacing(3)

        for workspace_id, icon, label in self.DEFAULT_NAV_ITEMS:
            self._add_button(workspace_id, icon, label)

        self._nav_layout.addStretch()

        scroll.setWidget(nav_container)
        main_layout.addWidget(scroll)

        # Bottom notifications shortcut
        notif_btn = QPushButton(" \U0001F514 Notifications")
        notif_btn.setObjectName("sidebarBtn")
        notif_btn.setToolTip("Notifications & Activity")
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_btn.clicked.connect(lambda: self._on_click("notifications"))
        main_layout.addWidget(notif_btn)
        self._buttons["notifications"] = notif_btn

    def _add_button(self, workspace_id: str, icon: str, label: str) -> None:
        btn = QPushButton(f" {icon}  {label}")
        btn.setObjectName("sidebarBtn")
        btn.setToolTip(label)
        btn.setCheckable(False)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked, wid=workspace_id: self._on_click(wid))
        self._nav_layout.addWidget(btn)
        self._buttons[workspace_id] = btn

    def add_nav_item(self, workspace_id: str, icon: str, label: str) -> None:
        """Allow plugins to dynamically add navigation items."""
        if workspace_id not in self._buttons:
            self._add_button(workspace_id, icon, label)

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

