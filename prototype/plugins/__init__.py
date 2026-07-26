"""Plugin Framework — dynamic loading, hot reload, and dependency isolation."""

from .plugin_manager import PluginManager
from .base_plugin import BasePlugin, PluginManifest
from .ponytail_plugin import PonytailPlugin

__all__ = ["PluginManager", "BasePlugin", "PluginManifest", "PonytailPlugin"]