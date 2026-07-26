"""HuggingFace provider — local transformers inference."""

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

logger = logging.getLogger("alfa.modelhub.huggingface")

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class HuggingFaceProvider(ModelProvider):
    """Provider for local HuggingFace transformers models."""

    provider_type = ProviderType.HUGGINGFACE
    display_name = "HuggingFace Transformers"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._model_paths: List[str] = self._config.get("model_paths", [])
        self._pipelines: Dict[str, Any] = {}
        self._model_infos: Dict[str, ModelInfo] = {}
        self._device = self._config.get("device", "auto")
        self._dtype = self._config.get("dtype", "auto")
        self._loaded = False

    def load(self) -> None:
        if not HF_AVAILABLE:
            logger.warning("transformers/torch not installed — provider unavailable")
            self._loaded = False
            return

        self._discover_models()
        self._loaded = True
        logger.info("HuggingFace provider loaded: %d models", len(self._model_infos))

    def is_available(self) -> bool:
        return self._loaded and HF_AVAILABLE

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

            model_type = config.get("model_type", "unknown")
            arch = config.get("architectures", ["unknown"])[0]
            hidden = config.get("hidden_size", 0)
            layers = config.get("num_hidden_layers", 0)
            vocab = config.get("vocab_size", 0)
            max_pos = config.get("max_position_embeddings", 4096)

            caps = ModelCapabilities(
                max_context_length=max_pos,
                supports_streaming=False,  # transformers pipeline doesn't stream easily
            )

            model_info = ModelInfo(
                id=f"hf:{name}",
                name=name,
                provider=ProviderType.HUGGINGFACE,
                family=model_type,
                architecture=arch,
                modality=ModelModality.TEXT,
                capabilities=caps,
                tokenizer=config.get("tokenizer_class", "auto"),
                runtime="transformers",
                local=True,
                path=str(model_dir),
                size_bytes=size,
                parameter_count=self._estimate_params(hidden, layers, vocab),
                description=f"HF model: {name}",
                metadata={"config": config},
            )
            self._model_infos[name] = model_info
        except Exception as exc:
            logger.debug("Failed to register HF model %s: %s", model_dir, exc)

    def _get_or_load_pipeline(self, model_id: str):
        name = model_id.replace("hf:", "")
        if name in self._pipelines:
            return self._pipelines[name]

        info = self._model_infos.get(name)
        if not info or not info.path:
            return None

        try:
            tokenizer = AutoTokenizer.from_pretrained(info.path, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                info.path,
                torch_dtype="auto" if self._dtype == "auto" else getattr(torch, self._dtype),
                device_map=self._device,
                trust_remote_code=True,
            )
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device_map=self._device,
            )
            self._pipelines[name] = pipe
            return pipe
        except Exception as exc:
            logger.error("Failed to load HF model %s: %s", name, exc)
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
                error="HuggingFace not available",
            )

        model_name = request.model.replace("hf:", "")
        pipe = self._get_or_load_pipeline(model_name)
        if not pipe:
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=f"Model not found: {model_name}",
            )

        start = time.time()
        try:
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            outputs = pipe(
                prompt,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                return_full_text=False,
            )
            content = outputs[0]["generated_text"]

            return GenerateResponse(
                content=content.strip(),
                model=request.model,
                provider=self.provider_type,
                finish_reason="stop",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as exc:
            logger.error("HF generation failed: %s", exc)
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=str(exc),
                latency_ms=(time.time() - start) * 1000,
            )

    def shutdown(self) -> None:
        for pipe in self._pipelines.values():
            try:
                del pipe
            except Exception:
                pass
        self._pipelines.clear()
        self._loaded = False

    def _estimate_params(self, hidden: int, layers: int, vocab: int) -> int:
        if hidden and layers:
            return int(12 * hidden * hidden * layers + vocab * hidden)
        return 0