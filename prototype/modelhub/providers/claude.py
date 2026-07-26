"""Anthropic Claude provider."""

import json
import logging
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional

from prototype.modelhub.providers.base import (
    GenerateRequest, GenerateResponse, ModelCapabilities,
    ModelInfo, ModelModality, ModelProvider, ProviderType, StreamChunk,
)

logger = logging.getLogger("alfa.modelhub.claude")

CLAUDE_MODELS = {
    "claude-sonnet-4-20250514": ModelCapabilities(max_context_length=200000, supports_tools=True, supports_vision=True),
    "claude-opus-4-20250514": ModelCapabilities(max_context_length=200000, supports_tools=True, supports_vision=True),
    "claude-3-5-haiku-20241022": ModelCapabilities(max_context_length=200000, supports_tools=True, supports_vision=True),
    "claude-3-5-sonnet-20241022": ModelCapabilities(max_context_length=200000, supports_tools=True, supports_vision=True),
}


class ClaudeProvider(ModelProvider):
    """Provider for Anthropic Claude Messages API."""

    provider_type = ProviderType.CLAUDE
    display_name = "Anthropic Claude"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self._api_key = self._config.get("api_key", "")
        self._base_url = self._config.get("base_url", "https://api.anthropic.com")
        self._timeout = self._config.get("timeout", 60)
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        for name, caps in CLAUDE_MODELS.items():
            self._models[name] = ModelInfo(
                id=f"claude:{name}", name=name, provider=ProviderType.CLAUDE,
                family="claude", architecture="transformer",
                modality=ModelModality.MULTIMODAL, capabilities=caps,
                runtime="claude", local=False,
                description=f"Anthropic {name}",
            )
        logger.info("Claude provider loaded: %d models", len(self._models))

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not self.is_available():
            return GenerateResponse(content="", model=request.model, provider=self.provider_type, success=False, error="API key not set")

        model = request.model.replace("claude:", "")
        start = time.time()

        try:
            msgs = [{"role": "user", "content": request.prompt}]
            body_dict = {
                "model": model, "max_tokens": request.max_tokens,
                "temperature": request.temperature, "top_p": request.top_p,
                "messages": msgs,
            }
            if request.system_prompt:
                body_dict["system"] = request.system_prompt
            if request.stop:
                body_dict["stop_sequences"] = request.stop

            payload = json.dumps(body_dict).encode()
            req = urllib.request.Request(
                f"{self._base_url}/v1/messages", data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                }, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode())
                text = body["content"][0]["text"]
                usage = body.get("usage", {})
                return GenerateResponse(
                    content=text.strip(), model=model, provider=self.provider_type,
                    finish_reason=body.get("stop_reason", "stop"),
                    usage={"prompt_tokens": usage.get("input_tokens", 0), "completion_tokens": usage.get("output_tokens", 0)},
                    latency_ms=(time.time() - start) * 1000,
                )
        except Exception as exc:
            return GenerateResponse(content="", model=model, provider=self.provider_type, success=False, error=str(exc), latency_ms=(time.time() - start) * 1000)

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        if not self.is_available():
            yield StreamChunk(content="[Error] API key not set", finish_reason="error")
            return

        model = request.model.replace("claude:", "")
        try:
            body_dict = {
                "model": model, "max_tokens": request.max_tokens,
                "temperature": request.temperature, "top_p": request.top_p,
                "messages": [{"role": "user", "content": request.prompt}],
                "stream": True,
            }
            if request.system_prompt:
                body_dict["system"] = request.system_prompt

            payload = json.dumps(body_dict).encode()
            req = urllib.request.Request(
                f"{self._base_url}/v1/messages", data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                }, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw in resp:
                    line = raw.decode().strip()
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        etype = data.get("type", "")
                        if etype == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield StreamChunk(content=text)
                        elif etype == "message_stop":
                            yield StreamChunk(content="", finish_reason="stop")
                            return
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    def shutdown(self) -> None:
        self._loaded = False