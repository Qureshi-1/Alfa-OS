"""
Alfa COS Settings Manager — single source of truth for all configuration.

Settings are stored in config.json inside the application directory.
No Windows environment variables are required. On first run, if environment
variables exist they are migrated once, then the config file is the sole
authority.

API keys are never logged. All display uses masking.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("alfa.config")

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "mock",
    "model": "z-ai/glm-5.2",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 30,
    "api_key": "",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "openrouter_model": "qwen/qwen3-32b",
    "openrouter_api_key": "",
    "openrouter_base_url": "https://openrouter.ai/api/v1/chat/completions",
    "max_retries": 3,
    "retry_delay": 1.0,
}

VALID_PROVIDERS = ("mock", "nvidia", "openrouter")

# Keys that contain secrets — never log their values.
_SECRET_KEYS = frozenset({"api_key", "openrouter_api_key"})

# ── Singleton accessor ───────────────────────────────────────────────────────

_settings_manager_instance: Optional["SettingsManager"] = None


class SettingsManager:
    """Manages application settings with persistence to config.json.

    Thread-safe for reads. Writes serialise through ``save()``.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = config_path or self._default_config_path()
        self._config: Dict[str, Any] = {}
        self._loaded = False

    # ── Path helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _default_config_path() -> str:
        """Return path to ``prototype/config/config.json``."""
        return str(Path(__file__).parent / "config.json")

    # ── Load / save ───────────────────────────────────────────────────────

    def load(self) -> None:
        """Load configuration from config.json, with env-var migration."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as fh:
                    self._config = json.load(fh)
            except (json.JSONDecodeError, IOError):
                logger.warning("Corrupt config.json — resetting to defaults")
                self._config = {}
        else:
            self._config = {}
            self._migrate_from_env()

        # Backfill any missing keys from defaults.
        for key, default in DEFAULT_CONFIG.items():
            self._config.setdefault(key, default)

        self._loaded = True
        self.save()

    def _migrate_from_env(self) -> None:
        """One-time migration from environment variables."""
        env_map = {
            "provider": "ALFA_PROVIDER",
            "model": "ALFA_MODEL",
            "temperature": "ALFA_TEMPERATURE",
            "max_tokens": "ALFA_MAX_TOKENS",
            "timeout": "ALFA_REQUEST_TIMEOUT",
            "api_key": "ALFA_NVIDIA_API_KEY",
            "base_url": "ALFA_NVIDIA_BASE_URL",
            "openrouter_model": "ALFA_OPENROUTER_MODEL",
            "openrouter_api_key": "ALFA_OPENROUTER_API_KEY",
            "openrouter_base_url": "ALFA_OPENROUTER_BASE_URL",
            "max_retries": "ALFA_MAX_RETRIES",
            "retry_delay": "ALFA_RETRY_DELAY",
        }
        migrated = False
        for key, env_key in env_map.items():
            env_val = os.environ.get(env_key, "")
            if not env_val:
                continue
            default = DEFAULT_CONFIG.get(key)
            if isinstance(default, (int, float)):
                try:
                    self._config[key] = type(default)(env_val)
                except (ValueError, TypeError):
                    pass
            else:
                self._config[key] = env_val
            migrated = True
        if migrated:
            logger.info("Migrated configuration from environment variables")

    def save(self) -> None:
        """Persist current config to disk."""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as fh:
                json.dump(self._config, fh, indent=4)
        except IOError as exc:
            logger.error("Failed to save config: %s", exc)

    # ── Generic accessors ─────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
        self.save()

    # ── Provider helpers ──────────────────────────────────────────────────

    def get_provider(self) -> str:
        return self._config.get("provider", "mock")

    def set_provider(self, provider: str) -> None:
        if provider in VALID_PROVIDERS:
            self.set("provider", provider)
        else:
            raise ValueError(
                f"Unknown provider '{provider}'. Valid: {', '.join(VALID_PROVIDERS)}"
            )

    def get_model(self) -> str:
        if self.get_provider() == "openrouter":
            return self._config.get("openrouter_model", "qwen/qwen3-32b")
        return self._config.get("model", "z-ai/glm-5.2")

    def set_model(self, model: str) -> None:
        if self.get_provider() == "openrouter":
            self.set("openrouter_model", model)
        else:
            self.set("model", model)

    def get_api_key(self) -> str:
        """Return the API key for the active provider."""
        provider = self.get_provider()
        if provider == "openrouter":
            return self._config.get("openrouter_api_key", "")
        return self._config.get("api_key", "")

    def set_api_key(self, key: str) -> None:
        """Set the API key for the active provider."""
        provider = self.get_provider()
        if provider == "openrouter":
            self.set("openrouter_api_key", key)
        else:
            self.set("api_key", key)

    def get_provider_config(self) -> Dict[str, Any]:
        """Build a flat config dict for the current provider."""
        provider = self.get_provider()
        cfg: Dict[str, Any] = {
            "provider": provider,
            "model": self.get_model(),
            "temperature": self._config.get("temperature", 0.7),
            "max_tokens": self._config.get("max_tokens", 4096),
            "timeout": self._config.get("timeout", 30),
            "max_retries": self._config.get("max_retries", 3),
            "retry_delay": self._config.get("retry_delay", 1.0),
        }
        if provider == "nvidia":
            cfg["api_key"] = self._config.get("api_key", "")
            cfg["base_url"] = self._config.get(
                "base_url", "https://integrate.api.nvidia.com/v1"
            )
        elif provider == "openrouter":
            cfg["api_key"] = self._config.get("openrouter_api_key", "")
            cfg["base_url"] = self._config.get(
                "openrouter_base_url",
                "https://openrouter.ai/api/v1/chat/completions",
            )
        return cfg

    # ── Display / safety ──────────────────────────────────────────────────

    @staticmethod
    def mask_secret(value: str) -> str:
        """Return a masked representation of a secret string."""
        if not value:
            return "(not set)"
        if len(value) <= 4:
            return "***"
        return "***" + value[-4:]

    def get_all(self) -> Dict[str, Any]:
        """Return all settings with API keys masked."""
        safe = self._config.copy()
        for key in _SECRET_KEYS:
            if safe.get(key):
                safe[key] = self.mask_secret(safe[key])
        return safe

    # ── Connection test ───────────────────────────────────────────────────

    def test_connection(self) -> Dict[str, Any]:
        """Test connectivity with the current provider."""
        provider_name = self.get_provider()
        start = time.time()
        try:
            if provider_name == "mock":
                return {
                    "connected": True,
                    "latency_ms": 0.0,
                    "error": None,
                    "provider": "mock",
                    "message": "Mock provider always available",
                }
            elif provider_name == "nvidia":
                return self._test_nvidia(start)
            elif provider_name == "openrouter":
                return self._test_openrouter(start)
            else:
                return {
                    "connected": False,
                    "latency_ms": 0.0,
                    "error": f"Unknown provider: {provider_name}",
                    "provider": provider_name,
                }
        except Exception as exc:
            return {
                "connected": False,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "error": str(exc),
                "provider": provider_name,
                "message": "Connection test failed",
            }

    def _test_nvidia(self, start: float) -> Dict[str, Any]:
        api_key = self._config.get("api_key", "")
        if not api_key:
            return {
                "connected": False,
                "latency_ms": 0.0,
                "error": "NVIDIA API key not configured",
                "provider": "nvidia",
                "message": "Set API key via: apikey <key>",
            }
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=self._config.get(
                    "base_url", "https://integrate.api.nvidia.com/v1"
                ),
                api_key=api_key,
            )
            client.chat.completions.create(
                model=self.get_model(),
                messages=[{"role": "user", "content": "OK"}],
                max_tokens=1,
                timeout=10.0,
            )
            return {
                "connected": True,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "error": None,
                "provider": "nvidia",
                "message": "NVIDIA API connection successful",
            }
        except Exception as exc:
            return {
                "connected": False,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "error": str(exc),
                "provider": "nvidia",
                "message": "NVIDIA API connection failed",
            }

    def _test_openrouter(self, start: float) -> Dict[str, Any]:
        import urllib.request

        api_key = self._config.get("openrouter_api_key", "")
        if not api_key:
            return {
                "connected": False,
                "latency_ms": 0.0,
                "error": "OpenRouter API key not configured",
                "provider": "openrouter",
                "message": "Set API key via: apikey <key>",
            }
        try:
            payload = json.dumps(
                {
                    "model": self.get_model(),
                    "messages": [{"role": "user", "content": "OK"}],
                    "max_tokens": 1,
                    "stream": False,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                self._config.get(
                    "openrouter_base_url",
                    "https://openrouter.ai/api/v1/chat/completions",
                ),
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com/alfa-cos",
                    "X-Title": "Alfa COS",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                latency = round((time.time() - start) * 1000, 2)
                if resp.status == 200:
                    return {
                        "connected": True,
                        "latency_ms": latency,
                        "error": None,
                        "provider": "openrouter",
                        "message": "OpenRouter connection successful",
                    }
                return {
                    "connected": False,
                    "latency_ms": latency,
                    "error": f"HTTP {resp.status}",
                    "provider": "openrouter",
                    "message": "OpenRouter connection failed",
                }
        except Exception as exc:
            return {
                "connected": False,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "error": str(exc),
                "provider": "openrouter",
                "message": "OpenRouter connection failed",
            }


# ── Singleton ─────────────────────────────────────────────────────────────────


def get_settings_manager(config_path: Optional[str] = None) -> SettingsManager:
    """Return (and lazily create) the global SettingsManager."""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager(config_path)
        _settings_manager_instance.load()
    return _settings_manager_instance


def reset_settings_manager() -> None:
    """Reset the singleton — used by tests."""
    global _settings_manager_instance
    _settings_manager_instance = None