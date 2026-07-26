"""Plugin Manager — dynamic plugin loading, hot reload, and dependency isolation."""

import importlib
import importlib.util
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from prototype.common import Event, EventBus
from prototype.plugins.base_plugin import BasePlugin, PluginManifest

logger = logging.getLogger("alfa.plugins.manager")


class PluginManager:
    """Central plugin registry with hot load, hot unload, and dependency isolation.

    Features:
    - Register/unregister plugins
    - Hot load plugins from file paths at runtime
    - Hot unload with cleanup
    - Reload plugins without restart
    - Dependency tracking per plugin
    - Isolated plugin namespaces
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._loaded = False
        self._event_bus = event_bus
        self._plugins: Dict[str, BasePlugin] = {}
        self._enabled: Dict[str, bool] = {}
        self._modules: Dict[str, Any] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._load_order: List[str] = []
        self._watch_paths: List[str] = []
        self._lock = threading.RLock()

    def load(self) -> None:
        self._loaded = True
        logger.info("Plugin Manager loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, plugin: BasePlugin) -> bool:
        with self._lock:
            name = plugin.manifest.name
            if not name:
                logger.error("Plugin has no name — rejected")
                return False

            if name in self._plugins:
                logger.warning("Plugin '%s' already registered — hot reloading", name)
                self.unregister(name)

            try:
                plugin.on_load()
                self._plugins[name] = plugin
                self._enabled[name] = plugin.manifest.enabled
                self._load_order.append(name)
                self._track_dependencies(name, plugin)
                logger.info("Plugin registered: %s v%s", name, plugin.manifest.version)
                self._publish_event("PluginLoaded", {"name": name, "version": plugin.manifest.version})
                return True
            except Exception as exc:
                logger.exception("Failed to load plugin '%s': %s", name, exc)
                return False

    def unregister(self, name: str) -> bool:
        with self._lock:
            plugin = self._plugins.get(name)
            if not plugin:
                return False

            # Check dependents
            dependents = self._find_dependents(name)
            if dependents:
                logger.warning("Plugin '%s' has dependents: %s — unregistering them first", name, dependents)
                for dep in list(dependents):
                    self.unregister(dep)

            try:
                plugin.on_unload()
            except Exception as exc:
                logger.warning("Error unloading plugin '%s': %s", name, exc)

            del self._plugins[name]
            self._enabled.pop(name, None)
            self._dependencies.pop(name, None)
            self._unload_module(name)
            if name in self._load_order:
                self._load_order.remove(name)

            logger.info("Plugin unregistered: %s", name)
            self._publish_event("PluginUnloaded", {"name": name})
            return True

    # ── Hot Load from File ─────────────────────────────────────────────────

    def hot_load(self, file_path: str, class_name: Optional[str] = None) -> bool:
        """Hot load a plugin from a Python file at runtime."""
        path = Path(file_path)
        if not path.exists() or not path.suffix == ".py":
            logger.error("Invalid plugin file: %s", file_path)
            return False

        try:
            module_name = f"alfa_plugin_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, str(path))
            if not spec or not spec.loader:
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self._modules[module_name] = module

            # Find BasePlugin subclass
            plugin_class = None
            if class_name:
                plugin_class = getattr(module, class_name, None)
            else:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and issubclass(attr, BasePlugin)
                            and attr is not BasePlugin):
                        plugin_class = attr
                        break

            if not plugin_class:
                logger.error("No BasePlugin subclass found in %s", file_path)
                return False

            plugin_instance = plugin_class()
            return self.register(plugin_instance)

        except Exception as exc:
            logger.exception("Hot load failed for %s: %s", file_path, exc)
            return False

    def hot_unload(self, name: str) -> bool:
        """Hot unload a plugin and release its resources."""
        return self.unregister(name)

    def reload(self, name: str) -> bool:
        """Reload a plugin from its original source."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        manifest = plugin.manifest
        entry = manifest.entry
        if not entry:
            logger.error("Plugin '%s' has no entry point", name)
            return False

        self.unregister(name)
        return self.hot_load(entry)

    # ── Watch Directory ────────────────────────────────────────────────────

    def add_watch_path(self, path: str) -> None:
        if path not in self._watch_paths:
            self._watch_paths.append(path)

    def scan_and_load(self) -> int:
        """Scan watch paths for plugin files and load them."""
        loaded = 0
        for watch_path in self._watch_paths:
            p = Path(watch_path)
            if not p.exists():
                continue
            for py_file in p.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                module_name = py_file.stem
                if not any(module_name in str(entry) for entry in
                           [getattr(pl, "manifest", None) and pl.manifest.entry or "" for pl in self._plugins.values()]):
                    if self.hot_load(str(py_file)):
                        loaded += 1
        return loaded

    # ── Enable / Disable ──────────────────────────────────────────────────

    def enable(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        self._enabled[name] = True
        try:
            plugin.on_enable()
        except Exception as exc:
            logger.warning("Error enabling plugin '%s': %s", name, exc)
        self._publish_event("PluginEnabled", {"name": name})
        return True

    def disable(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if not plugin:
            return False
        self._enabled[name] = False
        try:
            plugin.on_disable()
        except Exception as exc:
            logger.warning("Error disabling plugin '%s': %s", name, exc)
        self._publish_event("PluginDisabled", {"name": name})
        return True

    def is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, False)

    # ── Dependency Tracking ────────────────────────────────────────────────

    def _track_dependencies(self, name: str, plugin: BasePlugin) -> None:
        deps = set()
        manifest = plugin.manifest
        if hasattr(manifest, "dependencies"):
            deps = set(getattr(manifest, "dependencies", []))
        self._dependencies[name] = deps

    def _find_dependents(self, name: str) -> Set[str]:
        dependents = set()
        for plugin_name, deps in self._dependencies.items():
            if name in deps:
                dependents.add(plugin_name)
        return dependents

    def check_dependencies(self, name: str) -> List[str]:
        """Check if a plugin's dependencies are satisfied."""
        deps = self._dependencies.get(name, set())
        missing = []
        for dep in deps:
            if dep not in self._plugins:
                missing.append(dep)
        return missing

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        return {name: list(deps) for name, deps in self._dependencies.items()}

    def _unload_module(self, name: str) -> None:
        to_remove = [k for k in self._modules if k.endswith(name)]
        for key in to_remove:
            sys.modules.pop(key, None)
            del self._modules[key]

    # ── Query ─────────────────────────────────────────────────────────────

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        result = []
        for name, plugin in self._plugins.items():
            manifest = plugin.manifest
            result.append({
                "name": manifest.name,
                "version": manifest.version,
                "author": manifest.author,
                "description": manifest.description,
                "enabled": self._enabled.get(name, False),
                "healthy": plugin.health(),
                "capabilities": manifest.capabilities,
                "permissions": manifest.permissions,
                "dependencies": list(self._dependencies.get(name, set())),
            })
        return result

    def get_plugin_names(self) -> List[str]:
        return list(self._plugins.keys())

    def get_load_order(self) -> List[str]:
        return self._load_order.copy()

    def get_plugin_tools(self) -> list:
        tools = []
        for name, plugin in self._plugins.items():
            if self._enabled.get(name, False):
                tools.extend(plugin.get_tools())
        return tools

    # ── Events ─────────────────────────────────────────────────────────────

    def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type=event_type, payload=payload, source="plugin_manager",
            ))

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        for name in list(self._plugins.keys()):
            self.unregister(name)
        self._watch_paths.clear()
        self._loaded = False
        logger.info("Plugin Manager shutdown")