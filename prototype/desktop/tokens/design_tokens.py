"""Design Tokens — single source of truth for all ALFA COS visual values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    """Color palette — Dark Graphite Futuristic AI OS Theme."""
    # Backgrounds
    BG_PRIMARY = "#090c10"
    BG_SECONDARY = "#0d1117"
    BG_TERTIARY = "#131722"
    BG_SURFACE = "#161b26"
    BG_ELEVATED = "#1e2433"
    BG_HOVER = "#252d3f"
    BG_ACTIVE = "#2d374d"
    BG_INPUT = "#0d1117"

    # Glass & Cards
    GLASS_BG = "#161b26"
    GLASS_BORDER = "rgba(0, 229, 255, 0.14)"
    GLASS_HOVER = "rgba(0, 229, 255, 0.08)"

    # Accents
    ACCENT_CYAN = "#00e5ff"
    ACCENT_PRIMARY = "#00e5ff"
    ACCENT_SECONDARY = "#3b82f6"
    ACCENT_PURPLE = "#a855f7"
    ACCENT_GLOW = "rgba(0, 229, 255, 0.20)"
    ACCENT_SUBTLE = "rgba(0, 229, 255, 0.08)"

    # Text
    TEXT_PRIMARY = "#f3f4f6"
    TEXT_SECONDARY = "#9ca3af"
    TEXT_MUTED = "#6b7280"
    TEXT_ACCENT = "#00e5ff"
    TEXT_DANGER = "#f87171"
    TEXT_SUCCESS = "#34d399"
    TEXT_WARNING = "#fbbf24"

    # Semantic
    DANGER = "#ef4444"
    DANGER_BG = "rgba(239, 68, 68, 0.12)"
    SUCCESS = "#10b981"
    SUCCESS_BG = "rgba(16, 185, 129, 0.12)"
    WARNING = "#f59e0b"
    WARNING_BG = "rgba(245, 158, 11, 0.12)"
    INFO = "#3b82f6"
    INFO_BG = "rgba(59, 130, 246, 0.12)"

    # Borders
    BORDER_PRIMARY = "rgba(0, 229, 255, 0.22)"
    BORDER_SECONDARY = "rgba(255, 255, 255, 0.08)"
    BORDER_FOCUS = "rgba(0, 229, 255, 0.60)"

    # Shadows
    SHADOW_SM = "0 1px 3px rgba(0, 0, 0, 0.4)"
    SHADOW_MD = "0 4px 14px rgba(0, 0, 0, 0.5)"
    SHADOW_LG = "0 8px 32px rgba(0, 0, 0, 0.6)"


@dataclass(frozen=True)
class Typography:
    """Font families and sizes."""
    FONT_FAMILY = "'Inter', 'SF Pro Display', 'Segoe UI', -apple-system, sans-serif"
    FONT_MONO = "'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace"

    # Sizes
    SIZE_XS = "10px"
    SIZE_SM = "11px"
    SIZE_MD = "12px"
    SIZE_BASE = "13px"
    SIZE_LG = "14px"
    SIZE_XL = "16px"
    SIZE_2XL = "20px"
    SIZE_3XL = "26px"

    # Weights
    WEIGHT_NORMAL = "400"
    WEIGHT_MEDIUM = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD = "700"


@dataclass(frozen=True)
class Spacing:
    """Spacing scale."""
    XS = "2px"
    SM = "4px"
    MD = "8px"
    LG = "12px"
    XL = "16px"
    XXL = "24px"
    XXXL = "32px"


@dataclass(frozen=True)
class Radii:
    """Border radii scale — 12px cards."""
    SM = "4px"
    MD = "8px"
    LG = "12px"
    XL = "16px"
    FULL = "9999px"


@dataclass(frozen=True)
class Sizes:
    """Component sizes."""
    SIDEBAR_WIDTH = "60px"
    SIDEBAR_EXPANDED = "200px"
    STATUS_BAR_HEIGHT = "28px"
    TOP_BAR_HEIGHT = "42px"
    INPUT_HEIGHT = "34px"
    BUTTON_HEIGHT = "30px"
    ICON_SM = "14px"
    ICON_MD = "18px"
    ICON_LG = "24px"


# Global instances
colors = Colors()
typography = Typography()
spacing = Spacing()
radii = Radii()
sizes = Sizes()

