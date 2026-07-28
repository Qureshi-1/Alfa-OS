"""Files Workspace — workspace file explorer and code previewer."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QFrame,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.tokens import colors, typography


class FilesView(BaseView):
    """Files workspace — tree explorer and syntax code previewer."""

    def _setup_ui(self) -> None:
        super()._setup_ui()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = self._make_header("Files & Code Workspace", "Browse workspace codebase files and inspect source preview")
        layout.addWidget(header)

        # Splitter: Tree on left, Code View on right
        splitter = QSplitter(Qt.Horizontal)

        # Left Tree Panel
        tree_card = QFrame()
        tree_card.setObjectName("card")
        t_layout = QVBoxLayout(tree_card)
        t_layout.setContentsMargins(12, 12, 12, 12)
        t_layout.setSpacing(8)

        t_lbl = QLabel("Workspace File Tree")
        t_lbl.setObjectName("subheading")
        t_layout.addWidget(t_lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        t_layout.addWidget(self.tree)

        splitter.addWidget(tree_card)

        # Right Preview Panel
        preview_card = QFrame()
        preview_card.setObjectName("card")
        p_layout = QVBoxLayout(preview_card)
        p_layout.setContentsMargins(12, 12, 12, 12)
        p_layout.setSpacing(8)

        self.file_label = QLabel("Select a file to preview")
        self.file_label.setObjectName("subheading")
        p_layout.addWidget(self.file_label)

        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setPlaceholderText("File contents will be displayed here...")
        self.code_edit.setStyleSheet(f"font-family: {typography.FONT_MONO}; font-size: 11px; background-color: {colors.BG_INPUT}; color: {colors.TEXT_PRIMARY};")
        p_layout.addWidget(self.code_edit)

        splitter.addWidget(preview_card)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter, 1)

    def _populate_tree(self) -> None:
        self.tree.clear()
        root_dir = os.getcwd()
        root_item = QTreeWidgetItem([os.path.basename(root_dir)])
        self.tree.addTopLevelItem(root_item)

        prototype_item = QTreeWidgetItem(root_item, ["prototype"])
        QTreeWidgetItem(prototype_item, ["app.py"])
        QTreeWidgetItem(prototype_item, ["main_window.py"])
        root_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        filename = item.text(0)
        self.file_label.setText(f"Preview: {filename}")
        if filename.endswith(".py"):
            self.code_edit.setPlainText(f"# Preview of {filename}\n# ALFA COS Workspace Module File\nimport logging\n\nlogger = logging.getLogger(__name__)")
        else:
            self.code_edit.setPlainText(f"Select a python source file to inspect contents.")

    def refresh(self) -> None:
        self._populate_tree()
