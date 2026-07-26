"""Stylesheet — centralized QSS for all ALFA COS widgets."""

from prototype.desktop.tokens import colors, typography, spacing, radii, sizes


def build_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return f"""
    /* ═══════════════════════════════════════════════════════════════════
       ALFA COS — Cyber Blue Dark Glass Theme
       ═══════════════════════════════════════════════════════════════════ */

    * {{
        font-family: {typography.FONT_FAMILY};
        font-size: {typography.SIZE_BASE};
        color: {colors.TEXT_PRIMARY};
    }}

    /* ── QMainWindow ──────────────────────────────────────────────── */
    QMainWindow {{
        background-color: {colors.BG_PRIMARY};
    }}

    /* ── QWidget ──────────────────────────────────────────────────── */
    QWidget {{
        background-color: transparent;
    }}

    /* ── Sidebar ──────────────────────────────────────────────────── */
    QWidget#sidebar {{
        background-color: {colors.BG_SECONDARY};
        border-right: 1px solid {colors.BORDER_SECONDARY};
    }}

    QWidget#sidebar QPushButton {{
        background-color: transparent;
        border: none;
        border-radius: {radii.MD};
        padding: {spacing.MD};
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        color: {colors.TEXT_SECONDARY};
    }}

    QWidget#sidebar QPushButton:hover {{
        background-color: {colors.BG_HOVER};
        color: {colors.TEXT_PRIMARY};
    }}

    QWidget#sidebar QPushButton[active="true"] {{
        background-color: {colors.ACCENT_SUBTLE};
        color: {colors.ACCENT_SECONDARY};
        border-left: 2px solid {colors.ACCENT_PRIMARY};
    }}

    /* ── Top Status Bar ───────────────────────────────────────────── */
    QWidget#topBar {{
        background-color: {colors.BG_SECONDARY};
        border-bottom: 1px solid {colors.BORDER_SECONDARY};
    }}

    /* ── Bottom Status Bar ────────────────────────────────────────── */
    QWidget#bottomBar {{
        background-color: {colors.BG_SECONDARY};
        border-top: 1px solid {colors.BORDER_SECONDARY};
    }}

    /* ── Central Workspace ────────────────────────────────────────── */
    QWidget#workspace {{
        background-color: {colors.BG_PRIMARY};
    }}

    /* ── Right Panel ──────────────────────────────────────────────── */
    QWidget#rightPanel {{
        background-color: {colors.BG_SECONDARY};
        border-left: 1px solid {colors.BORDER_SECONDARY};
    }}

    /* ── Cards ────────────────────────────────────────────────────── */
    QFrame#card {{
        background-color: {colors.BG_SURFACE};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.LG};
        padding: {spacing.XL};
    }}

    QFrame#card:hover {{
        border-color: {colors.BORDER_PRIMARY};
        background-color: {colors.BG_ELEVATED};
    }}

    QFrame#cardAccent {{
        background-color: {colors.BG_SURFACE};
        border: 1px solid {colors.BORDER_PRIMARY};
        border-radius: {radii.LG};
        padding: {spacing.XL};
    }}

    /* ── Labels ───────────────────────────────────────────────────── */
    QLabel {{
        color: {colors.TEXT_PRIMARY};
        background: transparent;
    }}

    QLabel#heading {{
        font-size: {typography.SIZE_2XL};
        font-weight: {typography.WEIGHT_BOLD};
        color: {colors.TEXT_PRIMARY};
    }}

    QLabel#subheading {{
        font-size: {typography.SIZE_LG};
        font-weight: {typography.WEIGHT_MEDIUM};
        color: {colors.TEXT_SECONDARY};
    }}

    QLabel#caption {{
        font-size: {typography.SIZE_SM};
        color: {colors.TEXT_MUTED};
    }}

    QLabel#accent {{
        color: {colors.TEXT_ACCENT};
        font-weight: {typography.WEIGHT_MEDIUM};
    }}

    QLabel#success {{
        color: {colors.TEXT_SUCCESS};
    }}

    QLabel#danger {{
        color: {colors.TEXT_DANGER};
    }}

    QLabel#warning {{
        color: {colors.TEXT_WARNING};
    }}

    QLabel#value {{
        font-size: {typography.SIZE_2XL};
        font-weight: {typography.WEIGHT_BOLD};
        color: {colors.TEXT_PRIMARY};
    }}

    QLabel#mono {{
        font-family: {typography.FONT_MONO};
        font-size: {typography.SIZE_MD};
    }}

    /* ── Buttons ──────────────────────────────────────────────────── */
    QPushButton {{
        background-color: {colors.BG_ELEVATED};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.MD};
        padding: {spacing.MD} {spacing.XL};
        min-height: {sizes.BUTTON_HEIGHT};
        color: {colors.TEXT_PRIMARY};
        font-weight: {typography.WEIGHT_MEDIUM};
    }}

    QPushButton:hover {{
        background-color: {colors.BG_HOVER};
        border-color: {colors.BORDER_PRIMARY};
    }}

    QPushButton:pressed {{
        background-color: {colors.BG_ACTIVE};
    }}

    QPushButton:disabled {{
        background-color: {colors.BG_TERTIARY};
        color: {colors.TEXT_MUTED};
        border-color: {colors.BORDER_SECONDARY};
    }}

    QPushButton#primary {{
        background-color: {colors.ACCENT_PRIMARY};
        border-color: {colors.ACCENT_PRIMARY};
        color: white;
    }}

    QPushButton#primary:hover {{
        background-color: {colors.ACCENT_SECONDARY};
    }}

    QPushButton#danger {{
        background-color: transparent;
        border-color: {colors.DANGER};
        color: {colors.DANGER};
    }}

    QPushButton#danger:hover {{
        background-color: {colors.DANGER_BG};
    }}

    QPushButton#ghost {{
        background-color: transparent;
        border: none;
        color: {colors.TEXT_SECONDARY};
    }}

    QPushButton#ghost:hover {{
        background-color: {colors.BG_HOVER};
        color: {colors.TEXT_PRIMARY};
    }}

    /* ── Input Fields ─────────────────────────────────────────────── */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {colors.BG_INPUT};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.MD};
        padding: {spacing.MD} {spacing.LG};
        min-height: {sizes.INPUT_HEIGHT};
        color: {colors.TEXT_PRIMARY};
        selection-background-color: {colors.ACCENT_PRIMARY};
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {colors.BORDER_FOCUS};
    }}

    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {colors.BG_TERTIARY};
        color: {colors.TEXT_MUTED};
    }}

    QTextEdit {{
        background-color: {colors.BG_INPUT};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.MD};
        padding: {spacing.MD};
        color: {colors.TEXT_PRIMARY};
        selection-background-color: {colors.ACCENT_PRIMARY};
    }}

    QTextEdit:focus {{
        border-color: {colors.BORDER_FOCUS};
    }}

    /* ── ComboBox ─────────────────────────────────────────────────── */
    QComboBox {{
        background-color: {colors.BG_INPUT};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.MD};
        padding: {spacing.MD} {spacing.LG};
        min-height: {sizes.INPUT_HEIGHT};
        color: {colors.TEXT_PRIMARY};
    }}

    QComboBox:hover {{
        border-color: {colors.BORDER_PRIMARY};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {colors.TEXT_SECONDARY};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {colors.BG_ELEVATED};
        border: 1px solid {colors.BORDER_PRIMARY};
        border-radius: {radii.MD};
        padding: {spacing.SM};
        selection-background-color: {colors.ACCENT_SUBTLE};
        selection-color: {colors.TEXT_PRIMARY};
        outline: none;
    }}

    /* ── Tables ───────────────────────────────────────────────────── */
    QTableWidget {{
        background-color: {colors.BG_INPUT};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.MD};
        gridline-color: {colors.BORDER_SECONDARY};
        selection-background-color: {colors.ACCENT_SUBTLE};
        selection-color: {colors.TEXT_PRIMARY};
        outline: none;
    }}

    QTableWidget::item {{
        padding: {spacing.MD};
        border-bottom: 1px solid {colors.BORDER_SECONDARY};
    }}

    QTableWidget::item:selected {{
        background-color: {colors.ACCENT_SUBTLE};
    }}

    QTableWidget::item:hover {{
        background-color: {colors.BG_HOVER};
    }}

    QHeaderView::section {{
        background-color: {colors.BG_TERTIARY};
        color: {colors.TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {colors.BORDER_SECONDARY};
        border-right: 1px solid {colors.BORDER_SECONDARY};
        padding: {spacing.MD} {spacing.LG};
        font-weight: {typography.WEIGHT_SEMIBOLD};
        font-size: {typography.SIZE_SM};
        text-transform: uppercase;
    }}

    QHeaderView::section:hover {{
        background-color: {colors.BG_HOVER};
    }}

    /* ── Scroll Bars ──────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors.BG_HOVER};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors.TEXT_MUTED};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {colors.BG_HOVER};
        border-radius: 4px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {colors.TEXT_MUTED};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ── Tab Widget ───────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}

    /* ── Splitter ─────────────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {colors.BORDER_SECONDARY};
        width: 1px;
        height: 1px;
    }}

    QSplitter::handle:hover {{
        background-color: {colors.ACCENT_PRIMARY};
    }}

    /* ── Progress Bar ─────────────────────────────────────────────── */
    QProgressBar {{
        background-color: {colors.BG_TERTIARY};
        border: none;
        border-radius: {radii.SM};
        height: 4px;
        text-align: center;
        color: transparent;
    }}

    QProgressBar::chunk {{
        background-color: {colors.ACCENT_PRIMARY};
        border-radius: {radii.SM};
    }}

    /* ── ToolTip ──────────────────────────────────────────────────── */
    QToolTip {{
        background-color: {colors.BG_ELEVATED};
        border: 1px solid {colors.BORDER_PRIMARY};
        border-radius: {radii.MD};
        padding: {spacing.SM} {spacing.MD};
        color: {colors.TEXT_PRIMARY};
        font-size: {typography.SIZE_SM};
    }}

    /* ── Menu ─────────────────────────────────────────────────────── */
    QMenu {{
        background-color: {colors.BG_ELEVATED};
        border: 1px solid {colors.BORDER_PRIMARY};
        border-radius: {radii.MD};
        padding: {spacing.SM};
    }}

    QMenu::item {{
        padding: {spacing.MD} {spacing.XL};
        border-radius: {radii.SM};
    }}

    QMenu::item:selected {{
        background-color: {colors.ACCENT_SUBTLE};
    }}

    /* ── Status Dot ───────────────────────────────────────────────── */
    QLabel#statusDot {{
        min-width: 8px;
        max-width: 8px;
        min-height: 8px;
        max-height: 8px;
        border-radius: 4px;
    }}

    QLabel#statusDotOnline {{
        background-color: {colors.SUCCESS};
    }}

    QLabel#statusDotOffline {{
        background-color: {colors.DANGER};
    }}

    QLabel#statusDotWarning {{
        background-color: {colors.WARNING};
    }}

    /* ── Badge ────────────────────────────────────────────────────── */
    QLabel#badge {{
        background-color: {colors.ACCENT_SUBTLE};
        color: {colors.ACCENT_SECONDARY};
        border-radius: {radii.FULL};
        padding: {spacing.XS} {spacing.MD};
        font-size: {typography.SIZE_XS};
        font-weight: {typography.WEIGHT_SEMIBOLD};
    }}

    QLabel#badgeDanger {{
        background-color: {colors.DANGER_BG};
        color: {colors.DANGER};
        border-radius: {radii.FULL};
        padding: {spacing.XS} {spacing.MD};
        font-size: {typography.SIZE_XS};
        font-weight: {typography.WEIGHT_SEMIBOLD};
    }}

    QLabel#badgeSuccess {{
        background-color: {colors.SUCCESS_BG};
        color: {colors.SUCCESS};
        border-radius: {radii.FULL};
        padding: {spacing.XS} {spacing.MD};
        font-size: {typography.SIZE_XS};
        font-weight: {typography.WEIGHT_SEMIBOLD};
    }}

    QLabel#badgeWarning {{
        background-color: {colors.WARNING_BG};
        color: {colors.WARNING};
        border-radius: {radii.FULL};
        padding: {spacing.XS} {spacing.MD};
        font-size: {typography.SIZE_XS};
        font-weight: {typography.WEIGHT_SEMIBOLD};
    }}

    /* ── Separator ────────────────────────────────────────────────── */
    QFrame#separator {{
        background-color: {colors.BORDER_SECONDARY};
        max-height: 1px;
    }}

    QFrame#separatorV {{
        background-color: {colors.BORDER_SECONDARY};
        max-width: 1px;
    }}

    /* ── Panel Header ─────────────────────────────────────────────── */
    QWidget#panelHeader {{
        background-color: transparent;
        border-bottom: 1px solid {colors.BORDER_SECONDARY};
        padding: {spacing.MD} {spacing.XL};
    }}

    /* ── Metric Card ──────────────────────────────────────────────── */
    QFrame#metricCard {{
        background-color: {colors.BG_SURFACE};
        border: 1px solid {colors.BORDER_SECONDARY};
        border-radius: {radii.LG};
        padding: {spacing.LG};
    }}

    QFrame#metricCard:hover {{
        border-color: {colors.BORDER_PRIMARY};
    }}
    """
