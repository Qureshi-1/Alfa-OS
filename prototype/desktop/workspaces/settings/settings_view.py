"""Settings workspace — provider, model, and system configuration."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QFormLayout, QMessageBox, QGroupBox, QTextEdit,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.tokens import colors


class SettingsView(BaseView):
    """Settings workspace with provider, model, and system configuration."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("heading")
        layout.addWidget(title)

        # ── Provider Settings ───────────────────────────────────────────
        provider_group = QGroupBox("Provider")
        provider_group.setStyleSheet(f"""
            QGroupBox {{
                color: {colors.TEXT_SECONDARY};
                font-weight: 600;
                border: 1px solid {colors.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)
        pf = QFormLayout(provider_group)
        pf.setSpacing(10)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["mock", "nvidia", "openrouter", "ollama"])
        pf.addRow("Provider:", self._provider_combo)

        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("Model name")
        pf.addRow("Model:", self._model_input)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("API key (leave blank to keep current)")
        pf.addRow("API Key:", self._api_key_input)

        layout.addWidget(provider_group)

        # ── Generation Settings ─────────────────────────────────────────
        gen_group = QGroupBox("Generation")
        gen_group.setStyleSheet(provider_group.styleSheet())
        gf = QFormLayout(gen_group)
        gf.setSpacing(10)

        self._temp_spin = QDoubleSpinBox()
        self._temp_spin.setRange(0.0, 2.0)
        self._temp_spin.setSingleStep(0.1)
        self._temp_spin.setValue(0.7)
        gf.addRow("Temperature:", self._temp_spin)

        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(256, 32768)
        self._max_tokens_spin.setSingleStep(256)
        self._max_tokens_spin.setValue(4096)
        gf.addRow("Max Tokens:", self._max_tokens_spin)

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(1, 300)
        self._timeout_spin.setValue(30)
        self._timeout_spin.setSuffix("s")
        gf.addRow("Timeout:", self._timeout_spin)

        layout.addWidget(gen_group)

        # ── Actions ─────────────────────────────────────────────────────
        actions = QHBoxLayout()
        actions.setSpacing(8)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primary")
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self._save)
        actions.addWidget(save_btn)

        test_btn = QPushButton("Test Connection")
        test_btn.setFixedWidth(140)
        test_btn.clicked.connect(self._test_connection)
        actions.addWidget(test_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # ── Status ──────────────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def _save(self) -> None:
        if not self.runtime:
            return
        try:
            s = self.runtime._settings
            s.set("provider", self._provider_combo.currentText())

            model = self._model_input.text().strip()
            if model:
                s.set_model(model)

            s.set("temperature", round(self._temp_spin.value(), 2))
            s.set("max_tokens", self._max_tokens_spin.value())
            s.set("timeout", self._timeout_spin.value())

            api_key = self._api_key_input.text().strip()
            if api_key:
                s.set_api_key(api_key)

            self.runtime.switch_provider(self._provider_combo.currentText())
            self._status.setText("Settings saved successfully.")
            self._status.setStyleSheet(f"color: {colors.TEXT_SUCCESS};")
            self._api_key_input.clear()
        except Exception as exc:
            self._status.setText(f"Error: {exc}")
            self._status.setStyleSheet(f"color: {colors.TEXT_DANGER};")

    def _test_connection(self) -> None:
        if not self.runtime:
            return
        try:
            result = self.runtime._settings.test_connection()
            if result.get("connected"):
                latency = result.get("latency_ms", 0)
                msg = result.get("message", "Connected")
                self._status.setText(f"{msg} ({latency:.0f}ms)")
                self._status.setStyleSheet(f"color: {colors.TEXT_SUCCESS};")
            else:
                error = result.get("error", "Unknown error")
                self._status.setText(f"Connection failed: {error}")
                self._status.setStyleSheet(f"color: {colors.TEXT_DANGER};")
        except Exception as exc:
            self._status.setText(f"Test failed: {exc}")
            self._status.setStyleSheet(f"color: {colors.TEXT_DANGER};")

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            s = self.runtime._settings
            self._provider_combo.setCurrentText(s.get_provider())
            self._model_input.setText(s.get_model())
            self._temp_spin.setValue(float(s.get("temperature", 0.7)))
            self._max_tokens_spin.setValue(int(s.get("max_tokens", 4096)))
            self._timeout_spin.setValue(int(s.get("timeout", 30)))
            self._status.setText("")
        except Exception:
            pass
