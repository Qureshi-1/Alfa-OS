"""Google Gemini provider."""

import json
import logging
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.gemini")

GEMINI_MODELS = {
    "gemini-2.5-pro": ModelCapabilities(max_context_length=1048576, supports_vision=True, supports_tools=True),
    "gemini-2.5-flash": ModelCapabilities(max_context_length=1048576, supports_vision=True, supports_tools=True),
    "gemini-2.0-flash": ModelCapabilities(max_context_length=1048576, supports_vision=True, supports_tools=True),
    "gemini-1.5-pro": ModelCapabilities(max_context_length=2097152, supports_vision=True),
    "gemini-1.5-flash": ModelCapabilities(max_context_length=1048576, supports_vision=True),
}


class GeminiProvider(ModelProvider):
    """Provider for Google Gemini API."""

    provider_type = ProviderType.GEMINI
    display_name = "Google Gemini"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._api_key = self._config.get("api_key", "")
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._timeout = self._config.get("timeout", 60)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        for name, caps in GEMINI_MODELS.items():
            self._models[name] = ModelInfo(
                id=f"gemini:{name}", name=name, provider=ProviderType.GEMINI,
                family="gemini", architecture="transformer",
                modality=ModelModality.MULTIMODAL, capabilities=caps,
                runtime="gemini", local=False,
                description=f"Google {name}",
            )
        logger.info("Gemini provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def _url(self, model: str, action: str = "generateContent") -> str:
        return f"{self._base_url}/models/{model}:{action}?key={self._api_key}"

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="API key not set")

        model = request.model.replace("gemini:", "")
        start = time.time()

        try:
            contents = []
            if request.system_prompt:
                contents.append({"role": "user", "parts": [{"text": request.system_prompt}]})
            contents.append({"role": "user", "parts": [{"text": request.prompt}]})

            payload = json.dumps({
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature, "topP": request.top_p,
                    "maxOutputTokens": request.max_tokens,
                },
            }).encode()

            req = urllib.request.Request(self._url(model), data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode())
                text = body["candidates"][0]["content"]["parts"][0]["text"]
                usage = body.get("usageMetadata", {})
                return GenerateResponse(
                    content=text.strip(), model=model, provider=self.provider_type,
                    finish_reason="stop",
                    usage={"prompt_tokens": usage.get("promptTokenCount", 0), "completion_tokens": usage.get("candidatesTokenCount", 0)},
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return GenerateResponse(content="", model=model, provider=self.provider_type, success=False, error=str(exc), latency_ms=(time.time() - start) * 1000)

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        if not self.is_available():
            yield StreamChunk(content="[Error] API key not set", finish_reason="error")
            return

        model = request.model.replace("gemini:", "")
        try:
            contents = []
            if request.system_prompt:
                contents.append({"role": "user", "parts": [{"text": request.system_prompt}]})
            contents.append({"role": "user", "parts": [{"text": request.prompt}]})

            payload = json.dumps({
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature, "topP": request.top_p,
                    "maxOutputTokens": request.max_tokens,
                },
            }).encode()

            req = urllib.request.Request(
                self._url(model, "streamGenerateContent?alt=sse"),
                data=payload, headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw in resp:
                    line = raw.decode().strip()
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if text:
                            yield StreamChunk(content=text)
                    except (json.JSONDecodeError, KeyError):
                        continue
            yield StreamChunk(content="", finish_reason="stop")
        except Exception as exc:
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False