"""NVIDIA Build provider — OpenAI-compatible cloud inference."""

import json
import logging
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.nvidia")


class NVIDIAProvider(ModelProvider):
    """Provider for NVIDIA Build API (integrate.api.nvidia.com)."""

    provider_type = ProviderType.NVIDIA
    display_name = "NVIDIA Build"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._api_key = self._config.get("api_key", "")
        self._base_url = self._config.get("base_url", "https://integrate.api.nvidia.com/v1")
        self._timeout = self._config.get("timeout", 30)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        self._discover_models()
        logger.info("NVIDIA provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    def _discover_models(self) -> None:
        if not self._api_key:
            return
        try:
            req = urllib.request.Request(f"{self._base_url}/models", method="GET")
            req.add_header("Authorization", f"Bearer {self._api_key}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                for m in data.get("data", []):
                    mid = m.get("id", "unknown")
                    self._models[mid] = ModelInfo(
                        id=f"nvidia:{mid}", name=mid, provider=ProviderType.NVIDIA,
                        family=self._guess_family(mid), modality=ModelModality.TEXT,
                        capabilities=ModelCapabilities(max_context_length=4096, supports_tools=True),
                        runtime="nvidia", local=False, description=f"NVIDIA {mid}",
                    )
        except Exception as exc:
            logger.debug("NVIDIA model discovery: %s", exc)

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"}

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="API key not set")

        model = request.model.replace("nvidia:", "")
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

        model = request.model.replace("nvidia:", "")
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
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False

    def _guess_family(self, name: str) -> str:
        n = name.lower()
        if "llama" in n: return "llama"
        if "mistral" in n or "mixtral" in n: return "mistral"
        if "qwen" in n: return "qwen"
        if "gemma" in n: return "gemma"
        return "unknown"