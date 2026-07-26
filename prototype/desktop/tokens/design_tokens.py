"""Design Tokens — single source of truth for all ALFA COS visual values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    """Color palette — Cyber Blue dark glass theme."""
    # Backgrounds
    BG_PRIMARY = "#0a0e17"
    BG_SECONDARY = "#111827"
    BG_TERTIARY = "#1a2236"
    BG_SURFACE = "#1e293b"
    BG_ELEVATED = "#243049"
    BG_HOVER = "#2a3a52"
    BG_ACTIVE = "#334766"
    BG_INPUT = "#0f172a"

    # Glass
    GLASS_BG = "rgba(14, 22, 40, 0.85)"
    GLASS_BORDER = "rgba(56, 128, 255, 0.12)"
    GLASS_HOVER = "rgba(56, 128, 255, 0.08)"

    # Accent
    ACCENT_PRIMARY = "#3b82f6"
    ACCENT_SECONDARY = "#60a5fa"
    ACCENT_TERTIARY = "#2563eb"
    ACCENT_GLOW = "rgba(59, 130, 246, 0.25)"
    ACCENT_SUBTLE = "rgba(59, 130, 246, 0.10)"

    # Text
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    TEXT_ACCENT = "#60a5fa"
    TEXT_DANGER = "#f87171"
    TEXT_SUCCESS = "#34d399"
    TEXT_WARNING = "#fbbf24"

    # Semantic
    DANGER = "#ef4444"
    DANGER_BG = "rgba(239, 68, 68, 0.12)"
    SUCCESS = "#22c55e"
    SUCCESS_BG = "rgba(34, 197, 94, 0.12)"
    WARNING = "#f59e0b"
    WARNING_BG = "rgba(245, 158, 11, 0.12)"
    INFO = "#3b82f6"
    INFO_BG = "rgba(59, 130, 246, 0.12)"

    # Borders
    BORDER_PRIMARY = "rgba(56, 128, 255, 0.15)"
    BORDER_SECONDARY = "rgba(148, 163, 184, 0.10)"
    BORDER_FOCUS = "rgba(59, 130, 246, 0.50)"

    # Shadows
    SHADOW_SM = "0 1px 2px rgba(0, 0, 0, 0.3)"
    SHADOW_MD = "0 4px 12px rgba(0, 0, 0, 0.4)"
    SHADOW_LG = "0 8px 32px rgba(0, 0, 0, 0.5)"


@dataclass(frozen=True)
class Typography:
    """Font families and sizes."""
    FONT_FAMILY = "'Segoe UI', 'SF Pro Display', -apple-system, sans-serif"
    FONT_MONO = "'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace"

    # Sizes
    SIZE_XS = "10px"
    SIZE_SM = "11px"
    SIZE_MD = "12px"
    SIZE_BASE = "13px"
    SIZE_LG = "14px"
    SIZE_XL = "16px"
    SIZE_2XL = "20px"
    SIZE_3XL = "28px"

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
    """Border radii."""
    SM = "4px"
    MD = "6px"
    LG = "8px"
    XL = "12px"
    FULL = "9999px"


@dataclass(frozen=True)
class Sizes:
    """Component sizes."""
    SIDEBAR_WIDTH = "52px"
    SIDEBAR_EXPANDED = "200px"
    STATUS_BAR_HEIGHT = "28px"
    TOP_BAR_HEIGHT = "40px"
    INPUT_HEIGHT = "32px"
    BUTTON_HEIGHT = "28px"
    ICON_SM = "14px"
    ICON_MD = "18px"
    ICON_LG = "24px"


# Global instances
colors = Colors()
typography = Typography()
spacing = Spacing()
radii = Radii()
sizes = Sizes()
