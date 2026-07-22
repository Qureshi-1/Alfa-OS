"""NVIDIA Build provider using the OpenAI-compatible API."""

import logging
import time
from typing import Iterator

from prototype.common import EngineResult
from prototype.provider.api_provider import Provider

logger = logging.getLogger("alfa.provider.nvidia")


class NVIDIAProvider(Provider):
    """Connects to NVIDIA Build (integrate.api.nvidia.com/v1).

    Uses the ``openai`` Python SDK.  If the SDK is not installed, the
    provider will report unavailable on ``load()``.
    """

    def __init__(self, settings_manager=None) -> None:
        self._loaded = False
        self._client = None

        if settings_manager is not None:
            cfg = settings_manager.get_provider_config()
        else:
            cfg = {}

        self._api_key: str = cfg.get("api_key", "")
        self._model: str = cfg.get("model", "z-ai/glm-5.2")
        self._base_url: str = cfg.get(
            "base_url", "https://integrate.api.nvidia.com/v1"
        )
        self._timeout: float = float(cfg.get("timeout", 30))
        self._max_retries: int = int(cfg.get("max_retries", 3))
        self._retry_delay: float = float(cfg.get("retry_delay", 1.0))
        self._temperature: float = float(cfg.get("temperature", 0.7))
        self._max_tokens: int = int(cfg.get("max_tokens", 4096))

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        if not self._api_key:
            logger.warning("NVIDIA API key not set — provider unavailable")
            self._loaded = False
            return
        try:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
            )
            self._loaded = True
            logger.info("NVIDIA provider loaded (model=%s)", self._model)
        except ImportError:
            logger.error("openai package not installed — NVIDIA provider unavailable")
            self._loaded = False

    def is_available(self) -> bool:
        return self._loaded and bool(self._api_key) and self._client is not None

    # ── Generate ──────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> EngineResult:
        if not self.is_available():
            return EngineResult(
                content="",
                success=False,
                error="NVIDIA provider not available — check API key",
            )

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    stream=False,
                    timeout=self._timeout,
                )
                content = (response.choices[0].message.content or "").strip()
                if not content:
                    return EngineResult(
                        content="",
                        success=False,
                        error="NVIDIA returned an empty response",
                    )
                return EngineResult(content=content, success=True)
            except Exception as exc:
                last_error = exc
                err = str(exc)
                # Don't retry auth errors.
                if any(code in err for code in ("401", "403", "Authentication")):
                    logger.error("NVIDIA auth failure: %s", err)
                    return EngineResult(
                        content="", success=False, error=f"Authentication failed: {err}"
                    )
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning(
                        "NVIDIA attempt %d failed, retrying in %.1fs: %s",
                        attempt + 1,
                        delay,
                        err,
                    )
                    time.sleep(delay)

        logger.error("NVIDIA exhausted %d retries", self._max_retries)
        return EngineResult(
            content="",
            success=False,
            error=f"NVIDIA error after {self._max_retries} retries: {last_error}",
        )

    # ── Streaming ─────────────────────────────────────────────────────────

    def stream(self, prompt: str) -> Iterator[str]:
        """Stream tokens; falls back to non-streaming on failure."""
        if not self.is_available():
            yield "[Error] NVIDIA provider not available"
            return

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                stream=True,
                timeout=self._timeout,
            )
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
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
        self._client = None