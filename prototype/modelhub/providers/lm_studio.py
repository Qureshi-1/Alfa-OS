"""LM Studio provider — connects to local LM Studio server (OpenAI-compatible)."""

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

logger = logging.getLogger("alfa.modelhub.lm_studio")


class LMStudioProvider(ModelProvider):
    """Provider for LM Studio local server (OpenAI-compatible API)."""

    provider_type = ProviderType.LM_STUDIO
    display_name = "LM Studio"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._base_url = self._config.get("base_url", "http://localhost:1234")
        self._timeout = self._config.get("timeout", 60)
        self._loaded = False
        self._models: Dict[str, ModelInfo] = {}

    def load(self) -> None:
        self._loaded = True
        self._discover_models()
        logger.info("LM Studio provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        if not self._loaded:
            return False
        try:
            req = urllib.request.Request(f"{self._base_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _discover_models(self) -> None:
        try:
            req = urllib.request.Request(f"{self._base_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for model in data.get("data", []):
                    self._parse_model(model)
        except Exception as exc:
            logger.warning("Failed to discover LM Studio models: %s", exc)

    def _parse_model(self, model_data: Dict[str, Any]) -> None:
        model_id = model_data.get("id", "unknown")
        owned_by = model_data.get("owned_by", "local")

        caps = ModelCapabilities(
            max_context_length=4096,
            supports_streaming=True,
        )

        model_info = ModelInfo(
            id=f"lmstudio:{model_id}",
            name=model_id,
            provider=ProviderType.LM_STUDIO,
            family=self._guess_family(model_id),
            architecture="transformer",
            modality=ModelModality.TEXT,
            capabilities=caps,
            tokenizer="auto",
            runtime="lm_studio",
            local=True,
            description=f"LM Studio model: {model_id}",
            metadata={"owned_by": owned_by},
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
                error="LM Studio not available",
            )

        model_name = request.model.replace("lmstudio:", "")
        start = time.time()

        try:
            payload = json.dumps({
                "model": model_name,
                "messages": [
                    *([{"role": "system", "content": request.system_prompt}] if request.system_prompt else []),
                    {"role": "user", "content": request.prompt},
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stop": request.stop,
                "stream": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
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
            logger.error("LM Studio generation failed: %s", exc)
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
            yield StreamChunk(content="[Error] LM Studio not available", finish_reason="error")
            return

        model_name = request.model.replace("lmstudio:", "")

        try:
            payload = json.dumps({
                "model": model_name,
                "messages": [
                    *([{"role": "system", "content": request.system_prompt}] if request.system_prompt else []),
                    {"role": "user", "content": request.prompt},
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stop": request.stop,
                "stream": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._base_url}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield StreamChunk(content=content)
                        finish_reason = data["choices"][0].get("finish_reason")
                        if finish_reason:
                            yield StreamChunk(content="", finish_reason=finish_reason)
                    except json.JSONDecodeError:
                        continue

        except Exception as exc:
            logger.warning("LM Studio streaming failed: %s", exc)
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False
        self._models.clear()

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
        return "unknown"