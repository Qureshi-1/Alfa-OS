"""Universal Model Hub workspace — model discovery, management, and switching."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QComboBox, QLineEdit,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.metric_card import MetricCard
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors


class ModelHubView(BaseView):
    """Universal Model Hub workspace — shows active provider/model, available providers."""

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

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Model Hub")
        title.setObjectName("heading")
        hdr.addWidget(title)
        hdr.addStretch()

        self._provider_filter = QComboBox()
        self._provider_filter.setFixedWidth(160)
        self._provider_filter.currentTextChanged.connect(lambda: self.refresh())
        hdr.addWidget(self._provider_filter)

        refresh_btn = QPushButton("\u21bb Refresh")
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        # Metrics
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_total = MetricCard("Total Models", "0")
        self.metric_local = MetricCard("Local Models", "0")
        self.metric_cloud = MetricCard("Cloud Models", "0")
        self.metric_active = MetricCard("Active Provider", "---")
        for card in [self.metric_total, self.metric_local, self.metric_cloud, self.metric_active]:
            metrics.addWidget(card)
        layout.addLayout(metrics)

        # Active model info
        info_card = QFrame()
        info_card.setObjectName("cardAccent")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)

        info_title = QLabel("Active Configuration")
        info_title.setObjectName("subheading")
        info_layout.addWidget(info_title)

        from prototype.desktop.components.info_row import InfoRow
        self.info_provider = InfoRow("Provider:")
        self.info_model = InfoRow("Model:")
        self.info_temperature = InfoRow("Temperature:")
        self.info_max_tokens = InfoRow("Max Tokens:")
        info_layout.addWidget(self.info_provider)
        info_layout.addWidget(self.info_model)
        info_layout.addWidget(self.info_temperature)
        info_layout.addWidget(self.info_max_tokens)
        layout.addWidget(info_card)

        # Models table
        self._table = DataTable(["Name", "Provider", "Family", "Context", "Modality", "Status"])
        self._table.set_column_width(0, 250)
        self._table.set_column_width(1, 100)
        self._table.set_column_width(2, 80)
        self._table.set_column_width(3, 80)
        self._table.set_column_width(4, 80)
        layout.addWidget(self._table, 1)

        self._empty = EmptyState("\u2699", "No models discovered",
                                 "Models appear here when detected from local paths or cloud providers")
        layout.addWidget(self._empty)

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            s = self.runtime._settings
            provider = s.get_provider()
            model = s.get_model()

            # Update active config display
            self.info_provider.set_value(provider)
            self.info_model.set_value(model)
            self.info_temperature.set_value(str(s.get("temperature", 0.7)))
            self.info_max_tokens.set_value(str(s.get("max_tokens", 4096)))
            self.metric_active.set_value(provider)

            # Provider filter
            self._provider_filter.blockSignals(True)
            cur = self._provider_filter.currentText()
            self._provider_filter.clear()
            self._provider_filter.addItem("All Providers")
            for p in ["mock", "nvidia", "openrouter", "ollama"]:
                self._provider_filter.addItem(p)
            if cur and self._provider_filter.findText(cur) >= 0:
                self._provider_filter.setCurrentText(cur)
            else:
                self._provider_filter.setCurrentText("All Providers")
            self._provider_filter.blockSignals(False)

            # Populate table from stats
            stats = self.runtime.get_stats()
            agent_stats = stats.get("agents", {})
            agent_count = agent_stats.get("agent_count", 0)
            self.metric_total.set_value(str(max(1, agent_count)))

            tools = stats.get("tools", [])
            self.metric_local.set_value(str(len(tools)))
            self.metric_cloud.set_value("1" if provider != "mock" else "0")

            # Show active model in table
            self._table.clear_data()
            self._table.show()
            self._empty.hide()

            modality = "text"
            family = "---"
            context = "---"
            if "llama" in model.lower():
                family = "llama"
                context = "128K"
            elif "qwen" in model.lower():
                family = "qwen"
                context = "32K"
            elif "mistral" in model.lower():
                family = "mistral"
                context = "32K"

            self._table.populate([[
                model, provider, family, context, modality, "Active"
            ]])

            # Show other available providers
            for p in ["nvidia", "openrouter", "ollama"]:
                if p == provider:
                    continue
                m = s.get(f"{p}_model", "") if p != "nvidia" else s.get("model", "")
                if m:
                    self._table.add_row([
                        m, p, "---", "---", "text", "Available"
                    ])

        except Exception:
            pass
