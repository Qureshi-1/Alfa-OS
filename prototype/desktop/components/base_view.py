"""Base View — standard contract for all ALFA COS workspace views."""

import logging
from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography, spacing

logger = logging.getLogger("alfa.desktop.base_view")


class BaseView(QWidget):
    """Base class for all ALFA COS workspace views.

    Provides:
    - Runtime reference
    - Standard layout with header
    - refresh() protocol
    - Consistent styling
    """

    def __init__(self, runtime, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.runtime = runtime
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Override in subclasses to build the view."""
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

    def _make_header(self, title: str, subtitle: str = "") -> QWidget:
        """Create a standard section header with title and optional subtitle."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setObjectName("heading")
        layout.addWidget(title_label)

        if subtitle:
            layout.addSpacing(8)
            sub_label = QLabel(subtitle)
            sub_label.setObjectName("subheading")
            layout.addWidget(sub_label)

        layout.addStretch()
        return header

    def _make_panel_header(self, title: str, actions: Optional[QWidget] = None) -> QWidget:
        """Create a panel header with title and optional action buttons."""
        header = QWidget()
        header.setObjectName("panelHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setObjectName("subheading")
        layout.addWidget(label)
        layout.addStretch()

        if actions:
            layout.addWidget(actions)

        return header

    def refresh(self) -> None:
        """Refresh view data. Override in subclasses."""
        pass
