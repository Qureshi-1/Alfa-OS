"""Chat Workspace — streaming chat with tool calls, memory recall, and reasoning."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.tokens import colors, typography, spacing


class _ProcessWorker(QThread):
    """Background worker for LLM processing."""
    finished = Signal(object)

    def __init__(self, runtime, text):
        super().__init__()
        self._runtime = runtime
        self._text = text

    def run(self):
        result = self._runtime.process(self._text)
        self.finished.emit(result)


class ChatView(BaseView):
    """Chat workspace with message display, input, and status."""

    def _setup_ui(self) -> None:
        super()._setup_ui()
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("panelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        title = QLabel("Chat")
        title.setObjectName("heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("caption")
        header_layout.addWidget(self._status_label)

        layout.addWidget(header)

        # Messages area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._messages = QWidget()
        self._messages_layout = QVBoxLayout(self._messages)
        self._messages_layout.setContentsMargins(20, 16, 20, 16)
        self._messages_layout.setSpacing(12)
        self._messages_layout.addStretch()

        scroll.setWidget(self._messages)
        layout.addWidget(scroll, 1)

        # Input area
        input_bar = QWidget()
        input_bar.setStyleSheet(f"background-color: {colors.BG_SECONDARY}; border-top: 1px solid {colors.BORDER_SECONDARY};")
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(16, 10, 16, 10)
        input_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message...")
        self._input.setMinimumHeight(36)
        self._input.returnPressed.connect(self._send)
        input_layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("primary")
        self._send_btn.setFixedWidth(72)
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(input_bar)

    def _send(self) -> None:
        text = self._input.text().strip()
        if not text or self._worker:
            return

        self._add_message("user", text)
        self._input.clear()
        self._set_processing(True)

        self._worker = _ProcessWorker(self.runtime, text)
        self._worker.finished.connect(self._on_response)
        self._worker.start()

    @Slot(object)
    def _on_response(self, result) -> None:
        self._worker = None
        self._set_processing(False)

        if result.success:
            self._add_message("assistant", result.content)
        else:
            self._add_message("system", f"Error: {result.error}")

    def _add_message(self, role: str, content: str) -> None:
        msg_widget = QFrame()
        msg_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_SURFACE};
                border: 1px solid {colors.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(msg_widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Role label
        role_colors = {
            "user": colors.TEXT_ACCENT,
            "assistant": colors.ACCENT_SECONDARY,
            "system": colors.TEXT_WARNING,
        }
        role_label = QLabel(role.upper())
        role_label.setStyleSheet(f"color: {role_colors.get(role, colors.TEXT_MUTED)}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(role_label)

        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_BASE}; line-height: 1.5;")
        layout.addWidget(content_label)

        # Insert before the stretch
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, msg_widget)

        # Auto-scroll
        scroll_area = self._messages.parent().parent()
        if hasattr(scroll_area, "verticalScrollBar"):
            sb = scroll_area.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _set_processing(self, processing: bool) -> None:
        self._input.setEnabled(not processing)
        self._send_btn.setEnabled(not processing)
        if processing:
            self._status_label.setText("Processing...")
            self._status_label.setStyleSheet(f"color: {colors.TEXT_WARNING};")
        else:
            self._status_label.setText("Ready")
            self._status_label.setStyleSheet(f"color: {colors.TEXT_MUTED};")

    def refresh(self) -> None:
        pass
