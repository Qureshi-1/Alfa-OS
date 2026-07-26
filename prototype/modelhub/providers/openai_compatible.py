"""OpenAI Compatible provider — any server implementing OpenAI chat API."""

import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.openai_compatible")


class OpenAICompatibleProvider(ModelProvider):
    """Provider for any OpenAI-compatible endpoint."""

    provider_type = ProviderType.OPENAI_COMPATIBLE
    display_name = "OpenAI Compatible"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._base_url = self._config.get("base_url", "http://localhost:8000/v1")
        self._api_key = self._config.get("api_key", "")
        self._timeout = self._config.get("timeout", 60)
        self._models: Dict[str, ModelInfo] = {}
        self._loaded = False

    def load(self) -> None:
        self._discover_models()
        self._loaded = True
        logger.info("OpenAI Compatible loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        if not self._loaded:
            return False
        try:
            req = urllib.request.Request(f"{self._base_url}/models", method="GET")
            if self._api_key:
                req.add_header("Authorization", f"Bearer {self._api_key}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _discover_models(self) -> None:
        try:
            req = urllib.request.Request(f"{self._base_url}/models", method="GET")
            if self._api_key:
                req.add_header("Authorization", f"Bearer {self._api_key}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("data", []):
                    mid = m.get("id", "unknown")
                    self._models[mid] = ModelInfo(
                        id=f"oai:{mid}", name=mid,
                        provider=ProviderType.OPENAI_COMPATIBLE,
                        modality=ModelModality.TEXT,
                        capabilities=ModelCapabilities(max_context_length=128000),
                        runtime="openai_compatible",
                        local=False, description=f"OpenAI-compatible: {mid}",
                    )
        except Exception as exc:
            logger.warning("Discovery failed: %s", exc)

    def list_models(self) -> List[ModelInfo]:
        if not self._loaded:
            self.load()
        return list(self._models.values())

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="Not available")

        model = request.model.replace("oai:", "")
        start = time.time()

        try:
            msgs = []
            if request.system_prompt:
                msgs.append({"role": "system", "content": request.system_prompt})
            msgs.append({"role": "user", "content": request.prompt})

            payload = json.dumps({
                "model": model, "messages": msgs,
                "temperature": request.temperature, "max_tokens": request.max_tokens,
                "top_p": request.top_p, "stop": request.stop, "stream": False,
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
            yield StreamChunk(content="[Error] Not available", finish_reason="error")
            return

        model = request.model.replace("oai:", "")
        try:
            msgs = []
            if request.system_prompt:
                msgs.append({"role": "system", "content": request.system_prompt})
            msgs.append({"role": "user", "content": request.prompt})

            payload = json.dumps({
                "model": model, "messages": msgs,
                "temperature": request.temperature, "max_tokens": request.max_tokens,
                "top_p": request.top_p, "stop": request.stop, "stream": True,
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
        self._models.clear()