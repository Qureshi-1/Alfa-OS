"""Status Bars — top and bottom bars for system information."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer

from prototype.desktop.tokens import colors, typography, spacing


class TopBar(QWidget):
    """Top status bar — provider, model, system status."""

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(40)
        self._runtime = runtime

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        # Left: app title
        self._title = QLabel("ALFA COS")
        self._title.setStyleSheet(f"color: {colors.TEXT_ACCENT}; font-weight: 700; font-size: 12px; letter-spacing: 1px;")
        layout.addWidget(self._title)

        layout.addSpacing(24)

        # Provider indicator
        self._provider = QLabel("")
        self._provider.setObjectName("caption")
        layout.addWidget(self._provider)

        # Model indicator
        self._model = QLabel("")
        self._model.setObjectName("caption")
        layout.addWidget(self._model)

        layout.addStretch()

        # Right: system indicators
        self._uptime = QLabel("")
        self._uptime.setObjectName("caption")
        layout.addWidget(self._uptime)

        self._status = QLabel("\u25CF")
        self._status.setStyleSheet(f"color: {colors.SUCCESS}; font-size: 10px;")
        layout.addWidget(self._status)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            settings = self._runtime._settings
            provider = settings.get_provider()
            model = settings.get_model()
            self._provider.setText(f"Provider: {provider}")
            self._model.setText(f"Model: {model}")

            stats = self._runtime.get_stats()
            exec_stats = stats.get("executive", {})
            total = exec_stats.get("total_executions", 0)
            self._uptime.setText(f"Executions: {total}")
        except Exception:
            pass


class BottomBar(QWidget):
    """Bottom status bar — memory, workers, agent count."""

    def __init__(self, runtime=None, parent=None):
        super().__init__(parent)
        self.setObjectName("bottomBar")
        self.setFixedHeight(28)
        self._runtime = runtime

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        self._memory_label = QLabel("Memory: 0")
        self._memory_label.setObjectName("caption")
        layout.addWidget(self._memory_label)

        self._workers_label = QLabel("Workers: 0")
        self._workers_label.setObjectName("caption")
        layout.addWidget(self._workers_label)

        self._agents_label = QLabel("Agents: 0")
        self._agents_label.setObjectName("caption")
        layout.addWidget(self._agents_label)

        layout.addStretch()

        self._plugins_label = QLabel("Plugins: 0")
        self._plugins_label.setObjectName("caption")
        layout.addWidget(self._plugins_label)

    def refresh(self) -> None:
        if not self._runtime:
            return
        try:
            stats = self._runtime.get_stats()
            mem = stats.get("memory", {})
            workers = stats.get("workers", {})
            agents = stats.get("agents", {})
            plugins = stats.get("plugins", [])

            working = mem.get("working_count", 0)
            persistent = mem.get("persistent_count", 0)
            self._memory_label.setText(f"Memory: {working} working / {persistent} persistent")

            worker_count = workers.get("worker_count", 0)
            running = workers.get("running", 0)
            self._workers_label.setText(f"Workers: {worker_count} ({running} running)")

            agent_count = agents.get("agent_count", 0)
            self._agents_label.setText(f"Agents: {agent_count}")

            self._plugins_label.setText(f"Plugins: {len(plugins)}")
        except Exception:
            pass
