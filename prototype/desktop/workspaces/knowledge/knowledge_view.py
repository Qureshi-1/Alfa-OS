"""Knowledge Workspace — knowledge graph explorer, vector search, and document indexer."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
    QLineEdit, QPushButton,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.data_table import DataTable
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography


class KnowledgeView(BaseView):
    """Knowledge workspace — RAG knowledge base search, entity graph, document indexer."""

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
        header = self._make_header("Knowledge Base & RAG Indexer", "Search indexed documents, entity relationship graphs, and vector stores")
        layout.addWidget(header)

        # Search Bar Card
        search_card = QFrame()
        search_card.setObjectName("card")
        s_layout = QHBoxLayout(search_card)
        s_layout.setContentsMargins(16, 12, 16, 12)
        s_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search knowledge items, entities, or vector chunks...")
        s_layout.addWidget(self.search_input, 1)

        btn_search = QPushButton("Search Index")
        btn_search.setObjectName("primary")
        s_layout.addWidget(btn_search)

        layout.addWidget(search_card)

        # Knowledge Items Table Card
        items_card = QFrame()
        items_card.setObjectName("card")
        i_layout = QVBoxLayout(items_card)
        i_layout.setContentsMargins(16, 14, 16, 14)
        i_layout.setSpacing(10)

        i_header = QLabel("Indexed Knowledge Items")
        i_header.setObjectName("subheading")
        i_layout.addWidget(i_header)

        self.table = DataTable(headers=["Entity / Doc ID", "Category", "Relevance", "Source Path", "Indexed Date"])
        i_layout.addWidget(self.table)

        self.empty = EmptyState("No knowledge items indexed", "Knowledge items will appear here when documents or memories are added.")
        i_layout.addWidget(self.empty)

        layout.addWidget(items_card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            stats = self.runtime.get_stats()
            mem_info = stats.get("memory", {})
            p_count = mem_info.get("persistent_count", 0)

            if p_count == 0:
                self.table.hide()
                self.empty.show()
            else:
                self.empty.hide()
                self.table.show()
                rows = [
                    ["system_core_spec", "Architecture", "1.00", "docs/AGENTS.md", "2026-07-28"],
                    ["memory_hypervisor_rules", "Memory", "0.95", "prototype/memory/", "2026-07-28"],
                ]
                self.table.populate(rows)
        except Exception:
            pass
