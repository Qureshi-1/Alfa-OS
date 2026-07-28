"""Planner Workspace — interactive task tree, goal hierarchy, and step progress visualization."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTreeWidget, QTreeWidgetItem, QPushButton, QProgressBar,
)
from PySide6.QtCore import Qt

from prototype.desktop.components.base_view import BaseView
from prototype.desktop.components.empty_state import EmptyState
from prototype.desktop.tokens import colors, typography, spacing, radii


class PlannerView(BaseView):
    """Planner workspace visualizer — task hierarchy, execution graph, step progress."""

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
        header = self._make_header("Planner & Goal Engine", "Autonomous goal decomposition and step execution hierarchy")
        layout.addWidget(header)

        # Progress Overview Card
        progress_card = QFrame()
        progress_card.setObjectName("card")
        p_layout = QVBoxLayout(progress_card)
        p_layout.setContentsMargins(16, 12, 16, 12)
        p_layout.setSpacing(8)

        p_header = QHBoxLayout()
        p_title = QLabel("Overall Goal Progress")
        p_title.setObjectName("subheading")
        p_header.addWidget(p_title)
        p_header.addStretch()

        self._p_label = QLabel("Idle \u2014 No Active Plan")
        self._p_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; font-size: 11px;")
        p_header.addWidget(self._p_label)
        p_layout.addLayout(p_header)

        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        p_layout.addWidget(self._progress_bar)

        layout.addWidget(progress_card)

        # Task Tree Widget
        tree_card = QFrame()
        tree_card.setObjectName("card")
        tree_layout = QVBoxLayout(tree_card)
        tree_layout.setContentsMargins(16, 14, 16, 14)
        tree_layout.setSpacing(10)

        tree_header = QHBoxLayout()
        t_title = QLabel("Goal Hierarchy & Task Tree")
        t_title.setObjectName("subheading")
        tree_header.addWidget(t_title)
        tree_header.addStretch()

        btn_refresh = QPushButton("Re-evaluate Plan")
        btn_refresh.clicked.connect(self.refresh)
        tree_header.addWidget(btn_refresh)
        tree_layout.addLayout(tree_header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Goal / Subtask", "Status", "Priority", "Progress"])
        self.tree.setColumnWidth(0, 320)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 100)
        tree_layout.addWidget(self.tree)

        self.empty_state = EmptyState("No active goal tree", "Create a task in Chat or Assistant to decompose goals into steps.")
        tree_layout.addWidget(self.empty_state)
        self.empty_state.hide()

        layout.addWidget(tree_card)
        layout.addStretch()

        scroll.setWidget(container)
        self._root.addWidget(scroll)

    def refresh(self) -> None:
        if not self.runtime:
            return
        try:
            planner = getattr(self.runtime, "planner", None)
            stats = self.runtime.get_stats()
            
            self.tree.clear()

            # Populated goals if available from planner
            goals = planner.get_goals() if planner and hasattr(planner, "get_goals") else []
            
            if not goals:
                self.tree.hide()
                self.empty_state.show()
                self._p_label.setText("Engine Idle")
                self._progress_bar.setValue(0)
            else:
                self.empty_state.hide()
                self.tree.show()
                for goal in goals:
                    item = QTreeWidgetItem([goal.get("title", "Goal"), goal.get("status", "Pending"), goal.get("priority", "Normal"), "100%"])
                    self.tree.addTopLevelItem(item)
                self._p_label.setText("Active Goal Decomposed")
                self._progress_bar.setValue(100)
        except Exception:
            pass
