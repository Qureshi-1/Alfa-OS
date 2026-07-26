"""Groq provider — fast inference via Groq API."""

import json
import logging
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.groq")

GROQ_MODELS = {
    "llama-3.3-70b-versatile": ModelCapabilities(max_context_length=128000, supports_tools=True),
    "llama-3.1-8b-instant": ModelCapabilities(max_context_length=128000, supports_tools=True),
    "gemma2-9b-it": ModelCapabilities(max_context_length=8192),
    "mixtral-8x7b-32768": ModelCapabilities(max_context_length=32768),
    "meta-llama/llama-4-scout-17b-16e-instruct": ModelCapabilities(max_context_length=128000, supports_tools=True),
}


class GroqProvider(ModelProvider):
    """Provider for Groq high-speed inference API."""

    provider_type = ProviderType.GROQ
    display_name = "Groq"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._api_key = self._config.get("api_key", "")
        self._base_url = self._config.get("base_url", "https://api.groq.com/openai/v1")
        self._timeout = self._config.get("timeout", 30)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        for name, caps in GROQ_MODELS.items():
            self._models[name] = ModelInfo(
                id=f"groq:{name}", name=name, provider=ProviderType.GROQ,
                family=self._guess_family(name), architecture="transformer",
                modality=ModelModality.TEXT, capabilities=caps,
                runtime="groq", local=False, description=f"Groq {name}",
            )
        logger.info("Groq provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"}

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="API key not set")

        model = request.model.replace("groq:", "")
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

        model = request.model.replace("groq:", "")
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

    def _guess_family(self, name: str) -> str:
        n = name.lower()
        if "llama" in n: return "llama"
        if "gemma" in n: return "gemma"
        if "mixtral" in n: return "mistral"
        return "unknown"