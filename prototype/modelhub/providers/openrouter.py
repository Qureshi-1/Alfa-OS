"""OpenRouter provider — multi-model routing gateway."""

import json
import logging
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.openrouter")


class OpenRouterProvider(ModelProvider):
    """Provider for OpenRouter multi-model gateway."""

    provider_type = ProviderType.OPENROUTER
    display_name = "OpenRouter"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._api_key = self._config.get("api_key", "")
        self._base_url = self._config.get("base_url", "https://openrouter.ai/api/v1")
        self._timeout = self._config.get("timeout", 60)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        self._discover_models()
        logger.info("OpenRouter provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    def _discover_models(self) -> None:
        if not self._api_key:
            return
        try:
            req = urllib.request.Request(f"{self._base_url}/models", method="GET")
            req.add_header("Authorization", f"Bearer {self._api_key}")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                for m in data.get("data", []):
                    mid = m.get("id", "unknown")
                    ctx = m.get("context_length", 4096)
                    pricing = m.get("pricing", {})
                    self._models[mid] = ModelInfo(
                        id=f"openrouter:{mid}", name=mid, provider=ProviderType.OPENROUTER,
                        family=mid.split("/")[0] if "/" in mid else "unknown",
                        modality=ModelModality.TEXT,
                        capabilities=ModelCapabilities(max_context_length=ctx, supports_tools=True),
                        runtime="openrouter", local=False,
                        description=m.get("name", mid),
                        metadata={"pricing": pricing},
                    )
        except Exception as exc:
            logger.debug("OpenRouter discovery: %s", exc)

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/alfa-cos",
            "X-Title": "Alfa COS",
        }

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="API key not set")

        model = request.model.replace("openrouter:", "")
        start = time.time()

        try:
            msgs = []
            if request.system_prompt:
                msgs.append({"role": "system", "content": request.system_prompt})
            msgs.append({"role": "user", "content": request.prompt})

            payload = json.dumps({
                "model": model, "messages": msgs,
                "temperature": request.temperature, "max_tokens": request.max_tokens,
                "top_p": request.top_p, "stream": False,
            }).encode()

            req = urllib.request.Request(f"{self._base_url}/chat/completions", data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode())
                choice = body["choices"][0]
                usage = body.get("usage", {})
                return GenerateResponse(
                    content=choice["message"]["content"].strip(),
                    model=model, provider=self.provider_type,
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage={"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0)},
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return GenerateResponse(content="", model=model, provider=self.provider_type, success=False, error=str(exc), latency_ms=(time.time() - start) * 1000)

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        if not self.is_available():
            yield StreamChunk(content="[Error] API key not set", finish_reason="error")
            return

        model = request.model.replace("openrouter:", "")
        try:
            msgs = []
            if request.system_prompt:
                msgs.append({"role": "system", "content": request.system_prompt})
            msgs.append({"role": "user", "content": request.prompt})

            payload = json.dumps({
                "model": model, "messages": msgs,
                "temperature": request.temperature, "max_tokens": request.max_tokens,
                "top_p": request.top_p, "stream": True,
            }).encode()

            req = urllib.request.Request(f"{self._base_url}/chat/completions", data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw in resp:
                    line = raw.decode().strip()
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        yield StreamChunk(content="", finish_reason="stop")
                        return
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            yield StreamChunk(content=delta)
                        fr = chunk["choices"][0].get("finish_reason")
                        if fr:
                            yield StreamChunk(content="", finish_reason=fr)
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False