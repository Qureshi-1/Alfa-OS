"""Status Bars — top and bottom bars for system information."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QFrame
from PySide6.QtCore import Qt

from prototype.desktop.tokens import colors, typography, spacing, radii


class TopBar(QWidget):
    """Top status bar — branding, global command palette trigger, provider & status."""

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(42)
        self._runtime = runtime

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        # Left: logo badge
        self._brand = QLabel(" ALFA COS ")
        self._brand.setObjectName("badge")
        self._brand.setStyleSheet(f"""
            background-color: {colors.ACCENT_SUBTLE};
            color: {colors.ACCENT_CYAN};
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 1.5px;
            border-radius: 6px;
            padding: 3px 8px;
        """)
        layout.addWidget(self._brand)

        ver = QLabel("v1.2")
        ver.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 10px; font-weight: 600;")
        layout.addWidget(ver)

        layout.addSpacing(12)

        # Quick Command / Search field
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(" Search workspace, commands & memory... (Ctrl+K)")
        self._search_input.setFixedWidth(280)
        self._search_input.setFixedHeight(28)
        self._search_input.setStyleSheet(f"""
            background-color: {colors.BG_TERTIARY};
            border: 1px solid {colors.BORDER_SECONDARY};
            border-radius: 6px;
            color: {colors.TEXT_PRIMARY};
            font-size: 11px;
            padding-left: 8px;
        """)
        layout.addWidget(self._search_input)

        layout.addStretch()

        # Provider & Model indicators
        self._provider = QLabel("Provider: Ready")
        self._provider.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._provider)

        sep = QFrame()
        sep.setObjectName("separatorV")
        sep.setFixedHeight(14)
        layout.addWidget(sep)

        self._model = QLabel("Model: Standard")
        self._model.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._model)

        layout.addSpacing(8)

        # Status dot
        self._status = QLabel("\u25CF Online")
        self._status.setStyleSheet(f"color: {colors.SUCCESS}; font-size: 11px; font-weight: 500;")
        layout.addWidget(self._status)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            settings = self._runtime._settings
            provider = settings.get_provider() if hasattr(settings, "get_provider") else "Default"
            model = settings.get_model() if hasattr(settings, "get_model") else "Standard"
            self._provider.setText(f"Provider: {provider}")
            self._model.setText(f"Model: {model[:20]}")
        except Exception:
            pass


class BottomBar(QWidget):
    """Bottom status bar — connection, provider, execution status, background tasks, version."""

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.setObjectName("bottomBar")
        self.setFixedHeight(28)
        self._runtime = runtime

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(14)

        # Connection status
        self._conn_label = QLabel("\u25CF Connected")
        self._conn_label.setStyleSheet(f"color: {colors.SUCCESS}; font-size: 11px; font-weight: 500;")
        layout.addWidget(self._conn_label)

        # Provider badge
        self._provider_badge = QLabel("Provider: Gemini 3.6 Flash")
        self._provider_badge.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._provider_badge)

        # Execution Status
        self._exec_status = QLabel("Engine: Idle")
        self._exec_status.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._exec_status)

        layout.addStretch()

        # Background Tasks
        self._tasks_label = QLabel("Background Tasks: 0")
        self._tasks_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._tasks_label)

        # Version tag
        self._ver_label = QLabel("ALFA COS v1.2-dev")
        self._ver_label.setStyleSheet(f"color: {colors.TEXT_ACCENT}; font-size: 10px; font-weight: 600;")
        layout.addWidget(self._ver_label)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            stats = self._runtime.get_stats()
            provider = stats.get("provider", "Ready")
            workers = stats.get("workers", {})
            exec_stats = stats.get("executive", {})

            self._provider_badge.setText(f"Provider: {provider}")
            running_tasks = workers.get("running", 0)
            self._tasks_label.setText(f"Background Tasks: {running_tasks}")

            is_running = exec_stats.get("is_running", False)
            if is_running:
                self._exec_status.setText("Engine: Executing")
                self._exec_status.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-size: 11px; font-weight: 600;")
            else:
                self._exec_status.setText("Engine: Ready")
                self._exec_status.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        except Exception:
            pass

