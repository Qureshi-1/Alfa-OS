"""Config package for Alfa COS — single source of truth."""

from prototype.config.settings import (
    SettingsManager,
    get_settings_manager,
    reset_settings_manager,
    DEFAULT_CONFIG,
    VALID_PROVIDERS,
)

__all__ = [
    "SettingsManager",
    "get_settings_manager",
    "reset_settings_manager",
    "DEFAULT_CONFIG",
    "VALID_PROVIDERS",
]