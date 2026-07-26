"""MLX provider — local Apple Silicon MLX models."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest,
    GenerateResponse,
    ModelCapabilities,
    ModelInfo,
    ModelModality,
    ModelProvider,
    ProviderType,
    StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.mlx")

try:
    import mlx_lm
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    mlx_lm = None


class MLXProvider(ModelProvider):
    """Provider for local MLX models on Apple Silicon."""

    provider_type = ProviderType.MLX
    display_name = "MLX (Apple Silicon)"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._model_paths: List[str] = self._config.get("model_paths", [])
        self._model_cache: Dict[str, tuple] = {}
        self._model_infos: Dict[str, ModelInfo] = {}
        self._loaded = False

    def load(self) -> None:
        if not MLX_AVAILABLE:
            logger.warning("mlx-lm not installed — provider unavailable")
            self._loaded = False
            return

        self._discover_models()
        self._loaded = True
        logger.info("MLX provider loaded: %d models", len(self._model_infos))

    def is_available(self) -> bool:
        return self._loaded and MLX_AVAILABLE

    def _discover_models(self) -> None:
        search_paths = self._model_paths or [
            str(Path.home() / ".cache" / "huggingface" / "hub"),
            str(Path.home() / "models"),
            "./models",
        ]

        for path_str in search_paths:
            path = Path(path_str)
            if not path.exists():
                continue

            for model_dir in path.iterdir():
                if not model_dir.is_dir():
                    continue
                if (model_dir / "config.json").exists():
                    self._register_model(model_dir)

    def _register_model(self, model_dir: Path) -> None:
        try:
            name = model_dir.name
            size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())

            with open(model_dir / "config.json") as f:
                config = json.load(f)

            family = config.get("model_type", "unknown").lower()
            arch = config.get("architectures", ["unknown"])[0]
            hidden_size = config.get("hidden_size", 0)
            num_layers = config.get("num_hidden_layers", 0)
            vocab_size = config.get("vocab_size", 0)

            caps = ModelCapabilities(
                max_context_length=config.get("max_position_embeddings", 4096),
                supports_streaming=True,
            )

            model_info = ModelInfo(
                id=f"mlx:{name}",
                name=name,
                provider=ProviderType.MLX,
                family=family,
                architecture=arch,
                modality=ModelModality.TEXT,
                capabilities=caps,
                tokenizer=config.get("tokenizer_class", "auto"),
                runtime="mlx",
                local=True,
                path=str(model_dir),
                size_bytes=size,
                parameter_count=self._estimate_params(hidden_size, num_layers, vocab_size),
                description=f"MLX model: {name}",
                metadata={"config": config},
            )
            self._model_infos[name] = model_info
        except Exception as exc:
            logger.debug("Failed to register MLX model %s: %s", model_dir, exc)

    def _load_model(self, model_id: str):
        name = model_id.replace("mlx:", "")
        if name in self._model_cache:
            return self._model_cache[name]

        info = self._model_infos.get(name)
        if not info or not info.path:
            return None

        try:
            model, tokenizer = mlx_lm.load(info.path)
            self._model_cache[name] = (model, tokenizer)
            return model, tokenizer
        except Exception as exc:
            logger.error("Failed to load MLX model %s: %s", name, exc)
            return None

    def list_models(self) -> List[ModelInfo]:
        if not self._loaded:
            self.load()
        return list(self._model_infos.values())

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        import time

        if not self.is_available():
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error="MLX not available",
            )

        model_name = request.model.replace("mlx:", "")
        loaded = self._load_model(model_name)
        if not loaded:
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=f"Model not found: {model_name}",
            )

        model, tokenizer = loaded
        start = time.time()

        try:
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            response = mlx_lm.generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=request.max_tokens,
                temp=request.temperature,
                top_p=request.top_p,
            )

            return GenerateResponse(
                content=response.strip(),
                model=request.model,
                provider=self.provider_type,
                finish_reason="stop",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as exc:
            logger.error("MLX generation failed: %s", exc)
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=str(exc),
                latency_ms=(time.time() - start) * 1000,
            )

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        model_name = request.model.replace("mlx:", "")
        loaded = self._load_model(model_name)
        if not loaded:
            yield StreamChunk(content=f"[Error] Model not found: {model_name}", finish_reason="error")
            return

        model, tokenizer = loaded

        try:
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            for token in mlx_lm.generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=request.max_tokens,
                temp=request.temperature,
                top_p=request.top_p,
                streaming=True,
            ):
                yield StreamChunk(content=token)
            yield StreamChunk(content="", finish_reason="stop")
        except Exception as exc:
            logger.warning("MLX streaming failed: %s", exc)
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._model_cache.clear()
        self._loaded = False

    def _estimate_params(self, hidden: int, layers: int, vocab: int) -> int:
        if hidden and layers:
            # Rough estimate: 12 * hidden^2 * layers + vocab * hidden
            return int(12 * hidden * hidden * layers + vocab * hidden)
        return 0