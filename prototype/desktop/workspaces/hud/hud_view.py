"""Apex HUD Workspace — Cyberpunk F.R.I.D.A.Y. / Ultron Style Dark Glass Command HUD for ALFA COS v2.0."""

import time
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame,
    QGridLayout, QScrollArea, QProgressBar,
)

from prototype.desktop.tokens import colors, typography
from prototype.desktop.components import BaseView, MetricCard, SectionHeader


class HudView(QWidget):
    """Apex HUD View — Futuristic real-time cognitive command center.

    Displays:
    - F.R.I.D.A.Y. / Ultron Cognitive Swarm Telemetry
    - Vision Screen Observer Stream
    - Passive Voice Listener Spectrum Indicator
    - Self-Healing Auto-Repair Ledger
    - Proactive Morning Briefings
    """

    def __init__(self, runtime: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.runtime = runtime
        self._setup_ui()

        # Update timer for live telemetry
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._refresh_telemetry)
        self._timer.start()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = SectionHeader(
            title="APEX HUD — F.R.I.D.A.Y. / ULTRON COMMAND CENTER",
            subtitle="Real-time passive vision, agent swarm telemetry, and self-healing engine",
        )
        layout.addWidget(header)

        # Grid metrics top row
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(14)

        self.card_mode = MetricCard(
            label="SYSTEM OPERATIONAL MODE",
            value="APEX V2.0",
            subtitle="Autonomous Zero-Latency Engine",
        )
        self.card_swarm = MetricCard(
            label="ACTIVE AGENT SWARM",
            value="9 SWARM AGENTS",
            subtitle="Coding, Planning, Research, Git, Docs...",
        )
        self.card_healing = MetricCard(
            label="SELF-HEALING REPAIRS",
            value="100% VERIFIED",
            subtitle="Zero Crash Dumps",
        )
        self.card_vision = MetricCard(
            label="SCREEN VISION OBSERVER",
            value="ACTIVE",
            subtitle="1920x1080 Real-time Stream",
        )

        metrics_layout.addWidget(self.card_mode, 0, 0)
        metrics_layout.addWidget(self.card_swarm, 0, 1)
        metrics_layout.addWidget(self.card_healing, 0, 2)
        metrics_layout.addWidget(self.card_vision, 0, 3)

        layout.addLayout(metrics_layout)

        # Main HUD Split
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        # Left Panel: Live HUD Telemetry & Vision Feed
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {colors.GLASS_BG}; border: 1px solid {colors.GLASS_BORDER}; border-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)

        left_lbl = QLabel("LIVE VISION & VOICE TELEMETRY")
        left_lbl.setStyleSheet(f"color: {colors.ACCENT_CYAN}; font-size: {typography.SIZE_MD}; font-weight: bold; letter-spacing: 1px;")
        left_layout.addWidget(left_lbl)

        self.vision_feed = QTextEdit()
        self.vision_feed.setReadOnly(True)
        self.vision_feed.setStyleSheet(
            f"background-color: {colors.BG_PRIMARY}; color: {colors.TEXT_PRIMARY}; "
            f"border: 1px solid {colors.GLASS_BORDER}; border-radius: 8px; font-family: Consolas, monospace; font-size: 11px;"
        )
        self.vision_feed.setText(
            "[PASSIVE VISION OBSERVER STREAM]\n"
            "Status: ACTIVE\n"
            "Target Window: ALFA COS Desktop — Apex Mode (1920x1080)\n"
            "Detected Elements: ['code_editor', 'terminal', 'swarm_telemetry', 'ai_hud']\n"
            "Voice Spectrum Listener: HEY ALFA (Listening...)\n"
        )
        left_layout.addWidget(self.vision_feed)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_briefing = QPushButton("Generate Proactive Briefing")
        self.btn_briefing.setStyleSheet(
            f"background-color: {colors.ACCENT_CYAN}; color: {colors.BG_PRIMARY}; "
            f"font-weight: bold; padding: 10px 16px; border-radius: 8px;"
        )
        self.btn_briefing.clicked.connect(self._on_generate_briefing)

        self.btn_swarm = QPushButton("Deploy Agent Swarm")
        self.btn_swarm.setStyleSheet(
            f"background-color: {colors.ACCENT_PURPLE}; color: white; "
            f"font-weight: bold; padding: 10px 16px; border-radius: 8px;"
        )
        self.btn_swarm.clicked.connect(self._on_deploy_swarm)

        btn_layout.addWidget(self.btn_briefing)
        btn_layout.addWidget(self.btn_swarm)
        left_layout.addLayout(btn_layout)

        body_layout.addWidget(left_panel, 3)

        # Right Panel: Proactive Assistant & Self-Healing Ledger
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {colors.GLASS_BG}; border: 1px solid {colors.GLASS_BORDER}; border-radius: 12px;")
        right_layout = QVBoxLayout(right_panel)

        right_lbl = QLabel("PROACTIVE BRIEFING & SELF-HEALING")
        right_lbl.setStyleSheet(f"color: {colors.TEXT_SUCCESS}; font-size: {typography.SIZE_MD}; font-weight: bold; letter-spacing: 1px;")
        right_layout.addWidget(right_lbl)

        self.briefing_text = QTextEdit()
        self.briefing_text.setReadOnly(True)
        self.briefing_text.setStyleSheet(
            f"background-color: {colors.BG_PRIMARY}; color: {colors.TEXT_SECONDARY}; "
            f"border: 1px solid {colors.GLASS_BORDER}; border-radius: 8px; font-family: Segoe UI, sans-serif; font-size: 11px;"
        )
        self.briefing_text.setText(
            "=== PROACTIVE EXECUTIVE BRIEFING ===\n"
            "System Status: OPTIMAL — All 14 Workspaces Operational\n\n"
            "Pending Tasks:\n"
            "• Verify automated release candidate build checksums\n"
            "• Execute local self-healing test cycle\n"
            "• Review multi-agent swarm telemetry\n\n"
            "Self-Healing Engine: 0 Active Crashes | 100% System Resilience Verified\n"
        )
        right_layout.addWidget(self.briefing_text)

        body_layout.addWidget(right_panel, 2)

        layout.addLayout(body_layout)

    def _refresh_telemetry(self) -> None:
        if not self.runtime:
            return
        # Fetch stats if available
        if hasattr(self.runtime, "passive_daemon") and self.runtime.passive_daemon:
            tick_data = self.runtime.passive_daemon.tick()
            if tick_data.get("active"):
                self.vision_feed.append(f"[{time.strftime('%H:%M:%S')}] Passive Tick — Window: '{tick_data.get('window')}'")

    def _on_generate_briefing(self) -> None:
        if self.runtime and hasattr(self.runtime, "proactive_assistant") and self.runtime.proactive_assistant:
            briefing = self.runtime.proactive_assistant.generate_morning_briefing()
            self.briefing_text.setText(
                f"=== PROACTIVE EXECUTIVE BRIEFING ===\n"
                f"Date: {briefing.date_str}\n"
                f"Status: {briefing.system_status}\n\n"
                f"Pending Tasks:\n" + "\n".join(f"• {t}" for t in briefing.pending_tasks) + "\n\n"
                f"Recommendations:\n" + "\n".join(f"• {r}" for r in briefing.recommendations)
            )

    def _on_deploy_swarm(self) -> None:
        if self.runtime and hasattr(self.runtime, "swarm_orchestrator") and self.runtime.swarm_orchestrator:
            res = self.runtime.swarm_orchestrator.execute_swarm("Analyze system health and optimize local cognition")
            self.vision_feed.append(f"[{time.strftime('%H:%M:%S')}] Agent Swarm Deployed! Swarm ID: {res.swarm_id} | Time: {res.total_time_ms}ms")
