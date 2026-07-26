"""Model Registry — automatic model discovery, registration, and management."""

import json
import logging
import os
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from prototype.common import Event, EventBus, get_event_bus
from prototype.modelhub.base import (
    ModelCapabilities,
    ModelInfo,
    ModelModality,
    ModelProvider,
    ProviderType,
)

logger = logging.getLogger("alfa.modelhub.registry")


class ModelRegistry:
    """Central registry for all discovered models across all providers.

    Features:
    - Automatic model detection from provider configs
    - Local model file scanning (GGUF, safetensors, etc.)
    - Model capability inference from metadata
    - Persistent registry storage
    - Event-driven updates
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or get_event_bus()
        self._models: Dict[str, ModelInfo] = {}
        self._providers: Dict[ProviderType, ModelProvider] = {}
        self._provider_configs: Dict[ProviderType, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._loaded = False
        self._scan_paths: List[str] = []
        self._discovery_hooks: List[Callable[[ModelProvider], List[ModelInfo]]] = []

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load(self) -> None:
        """Initialize the registry."""
        with self._lock:
            if self._loaded:
                return
            self._load_persisted_registry()
            self._loaded = True
            logger.info("Model Registry loaded: %d models", len(self._models))

    def shutdown(self) -> None:
        """Shutdown and persist registry."""
        with self._lock:
            self._persist_registry()
            self._models.clear()
            self._providers.clear()
            self._loaded = False
            logger.info("Model Registry shutdown")

    # ── Provider Management ────────────────────────────────────────────────

    def register_provider(self, provider: ModelProvider) -> None:
        """Register a provider and trigger model discovery."""
        with self._lock:
            ptype = provider.provider_type
            if ptype in self._providers:
                logger.warning("Provider %s already registered, replacing", ptype.value)
            self._providers[ptype] = provider
            logger.info("Registered provider: %s", ptype.value)

            # Load provider and discover models
            try:
                provider.load()
                self._discover_models_from_provider(provider)
            except Exception as exc:
                logger.error("Failed to load provider %s: %s", ptype.value, exc)

    def unregister_provider(self, provider_type: ProviderType) -> bool:
        """Unregister a provider and its models."""
        with self._lock:
            provider = self._providers.pop(provider_type, None)
            if not provider:
                return False

            # Remove models from this provider
            to_remove = [
                mid for mid, m in self._models.items()
                if m.provider == provider_type
            ]
            for mid in to_remove:
                self._remove_model(mid, provider_type)

            provider.shutdown()
            logger.info("Unregistered provider: %s", provider_type.value)
            return True

    def get_provider(self, provider_type: ProviderType) -> Optional[ModelProvider]:
        return self._providers.get(provider_type)

    def list_providers(self) -> List[ProviderType]:
        return list(self._providers.keys())

    # ── Model Discovery ────────────────────────────────────────────────────

    def _discover_models_from_provider(self, provider: ModelProvider) -> None:
        """Discover and register models from a provider."""
        try:
            models = provider.list_models()
            for model in models:
                self._register_model(model)

            # Run custom discovery hooks
            for hook in self._discovery_hooks:
                try:
                    extra_models = hook(provider)
                    for model in extra_models:
                        self._register_model(model)
                except Exception as exc:
                    logger.warning("Discovery hook failed: %s", exc)

            self._publish_event("ModelsDiscovered", {
                "provider": provider.provider_type.value,
                "count": len(models),
            })
        except Exception as exc:
            logger.error("Model discovery failed for %s: %s", provider.provider_type.value, exc)

    def register_discovery_hook(self, hook: Callable[[ModelProvider], List[ModelInfo]]) -> None:
        """Register a custom model discovery hook."""
        self._discovery_hooks.append(hook)

    def scan_local_models(self, paths: Optional[List[str]] = None) -> List[ModelInfo]:
        """Scan local filesystem for model files (GGUF, safetensors, etc.)."""
        scan_paths = paths or self._scan_paths
        discovered: List[ModelInfo] = []

        for path_str in scan_paths:
            path = Path(path_str).expanduser()
            if not path.exists():
                continue

            for model_file in path.rglob("*"):
                if not model_file.is_file():
                    continue

                model_info = self._infer_model_from_file(model_file)
                if model_info:
                    self._register_model(model_info)
                    discovered.append(model_info)

        logger.info("Local scan found %d models in %d paths", len(discovered), len(scan_paths))
        return discovered

    def add_scan_path(self, path: str) -> None:
        """Add a path to scan for local models."""
        if path not in self._scan_paths:
            self._scan_paths.append(path)

    def _infer_model_from_file(self, file_path: Path) -> Optional[ModelInfo]:
        """Infer model metadata from a local model file."""
        suffix = file_path.suffix.lower()
        stem = file_path.stem

        if suffix == ".gguf":
            return self._infer_gguf_model(file_path, stem)
        elif suffix in {".safetensors", ".bin", ".pt", ".pth"}:
            return self._infer_hf_model(file_path, stem)
        elif suffix == ".mlx":
            return self._infer_mlx_model(file_path, stem)
        return None

    def _infer_gguf_model(self, path: Path, name: str) -> Optional[ModelInfo]:
        """Parse GGUF metadata for model info."""
        try:
            import gguf
            reader = gguf.GGUFReader(str(path))
            metadata = {k: v for k, v in reader.get_all_metadata().items()}

            # Extract known fields
            family = metadata.get("general.architecture", "").lower()
            param_count = metadata.get("general.parameter_count", 0)
            quantization = metadata.get("general.quantization_version", "")
            file_size = path.stat().st_size

            caps = ModelCapabilities(
                max_context_length=metadata.get("llama.context_length", 4096),
            )

            return ModelInfo(
                id=f"gguf:{name}",
                name=name,
                provider=ProviderType.LLAMA_CPP,
                family=family,
                architecture=family,
                modality=ModelModality.TEXT,
                capabilities=caps,
                tokenizer="llama",
                runtime="llama.cpp",
                local=True,
                path=str(path),
                size_bytes=file_size,
                quantization=quantization,
                parameter_count=param_count,
                metadata=metadata,
            )
        except ImportError:
            logger.debug("gguf library not available, using basic inference")
        except Exception as exc:
            logger.warning("Failed to parse GGUF %s: %s", path, exc)

        # Fallback basic inference
        return ModelInfo(
            id=f"gguf:{name}",
            name=name,
            provider=ProviderType.LLAMA_CPP,
            family=self._guess_family(name),
            architecture="llama",
            modality=ModelModality.TEXT,
            capabilities=ModelCapabilities(),
            tokenizer="llama",
            runtime="llama.cpp",
            local=True,
            path=str(path),
            size_bytes=path.stat().st_size,
            metadata={"source": "file_inference"},
        )

    def _infer_hf_model(self, path: Path, name: str) -> Optional[ModelInfo]:
        """Infer info from HuggingFace format model files."""
        return ModelInfo(
            id=f"hf:{name}",
            name=name,
            provider=ProviderType.HUGGINGFACE,
            family=self._guess_family(name),
            architecture="transformer",
            modality=ModelModality.TEXT,
            capabilities=ModelCapabilities(),
            tokenizer="auto",
            runtime="huggingface",
            local=True,
            path=str(path),
            size_bytes=path.stat().st_size,
            metadata={"source": "file_inference"},
        )

    def _infer_mlx_model(self, path: Path, name: str) -> Optional[ModelInfo]:
        """Infer info from MLX format model files."""
        return ModelInfo(
            id=f"mlx:{name}",
            name=name,
            provider=ProviderType.MLX,
            family=self._guess_family(name),
            architecture="mlx",
            modality=ModelModality.TEXT,
            capabilities=ModelCapabilities(),
            tokenizer="auto",
            runtime="mlx",
            local=True,
            path=str(path),
            size_bytes=path.stat().st_size,
            metadata={"source": "file_inference"},
        )

    def _guess_family(self, name: str) -> str:
        """Guess model family from name."""
        name_lower = name.lower()
        families = {
            "llama": ["llama", "alpaca", "vicuna", "guanaco", "wizard"],
            "mistral": ["mistral", "mixtral", "mistralite"],
            "qwen": ["qwen"],
            "gemma": ["gemma"],
            "phi": ["phi"],
            "falcon": ["falcon"],
            "mpt": ["mpt"],
            "gpt": ["gpt", "gpt2", "gpt-j", "gpt-neox"],
            "bloom": ["bloom"],
            "baichuan": ["baichuan"],
            "yi": ["yi-"],
            "deepseek": ["deepseek"],
            "starcoder": ["starcoder", "codegen", "code-llama"],
        }
        for family, keywords in families.items():
            if any(k in name_lower for k in keywords):
                return family
        return "unknown"

    # ── Model Registration ─────────────────────────────────────────────────

    def _register_model(self, model: ModelInfo) -> bool:
        """Register a model, returns True if new or updated."""
        with self._lock:
            existing = self._models.get(model.id)
            if existing and existing.last_used and model.last_used:
                if existing.last_used >= model.last_used:
                    return False  # Existing is newer

            is_new = model.id not in self._models
            self._models[model.id] = model

            if is_new:
                logger.info("Discovered new model: %s (%s)", model.id, model.provider.value)
                self._publish_event("ModelDiscovered", model.to_dict())
            else:
                logger.debug("Updated model: %s", model.id)
                self._publish_event("ModelUpdated", model.to_dict())

            return True

    def _remove_model(self, model_id: str, provider: ProviderType) -> bool:
        """Remove a model from registry."""
        with self._lock:
            model = self._models.pop(model_id, None)
            if model:
                logger.info("Removed model: %s", model_id)
                self._publish_event("ModelRemoved", {"model_id": model_id, "provider": provider.value})
                return True
            return False

    # ── Query ──────────────────────────────────────────────────────────────

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        with self._lock:
            return self._models.get(model_id)

    def list_models(
        self,
        provider: Optional[ProviderType] = None,
        local_only: bool = False,
        modality: Optional[ModelModality] = None,
        family: Optional[str] = None,
    ) -> List[ModelInfo]:
        with self._lock:
            models = list(self._models.values())
            if provider:
                models = [m for m in models if m.provider == provider]
            if local_only:
                models = [m for m in models if m.local]
            if modality:
                models = [m for m in models if m.modality == modality]
            if family:
                models = [m for m in models if m.family.lower() == family.lower()]
            return models

    def get_models_by_capability(self, capability: str) -> List[ModelInfo]:
        """Find models supporting a specific capability."""
        with self._lock:
            return [
                m for m in self._models.values()
                if getattr(m.capabilities, capability, False)
            ]

    def search_models(self, query: str) -> List[ModelInfo]:
        """Search models by name, family, or description."""
        query = query.lower()
        with self._lock:
            return [
                m for m in self._models.values()
                if query in m.name.lower()
                or query in m.family.lower()
                or query in m.description.lower()
                or query in m.id.lower()
            ]

    # ── Usage Tracking ─────────────────────────────────────────────────────

    def record_usage(self, model_id: str) -> None:
        """Record model usage for ranking/recency."""
        with self._lock:
            model = self._models.get(model_id)
            if model:
                model.last_used = datetime.now()
                model.usage_count += 1

    def get_recently_used(self, limit: int = 10) -> List[ModelInfo]:
        with self._lock:
            used = [m for m in self._models.values() if m.last_used]
            used.sort(key=lambda m: m.last_used, reverse=True)
            return used[:limit]

    def get_most_used(self, limit: int = 10) -> List[ModelInfo]:
        with self._lock:
            used = list(self._models.values())
            used.sort(key=lambda m: m.usage_count, reverse=True)
            return used[:limit]

    # ── Persistence ────────────────────────────────────────────────────────

    def _get_registry_path(self) -> Path:
        base = Path(__file__).parent.parent.parent / "data"
        base.mkdir(parents=True, exist_ok=True)
        return base / "model_registry.json"

    def _persist_registry(self) -> None:
        try:
            path = self._get_registry_path()
            data = {
                "models": {mid: m.to_dict() for mid, m in self._models.items()},
                "scan_paths": self._scan_paths,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug("Persisted registry: %d models", len(self._models))
        except Exception as exc:
            logger.warning("Failed to persist registry: %s", exc)

    def _load_persisted_registry(self) -> None:
        try:
            path = self._get_registry_path()
            if not path.exists():
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for mid, mdata in data.get("models", {}).items():
                try:
                    model = ModelInfo.from_dict(mdata)
                    self._models[mid] = model
                except Exception as exc:
                    logger.warning("Failed to load model %s: %s", mid, exc)
            self._scan_paths = data.get("scan_paths", [])
            logger.info("Loaded persisted registry: %d models", len(self._models))
        except Exception as exc:
            logger.warning("Failed to load persisted registry: %s", exc)

    # ── Events ─────────────────────────────────────────────────────────────

    def _publish_event(self, event_type: str, payload: Any) -> None:
        try:
            self._event_bus.publish(Event(
                event_type=event_type,
                payload=payload,
                source="model_registry",
            ))
        except Exception as exc:
            logger.debug("Event publish failed: %s", exc)

    # ── Stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            by_provider: Dict[str, int] = {}
            by_family: Dict[str, int] = {}
            local_count = 0
            cloud_count = 0

            for m in self._models.values():
                by_provider[m.provider.value] = by_provider.get(m.provider.value, 0) + 1
                by_family[m.family] = by_family.get(m.family, 0) + 1
                if m.local:
                    local_count += 1
                else:
                    cloud_count += 1

            return {
                "total_models": len(self._models),
                "by_provider": by_provider,
                "by_family": by_family,
                "local_models": local_count,
                "cloud_models": cloud_count,
                "registered_providers": [p.value for p in self._providers.keys()],
            }


# ── Singleton ───────────────────────────────────────────────────────────────

_model_registry_instance: Optional[ModelRegistry] = None
_registry_lock = threading.Lock()


def get_model_registry(event_bus: Optional[EventBus] = None) -> ModelRegistry:
    """Get the global ModelRegistry instance."""
    global _model_registry_instance
    with _registry_lock:
        if _model_registry_instance is None:
            _model_registry_instance = ModelRegistry(event_bus)
        return _model_registry_instance


def reset_model_registry() -> None:
    """Reset the singleton (for testing)."""
    global _model_registry_instance
    with _registry_lock:
        if _model_registry_instance:
            _model_registry_instance.shutdown()
        _model_registry_instance = None