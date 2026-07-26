"""llama.cpp provider — local GGUF model inference via llama-cpp-python."""

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

logger = logging.getLogger("alfa.modelhub.llama_cpp")

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None


class LlamaCppProvider(ModelProvider):
    """Provider for local GGUF models via llama-cpp-python."""

    provider_type = ProviderType.LLAMA_CPP
    display_name = "llama.cpp"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._model_paths: List[str] = self._config.get("model_paths", [])
        self._models: Dict[str, Llama] = {}
        self._model_infos: Dict[str, ModelInfo] = {}
        self._default_n_ctx = self._config.get("n_ctx", 4096)
        self._default_n_gpu_layers = self._config.get("n_gpu_layers", -1)
        self._loaded = False

    def load(self) -> None:
        if not LLAMA_CPP_AVAILABLE:
            logger.warning("llama-cpp-python not installed — provider unavailable")
            self._loaded = False
            return

        self._discover_models()
        self._loaded = True
        logger.info("llama.cpp provider loaded: %d models", len(self._model_infos))

    def is_available(self) -> bool:
        return self._loaded and LLAMA_CPP_AVAILABLE

    def _discover_models(self) -> None:
        search_paths = self._model_paths or [
            str(Path.home() / ".cache" / "llama.cpp"),
            str(Path.home() / "models"),
            "/models",
            "./models",
        ]

        for path_str in search_paths:
            path = Path(path_str)
            if not path.exists():
                continue

            for model_file in path.rglob("*.gguf"):
                self._register_model(model_file)

    def _register_model(self, model_path: Path) -> None:
        try:
            # Quick metadata extraction without full load
            name = model_path.stem
            size = model_path.stat().st_size

            # Infer from filename
            family = self._guess_family(name)
            quant = self._extract_quant(name)
            params = self._guess_params(name)

            caps = ModelCapabilities(
                max_context_length=self._default_n_ctx,
                supports_streaming=True,
            )

            model_info = ModelInfo(
                id=f"llamacpp:{name}",
                name=name,
                provider=ProviderType.LLAMA_CPP,
                family=family,
                architecture="gguf",
                modality=ModelModality.TEXT,
                capabilities=caps,
                tokenizer="llama",
                runtime="llama.cpp",
                local=True,
                path=str(model_path),
                size_bytes=size,
                quantization=quant,
                parameter_count=params,
                description=f"Local GGUF model: {name}",
            )
            self._model_infos[name] = model_info
        except Exception as exc:
            logger.debug("Failed to register %s: %s", model_path, exc)

    def _get_or_load_model(self, model_id: str) -> Optional[Llama]:
        name = model_id.replace("llamacpp:", "")
        if name in self._models:
            return self._models[name]

        info = self._model_infos.get(name)
        if not info or not info.path:
            return None

        try:
            llm = Llama(
                model_path=info.path,
                n_ctx=self._default_n_ctx,
                n_gpu_layers=self._default_n_gpu_layers,
                verbose=False,
            )
            self._models[name] = llm
            return llm
        except Exception as exc:
            logger.error("Failed to load %s: %s", name, exc)
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
                error="llama.cpp not available",
            )

        model_name = request.model.replace("llamacpp:", "")
        llm = self._get_or_load_model(model_name)
        if not llm:
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

            output = llm(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stop=request.stop,
                stream=False,
            )

            content = output["choices"][0]["text"]
            usage = output.get("usage", {})

            return GenerateResponse(
                content=content.strip(),
                model=request.model,
                provider=self.provider_type,
                finish_reason=output["choices"][0].get("finish_reason", "stop"),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as exc:
            logger.error("llama.cpp generation failed: %s", exc)
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=str(exc),
                latency_ms=(time.time() - start) * 1000,
            )

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        model_name = request.model.replace("llamacpp:", "")
        llm = self._get_or_load_model(model_name)
        if not llm:
            yield StreamChunk(content=f"[Error] Model not found: {model_name}", finish_reason="error")
            return

        try:
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            stream = llm(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stop=request.stop,
                stream=True,
            )

            for chunk in stream:
                text = chunk["choices"][0]["text"]
                if text:
                    yield StreamChunk(content=text)
                if chunk["choices"][0].get("finish_reason"):
                    yield StreamChunk(
                        content="",
                        finish_reason=chunk["choices"][0]["finish_reason"],
                    )
                    break
        except Exception as exc:
            logger.warning("llama.cpp streaming failed: %s", exc)
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        for model in self._models.values():
            try:
                del model
            except Exception:
                pass
        self._models.clear()
        self._loaded = False

    def _guess_family(self, name: str) -> str:
        name_lower = name.lower()
        if any(k in name_lower for k in ["llama", "alpaca", "vicuna"]):
            return "llama"
        if "mistral" in name_lower or "mixtral" in name_lower:
            return "mistral"
        if "qwen" in name_lower:
            return "qwen"
        if "gemma" in name_lower:
            return "gemma"
        if "phi" in name_lower:
            return "phi"
        if any(k in name_lower for k in ["code", "starcoder", "wizardcoder"]):
            return "code"
        return "unknown"

    def _extract_quant(self, name: str) -> str:
        import re
        match = re.search(r"(q[2-8]_[kms]|q[4-8]_[0-9])", name.lower())
        return match.group(1) if match else "unknown"

    def _guess_params(self, name: str) -> int:
        import re
        match = re.search(r"(\d+)b", name.lower())
        if match:
            return int(match.group(1)) * 1_000_000_000
        return 0