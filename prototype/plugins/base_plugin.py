"""Base Plugin interface — all plugins implement this contract."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("alfa.plugins")


@dataclass
class PluginManifest:
    """Plugin metadata descriptor."""
    name: str = ""
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    entry: str = ""
    permissions: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """Abstract base class for all Alfa COS plugins.

    Every plugin must provide:
    - manifest: Plugin metadata
    - on_load(): Called when the plugin is loaded
    - on_unload(): Called when the plugin is unloaded
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""

    @abstractmethod
    def on_load(self) -> None:
        """Called when the plugin is loaded into the runtime."""

    @abstractmethod
    def on_unload(self) -> None:
        """Called when the plugin is unloaded from the runtime."""

    def on_enable(self) -> None:
        """Called when the plugin is enabled. Override if needed."""

    def on_disable(self) -> None:
        """Called when the plugin is disabled. Override if needed."""

    def health(self) -> bool:
        """Check if the plugin is healthy. Override if needed."""
        return True

    def get_tools(self) -> list:
        """Return tools provided by this plugin. Override if needed."""
        return []
