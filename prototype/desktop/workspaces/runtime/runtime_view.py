"""Runtime Workspace — hardware gauges, process monitor, event stream log."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QTextEdit,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.chart_widget import MiniGaugeWidget, ExecutionGraphWidget
from prototype.desktop.tokens import colors, typography


class RuntimeView(BaseView):
    """Runtime workspace — system telemetry visualizer, process list, kernel event stream."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header = self._make_header("Runtime Engine & Telemetry Monitor", "Live CPU/RAM/GPU performance meters, process status, and kernel logs")
        layout.addWidget(header)

        # Telemetry Gauges Card
        t_card = QFrame()
        t_card.setObjectName("card")
        t_layout = QVBoxLayout(t_card)
        t_layout.setContentsMargins(16, 14, 16, 14)
        t_layout.setSpacing(12)

        t_title = QLabel("Hardware Telemetry Meters")
        t_title.setObjectName("subheading")
        t_layout.addWidget(t_title)

        g_row = QHBoxLayout()
        g_row.setSpacing(16)
        self.g_cpu = MiniGaugeWidget("CPU Load", 18.0, "%", accent_color=colors.ACCENT_CYAN)
        self.g_ram = MiniGaugeWidget("RAM Usage", 42.0, "%", accent_color=colors.ACCENT_SECONDARY)
        self.g_gpu = MiniGaugeWidget("GPU Compute", 24.0, "%", accent_color=colors.ACCENT_PURPLE)

        g_row.addWidget(self.g_cpu)
        g_row.addWidget(self.g_ram)
        g_row.addWidget(self.g_gpu)
        t_layout.addLayout(g_row)

        layout.addWidget(t_card)

        # Execution Activity & Event Stream
        logs_card = QFrame()
        logs_card.setObjectName("card")
        l_layout = QVBoxLayout(logs_card)
        l_layout.setContentsMargins(16, 14, 16, 14)
        l_layout.setSpacing(8)

        l_header = QHBoxLayout()
        l_title = QLabel("Kernel Event Stream & Logs")
        l_title.setObjectName("subheading")
        l_header.addWidget(l_title)
        l_header.addStretch()

        btn_clear = QPushButton("Clear Stream")
        btn_clear.clicked.connect(self._clear_logs)
        l_header.addWidget(btn_clear)
        l_layout.addLayout(l_header)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFixedHeight(220)
        self.log_edit.setPlaceholderText("Streaming runtime events...")
        self.log_edit.setStyleSheet(f"font-family: {typography.FONT_MONO}; font-size: 11px; background-color: {colors.BG_INPUT}; color: {colors.TEXT_PRIMARY};")
        l_layout.addWidget(self.log_edit)

        layout.addWidget(logs_card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def _clear_logs(self) -> None:
        self.log_edit.clear()

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            events = self.runtime.event_bus.get_history(limit=10)
            lines = []
            for ev in reversed(events):
                ts = ev.timestamp.strftime("%H:%M:%S") if hasattr(ev.timestamp, "strftime") else "??:??:??"
                lines.append(f"[{ts}] [{ev.source.upper()}] {ev.event_type} — Payload: {ev.data}")
            self.log_edit.setPlainText("\n".join(lines) if lines else "No kernel events logged yet.")
        except Exception:
            pass
