"""Ollama provider — connects to local Ollama instances."""

import json
import logging
import urllib.request
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

logger = logging.getLogger("alfa.modelhub.ollama")


class OllamaProvider(ModelProvider):
    """Provider for Ollama local models (http://localhost:11434)."""

    provider_type = ProviderType.OLLAMA
    display_name = "Ollama"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._base_url = self._config.get("base_url", "http://localhost:11434")
        self._timeout = self._config.get("timeout", 60)
        self._loaded = False
        self._models: Dict[str, ModelInfo] = {}

    def load(self) -> None:
        """Connect to Ollama and discover models."""
        self._loaded = True
        self._discover_models()
        logger.info("Ollama provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        if not self._loaded:
            return False
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _discover_models(self) -> None:
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for model in data.get("models", []):
                    self._parse_ollama_model(model)
        except Exception as exc:
            logger.warning("Failed to discover Ollama models: %s", exc)

    def _parse_ollama_model(self, model_data: Dict[str, Any]) -> None:
        name = model_data.get("name", "unknown")
        size = model_data.get("size", 0)
        details = model_data.get("details", {})

        family = details.get("family", "").lower()
        quantization = details.get("quantization_level", "")
        param_count = details.get("parameter_size", "")

        # Infer capabilities from model name/size
        caps = ModelCapabilities(
            max_context_length=details.get("context_length", 4096),
            streaming=True,
        )

        model_info = ModelInfo(
            id=f"ollama:{name}",
            name=name,
            provider=ProviderType.OLLAMA,
            family=family or self._guess_family(name),
            architecture=details.get("format", "gguf"),
            modality=ModelModality.TEXT,
            capabilities=caps,
            tokenizer="llama",
            runtime="ollama",
            local=True,
            size_bytes=size,
            quantization=quantization,
            parameter_count=self._parse_param_count(param_count),
            description=f"Ollama model: {name}",
            metadata={"details": details},
        )
        self._models[name] = model_info

    def list_models(self) -> List[ModelInfo]:
        if not self._loaded:
            self.load()
        return list(self._models.values())

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        for model in self._models.values():
            if model.id == model_id or model.name == model_id:
                return model
        return None

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        import time

        if not self.is_available():
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error="Ollama not available",
            )

        model_name = request.model.replace("ollama:", "")
        start = time.time()

        try:
            payload = json.dumps({
                "model": model_name,
                "prompt": request.prompt,
                "system": request.system_prompt,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
                "stop": request.stop,
                "stream": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = body.get("response", "")
                latency = (time.time() - start) * 1000

                return GenerateResponse(
                    content=content.strip(),
                    model=request.model,
                    provider=self.provider_type,
                    finish_reason="stop" if body.get("done") else "length",
                    usage={"prompt_tokens": body.get("prompt_eval_count", 0),
                           "completion_tokens": body.get("eval_count", 0)},
                    latency_ms=latency,
                )

        except Exception as exc:
            logger.error("Ollama generation failed: %s", exc)
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error=str(exc),
                latency_ms=(time.time() - start) * 1000,
            )

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        if not self.is_available():
            yield StreamChunk(content="[Error] Ollama not available", finish_reason="error")
            return

        model_name = request.model.replace("ollama:", "")

        try:
            payload = json.dumps({
                "model": model_name,
                "prompt": request.prompt,
                "system": request.system_prompt,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
                "stop": request.stop,
                "stream": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("response", "")
                        if content:
                            yield StreamChunk(content=content)
                        if data.get("done", False):
                            yield StreamChunk(
                                content="",
                                finish_reason="stop",
                                usage={"prompt_tokens": data.get("prompt_eval_count", 0),
                                      "completion_tokens": data.get("eval_count", 0)},
                            )
                            break
                    except json.JSONDecodeError:
                        continue

        except Exception as exc:
            logger.warning("Ollama streaming failed: %s", exc)
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False
        self._models.clear()

    def health_check(self) -> Dict[str, Any]:
        base = super().health_check()
        base["base_url"] = self._base_url
        base["model_count"] = len(self._models)
        return base

    def _guess_family(self, name: str) -> str:
        name_lower = name.lower()
        families = {
            "llama": ["llama", "alpaca", "vicuna", "guanaco"],
            "mistral": ["mistral", "mixtral"],
            "qwen": ["qwen"],
            "gemma": ["gemma"],
            "phi": ["phi"],
            "code": ["code", "starcoder", "wizardcoder"],
        }
        for fam, keywords in families.items():
            if any(k in name_lower for k in keywords):
                return fam
        return "unknown"

    def _parse_param_count(self, param_str: str) -> int:
        if not param_str:
            return 0
        original = param_str.upper()
        numeric_str = original.replace("B", "").replace("M", "").strip()
        try:
            val = float(numeric_str)
            if "B" in original:
                return int(val * 1_000_000_000)
            if "M" in original:
                return int(val * 1_000_000)
            return int(val)
        except ValueError:
            return 0