"""vLLM provider — high-throughput local inference server."""

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

logger = logging.getLogger("alfa.modelhub.vllm")


class VLLMProvider(ModelProvider):
    """Provider for vLLM OpenAI-compatible API server."""

    provider_type = ProviderType.VLLM
    display_name = "vLLM"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._base_url = self._config.get("base_url", "http://localhost:8000/v1")
        self._api_key = self._config.get("api_key", "dummy")
        self._timeout = self._config.get("timeout", 60)
        self._models: Dict[str, ModelInfo] = {}
        self._loaded = False

    def load(self) -> None:
        self._discover_models()
        self._loaded = True
        logger.info("vLLM provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        if not self._loaded:
            return False
        try:
            req = urllib.request.Request(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _discover_models(self) -> None:
        try:
            req = urllib.request.Request(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for model in data.get("data", []):
                    self._register_model(model)
        except Exception as exc:
            logger.warning("Failed to discover vLLM models: %s", exc)

    def _register_model(self, model_data: Dict[str, Any]) -> None:
        model_id = model_data.get("id", "unknown")
        owned_by = model_data.get("owned_by", "vllm")

        caps = ModelCapabilities(
            max_context_length=32768,
            supports_streaming=True,
            supports_tools=True,
        )

        model_info = ModelInfo(
            id=f"vllm:{model_id}",
            name=model_id,
            provider=ProviderType.VLLM,
            family=owned_by,
            architecture="transformer",
            modality=ModelModality.TEXT,
            capabilities=caps,
            tokenizer="auto",
            runtime="vllm",
            local=True,
            description=f"vLLM model: {model_id}",
            metadata=model_data,
        )
        self._models[model_id] = model_info

    def list_models(self) -> List[ModelInfo]:
        if not self._loaded:
            self.load()
        return list(self._models.values())

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        import time

        if not self.is_available():
            return GenerateResponse(
                content="",
                model=request.model,
                provider=self.provider_type,
                success=False,
                error="vLLM server not available",
            )

        model_name = request.model.replace("vllm:", "")
        start = time.time()

        try:
            payload = json.dumps({
                "model": model_name,
                "messages": [
                    *([{"role": "system", "content": request.system_prompt}] if request.system_prompt else []),
                    {"role": "user", "content": request.prompt},
                ],
                "temperature": request.temperature,
                "top_p": request.top_p,
                "max_tokens": request.max_tokens,
                "stop": request.stop,
                "stream": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                choice = body["choices"][0]
                content = choice["message"]["content"]
                usage = body.get("usage", {})

                return GenerateResponse(
                    content=content.strip(),
                    model=request.model,
                    provider=self.provider_type,
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                    },
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            logger.error("vLLM generation failed: %s", exc)
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
            yield StreamChunk(content="[Error] vLLM server not available", finish_reason="error")
            return

        model_name = request.model.replace("vllm:", "")

        try:
            payload = json.dumps({
                "model": model_name,
                "messages": [
                    *([{"role": "system", "content": request.system_prompt}] if request.system_prompt else []),
                    {"role": "user", "content": request.prompt},
                ],
                "temperature": request.temperature,
                "top_p": request.top_p,
                "max_tokens": request.max_tokens,
                "stop": request.stop,
                "stream": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        yield StreamChunk(content="", finish_reason="stop")
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]
                        content = delta.get("content", "")
                        if content:
                            yield StreamChunk(content=content)
                        finish_reason = chunk["choices"][0].get("finish_reason")
                        if finish_reason:
                            yield StreamChunk(content="", finish_reason=finish_reason)
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.warning("vLLM streaming failed: %s", exc)
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False
        self._models.clear()

    def health_check(self) -> Dict[str, Any]:
        base = super().health_check()
        base["base_url"] = self._base_url
        base["model_count"] = len(self._models)
        return base