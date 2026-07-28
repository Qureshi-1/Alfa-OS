"""Settings workspace — tabbed interface for provider, AI, memory, runtime, appearance, extensions, security."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QFormLayout, QMessageBox, QGroupBox, QTextEdit,
    QTabWidget, QCheckBox,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.tokens import colors, typography, spacing, radii


class SettingsView(BaseView):
    """Settings workspace with tabbed navigation: General, AI, Memory, Runtime, Appearance, Extensions, Security."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Header
        header = self._make_header("Settings & Preferences", "Configure system providers, memory limits, runtime policies, and appearance")
        layout.addWidget(header)

        # Main Tab Widget
        self.tabs = QTabWidget()
        
        # ── TAB 1: AI Provider & Models ──────────────────────────────
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_layout.setContentsMargins(16, 16, 16, 16)
        ai_layout.setSpacing(12)

        provider_group = QGroupBox("AI Provider & API Configuration")
        pf = QFormLayout(provider_group)
        pf.setSpacing(10)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["gemini", "mock", "nvidia", "openrouter", "ollama", "openai", "claude"])
        pf.addRow("Active Provider:", self._provider_combo)

        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("Model identifier (e.g. gemini-3.6-flash)")
        pf.addRow("Model Name:", self._model_input)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("API key (encrypted)")
        pf.addRow("API Key:", self._api_key_input)

        ai_layout.addWidget(provider_group)

        gen_group = QGroupBox("Generation Parameters")
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

        ai_layout.addWidget(gen_group)
        ai_layout.addStretch()
        self.tabs.addTab(ai_tab, "AI & Models")

        # ── TAB 2: General ───────────────────────────────────────────
        gen_tab = QWidget()
        gt_layout = QVBoxLayout(gen_tab)
        gt_layout.setContentsMargins(16, 16, 16, 16)
        gt_layout.setSpacing(10)
        gt_layout.addWidget(QLabel("General Preferences"))
        chk_autostart = QCheckBox("Auto-start runtime engine on desktop launch")
        chk_autostart.setChecked(True)
        gt_layout.addWidget(chk_autostart)
        chk_telemetry = QCheckBox("Enable live hardware telemetry polling")
        chk_telemetry.setChecked(True)
        gt_layout.addWidget(chk_telemetry)
        gt_layout.addStretch()
        self.tabs.addTab(gen_tab, "General")

        # ── TAB 3: Memory ────────────────────────────────────────────
        mem_tab = QWidget()
        mt_layout = QVBoxLayout(mem_tab)
        mt_layout.setContentsMargins(16, 16, 16, 16)
        mt_layout.setSpacing(10)
        mt_layout.addWidget(QLabel("Memory Engine Parameters"))
        chk_mem = QCheckBox("Enable long-term vector persistence storage")
        chk_mem.setChecked(True)
        mt_layout.addWidget(chk_mem)
        mt_layout.addStretch()
        self.tabs.addTab(mem_tab, "Memory")

        # ── TAB 4: Runtime ───────────────────────────────────────────
        rt_tab = QWidget()
        rt_layout = QVBoxLayout(rt_tab)
        rt_layout.setContentsMargins(16, 16, 16, 16)
        rt_layout.setSpacing(10)
        rt_layout.addWidget(QLabel("Kernel & Execution Scheduler Policies"))
        chk_rt = QCheckBox("Strict sandboxed tool execution mode")
        chk_rt.setChecked(True)
        rt_layout.addWidget(chk_rt)
        rt_layout.addStretch()
        self.tabs.addTab(rt_tab, "Runtime")

        # ── TAB 5: Appearance ────────────────────────────────────────
        app_tab = QWidget()
        ap_layout = QVBoxLayout(app_tab)
        ap_layout.setContentsMargins(16, 16, 16, 16)
        ap_layout.setSpacing(10)
        ap_layout.addWidget(QLabel("Theme & Visual Styling"))
        lbl_theme = QLabel("Theme Palette: Dark Graphite (Cyber Cyan Accent)")
        lbl_theme.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-weight: bold;")
        ap_layout.addWidget(lbl_theme)
        ap_layout.addStretch()
        self.tabs.addTab(app_tab, "Appearance")

        # ── TAB 6: Extensions ────────────────────────────────────────
        ext_tab = QWidget()
        ex_layout = QVBoxLayout(ext_tab)
        ex_layout.setContentsMargins(16, 16, 16, 16)
        ex_layout.setSpacing(10)
        ex_layout.addWidget(QLabel("Plugin Extension Directory"))
        chk_ext = QCheckBox("Allow third-party workspace plugin loading")
        chk_ext.setChecked(True)
        ex_layout.addWidget(chk_ext)
        ex_layout.addStretch()
        self.tabs.addTab(ext_tab, "Extensions")

        # ── TAB 7: Security ──────────────────────────────────────────
        sec_tab = QWidget()
        sec_layout = QVBoxLayout(sec_tab)
        sec_layout.setContentsMargins(16, 16, 16, 16)
        sec_layout.setSpacing(10)
        sec_layout.addWidget(QLabel("Security & Access Control Matrix"))
        chk_sec = QCheckBox("Prompt for permission on filesystem write operations")
        chk_sec.setChecked(True)
        sec_layout.addWidget(chk_sec)
        sec_layout.addStretch()
        self.tabs.addTab(sec_tab, "Security")

        layout.addWidget(self.tabs, 1)

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

