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
        root_name = os.path.basename(root_dir) or "Alfa"
        root_item = QTreeWidgetItem([f"📁 {root_name}"])
        self.tree.addTopLevelItem(root_item)

        try:
            for item_name in sorted(os.listdir(root_dir)):
                if item_name.startswith(('.', '__')) or item_name in ('build', 'dist', 'release', '.venv'):
                    continue
                item_path = os.path.join(root_dir, item_name)
                if os.path.isdir(item_path):
                    dir_node = QTreeWidgetItem(root_item, [f"📁 {item_name}"])
                    try:
                        for child in sorted(os.listdir(item_path))[:12]:
                            if not child.startswith(('.', '__')):
                                icon = "📁" if os.path.isdir(os.path.join(item_path, child)) else "📄"
                                child_node = QTreeWidgetItem(dir_node, [f"{icon} {child}"])
                                child_node.setData(0, Qt.UserRole, os.path.join(item_path, child))
                    except Exception:
                        pass
                else:
                    file_node = QTreeWidgetItem(root_item, [f"📄 {item_name}"])
                    file_node.setData(0, Qt.UserRole, item_path)
        except Exception:
            pass

        root_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        file_path = item.data(0, Qt.UserRole)
        name = item.text(0).replace("📁 ", "").replace("📄 ", "")
        self.file_label.setText(f"Preview: {name}")

        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(4096)
                    if len(content) == 4096:
                        content += "\n... [truncated preview]"
                    self.code_edit.setPlainText(content)
            except Exception as e:
                self.code_edit.setPlainText(f"Error reading file: {e}")
        else:
            self.code_edit.setPlainText(f"Directory or non-previewable file: {name}")

    def refresh(self) -> None:
        self._populate_tree()
