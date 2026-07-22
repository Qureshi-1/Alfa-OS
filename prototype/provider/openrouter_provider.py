"""OpenRouter provider using urllib (no extra dependencies)."""

import json
import logging
import time
import urllib.request
import urllib.error
from typing import Iterator

from prototype.common import EngineResult
from prototype.provider.api_provider import Provider

logger = logging.getLogger("alfa.provider.openrouter")


class OpenRouterProvider(Provider):
    """Connects to OpenRouter (openrouter.ai) via its chat-completions API."""

    def __init__(self, settings_manager=None) -> None:
        self._loaded = False

        if settings_manager is not None:
            cfg = settings_manager.get_provider_config()
        else:
            cfg = {}

        self._api_key: str = cfg.get("api_key", "")
        self._model: str = cfg.get("model", "qwen/qwen3-32b")
        self._endpoint: str = cfg.get(
            "base_url", "https://openrouter.ai/api/v1/chat/completions"
        )
        self._timeout: int = int(cfg.get("timeout", 30))
        self._max_retries: int = int(cfg.get("max_retries", 3))
        self._retry_delay: float = float(cfg.get("retry_delay", 1.0))
        self._temperature: float = float(cfg.get("temperature", 0.7))
        self._max_tokens: int = int(cfg.get("max_tokens", 4096))

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        self._loaded = True
        if not self._api_key:
            logger.warning("OpenRouter API key not set — calls will fail")
        else:
            logger.info("OpenRouter provider loaded (model=%s)", self._model)

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key)

    # ── Generate ──────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> EngineResult:
        if not self._loaded:
            return EngineResult(content="", success=False, error="Provider not loaded")
        if not self._api_key:
            return EngineResult(
                content="",
                success=False,
                error="OpenRouter API key not set — use: apikey <key>",
            )

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return self._do_request(prompt)
            except Exception as exc:
                last_error = exc
                err = str(exc)
                if any(code in err for code in ("401", "403")):
                    logger.error("OpenRouter auth failure: %s", err)
                    return EngineResult(
                        content="", success=False, error=f"Authentication failed: {err}"
                    )
                if "429" in err:
                    logger.warning("Rate limited on attempt %d", attempt + 1)
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(
                        "OpenRouter attempt %d failed, retrying in %.1fs: %s",
                        attempt + 1,
                        delay,
                        err,
                    )
                    time.sleep(delay)

        logger.error("OpenRouter exhausted %d retries", self._max_retries)
        return EngineResult(
            content="",
            success=False,
            error=f"OpenRouter error after {self._max_retries} retries: {last_error}",
        )

    def _do_request(self, prompt: str) -> EngineResult:
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
                "stream": False,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://github.com/alfa-cos",
                "X-Title": "Alfa COS",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            body = resp.read().decode("utf-8")
            if resp.status != 200:
                return EngineResult(
                    content="",
                    success=False,
                    error=f"HTTP {resp.status}: {body[:200]}",
                )
            try:
                data = json.loads(body)
            except json.JSONDecodeError as exc:
                return EngineResult(
                    content="",
                    success=False,
                    error=f"Invalid JSON from OpenRouter: {exc}",
                )
            content = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            if not content:
                return EngineResult(
                    content="", success=False, error="Empty response from OpenRouter"
                )
            return EngineResult(content=content.strip(), success=True)

    # ── Streaming (falls back to non-streaming) ──────────────────────────

    def stream(self, prompt: str) -> Iterator[str]:
        """OpenRouter streaming — falls back on failure."""
        if not self.is_available():
            yield "[Error] OpenRouter not available"
            return

        try:
            payload = json.dumps(
                {
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "stream": True,
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                self._endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://github.com/alfa-cos",
                    "X-Title": "Alfa COS",
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
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.warning("Streaming failed, falling back: %s", exc)
            result = self.generate(prompt)
            if result.success:
                yield result.content
            else:
                yield f"[Error] {result.error}"

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._loaded = False