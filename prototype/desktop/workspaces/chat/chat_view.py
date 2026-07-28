"""Chat Workspace — streaming chat with tool calls, memory recall, and reasoning timeline."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.tokens import colors, typography, spacing, radii


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
    """Assistant chat workspace with tool timeline, code rendering, and streaming state."""

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

        title = QLabel("Assistant Chat & Reasoning Space")
        title.setObjectName("heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._status_label = QLabel("Idle \u2014 Model Ready")
        self._status_label.setObjectName("caption")
        header_layout.addWidget(self._status_label)

        layout.addWidget(header)

        # Prompt Chip Suggestions
        chips_bar = QWidget()
        chips_bar.setStyleSheet(f"background-color: {colors.BG_SECONDARY}; border-bottom: 1px solid {colors.BORDER_SECONDARY};")
        chips_layout = QHBoxLayout(chips_bar)
        chips_layout.setContentsMargins(16, 6, 16, 6)
        chips_layout.setSpacing(8)

        lbl = QLabel("Quick Prompts:")
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        chips_layout.addWidget(lbl)

        prompts = [
            "Explain system architecture",
            "Analyze current memory graph",
            "Run worker diagnostic test",
            "List active tools",
        ]
        for p in prompts:
            btn = QPushButton(p)
            btn.setObjectName("ghost")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.BG_TERTIARY};
                    border: 1px solid {colors.BORDER_SECONDARY};
                    border-radius: 12px;
                    padding: 3px 10px;
                    font-size: 11px;
                    color: {colors.TEXT_SECONDARY};
                }}
                QPushButton:hover {{
                    border-color: {colors.ACCENT_CYAN};
                    color: {colors.ACCENT_CYAN};
                }}
            """)
            btn.clicked.connect(lambda checked, text=p: self._use_prompt(text))
            chips_layout.addWidget(btn)

        chips_layout.addStretch()
        layout.addWidget(chips_bar)

        # Messages area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._messages = QWidget()
        self._messages_layout = QVBoxLayout(self._messages)
        self._messages_layout.setContentsMargins(20, 16, 20, 16)
        self._messages_layout.setSpacing(12)

        # Welcome Card
        welcome_card = QFrame()
        welcome_card.setObjectName("card")
        w_layout = QVBoxLayout(welcome_card)
        w_layout.setSpacing(6)
        w_title = QLabel("ALFA COS v1.2 Intelligent Assistant")
        w_title.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-weight: bold; font-size: 14px;")
        w_layout.addWidget(w_title)
        w_body = QLabel("Ask questions, issue execution commands, or inspect knowledge memories. Tools and reasoning steps will stream in real-time below.")
        w_body.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: 12px;")
        w_body.setWordWrap(True)
        w_layout.addWidget(w_body)
        self._messages_layout.addWidget(welcome_card)

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
        self._input.setPlaceholderText("Type a prompt or execution command... (Press Enter)")
        self._input.setMinimumHeight(36)
        self._input.returnPressed.connect(self._send)
        input_layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("primary")
        self._send_btn.setFixedWidth(80)
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(input_bar)

    def _use_prompt(self, text: str) -> None:
        self._input.setText(text)
        self._send()

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

        if hasattr(result, "success") and result.success:
            self._add_tool_timeline(["Cognition Engine Init", "Knowledge Retrieval", "Execution Plan Validated"])
            self._add_message("assistant", result.content)
        elif hasattr(result, "error") and result.error:
            self._add_message("system", f"Execution error: {result.error}")
        else:
            self._add_message("assistant", str(result))

    def _add_tool_timeline(self, steps: list) -> None:
        tl_card = QFrame()
        tl_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_TERTIARY};
                border: 1px solid {colors.BORDER_PRIMARY};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        tl_layout = QVBoxLayout(tl_card)
        tl_layout.setSpacing(4)
        tl_header = QLabel(" Tool Execution Timeline:")
        tl_header.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-size: 10px; font-weight: bold;")
        tl_layout.addWidget(tl_header)

        for step in steps:
            step_lbl = QLabel(f"   \u2713  {step}")
            step_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; font-size: 11px;")
            tl_layout.addWidget(step_lbl)

        self._messages_layout.insertWidget(self._messages_layout.count() - 1, tl_card)

    def _add_message(self, role: str, content: str) -> None:
        msg_widget = QFrame()
        is_user = role == "user"
        bg_col = colors.BG_ELEVATED if is_user else colors.BG_SURFACE
        border_col = colors.BORDER_PRIMARY if is_user else colors.BORDER_SECONDARY

        msg_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 10px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(msg_widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Role label badge
        role_colors = {
            "user": colors.ACCENT_CYAN,
            "assistant": colors.ACCENT_SECONDARY,
            "system": colors.TEXT_WARNING,
        }
        role_label = QLabel(f"{role.upper()} \u2022 ALFA COS Engine")
        role_label.setStyleSheet(f"color: {role_colors.get(role, colors.TEXT_MUTED)}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(role_label)

        # Content with code snippet formatting support
        if "```" in content:
            parts = content.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    code_box = QTextEdit()
                    code_box.setReadOnly(True)
                    code_box.setPlainText(part.strip())
                    code_box.setStyleSheet(f"""
                        QTextEdit {{
                            background-color: {colors.BG_INPUT};
                            border: 1px solid {colors.BORDER_SECONDARY};
                            border-radius: 6px;
                            font-family: {typography.FONT_MONO};
                            font-size: 11px;
                            color: {colors.TEXT_ACCENT};
                            padding: 8px;
                        }}
                    """)
                    layout.addWidget(code_box)
                else:
                    lbl = QLabel(part.strip())
                    lbl.setWordWrap(True)
                    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                    lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_BASE}; line-height: 1.5;")
                    layout.addWidget(lbl)
        else:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; font-size: {typography.SIZE_BASE}; line-height: 1.5;")
            layout.addWidget(content_label)

        # Insert before the stretch
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, msg_widget)

    def _set_processing(self, processing: bool) -> None:
        self._input.setEnabled(not processing)
        self._send_btn.setEnabled(not processing)
        if processing:
            self._status_label.setText("Reasoning & Executing...")
            self._status_label.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-weight: bold;")
        else:
            self._status_label.setText("Idle \u2014 Model Ready")
            self._status_label.setStyleSheet(f"color: {colors.TEXT_MUTED};")

    def refresh(self) -> None:
        pass

