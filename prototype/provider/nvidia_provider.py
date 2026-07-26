"""NVIDIA Build provider using the OpenAI-compatible API."""

import logging
import time
from typing import Any, Dict, Iterator, Optional

from prototype.common import EngineResult
from prototype.provider.api_provider import Provider

logger = logging.getLogger("alfa.provider.nvidia")


class NVIDIAProvider(Provider):
    """Connects to NVIDIA Build (integrate.api.nvidia.com/v1).

    Uses the OpenAI Python SDK or urllib fallback.
    Exposes detailed diagnostics, URL logging, status codes, and error classification.
    """

    def __init__(self, settings_manager=None) -> None:
        self._loaded = False
        self._client = None
        self._settings_manager = settings_manager

        self._api_key: str = ""
        self._model: str = "meta/llama-3.3-70b-instruct"
        self._base_url: str = "https://integrate.api.nvidia.com/v1"
        self._timeout: float = 30.0
        self._max_retries: int = 3
        self._retry_delay: float = 1.0
        self._temperature: float = 0.7
        self._max_tokens: int = 4096

        self._refresh_config()

    def _refresh_config(self) -> None:
        """Dynamically refresh provider settings from settings manager if available."""
        if self._settings_manager is not None:
            cfg = self._settings_manager.get_provider_config()
        else:
            cfg = {}

        self._api_key = cfg.get("api_key", "").strip()
        model_name = cfg.get("model", "meta/llama-3.3-70b-instruct")
        if model_name == "z-ai/glm-5.2":
            model_name = "meta/llama-3.3-70b-instruct"
        self._model = model_name
        self._base_url = cfg.get("base_url", "https://integrate.api.nvidia.com/v1").rstrip("/")
        self._timeout = float(cfg.get("timeout", 30))
        self._max_retries = int(cfg.get("max_retries", 3))
        self._retry_delay = float(cfg.get("retry_delay", 1.0))
        self._temperature = float(cfg.get("temperature", 0.7))
        self._max_tokens = int(cfg.get("max_tokens", 4096))

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        self._refresh_config()
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
            logger.info("NVIDIA provider loaded: base_url=%s model=%s", self._base_url, self._model)
        except ImportError:
            logger.error("openai package not installed — NVIDIA provider unavailable")
            self._loaded = False

    def is_available(self) -> bool:
        self._refresh_config()
        return self._loaded and bool(self._api_key) and self._client is not None

    # ── Generate ──────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> EngineResult:
        self._refresh_config()

        if not self._api_key:
            logger.error("NVIDIA Generation Aborted: API Key not set")
            return EngineResult(
                content="",
                success=False,
                error="Provider Unavailable: NVIDIA API key is missing. Please set your API key in Settings.",
            )

        if not self.is_available():
            # Re-attempt load if not loaded yet
            self.load()
            if not self.is_available():
                logger.error("NVIDIA Generation Aborted: Provider client not available")
                return EngineResult(
                    content="",
                    success=False,
                    error="Provider Unavailable: Failed to initialize NVIDIA client connection.",
                )

        request_url = f"{self._base_url}/chat/completions"
        logger.info("NVIDIA API Request Initiated: URL=%s | Model=%s | Timeout=%.1fs", request_url, self._model, self._timeout)

        # Import openai exception types dynamically if available
        try:
            import openai
            auth_err_cls = (openai.AuthenticationError, getattr(openai, "PermissionDeniedError", Exception))
            not_found_cls = getattr(openai, "NotFoundError", Exception)
            timeout_cls = getattr(openai, "APITimeoutError", Exception)
            conn_cls = getattr(openai, "APIConnectionError", Exception)
            status_err_cls = getattr(openai, "APIStatusError", Exception)
        except ImportError:
            openai = None
            auth_err_cls = not_found_cls = timeout_cls = conn_cls = status_err_cls = Exception

        last_error: Optional[Exception] = None

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
                    logger.warning("NVIDIA API returned HTTP 200 with empty completion content")
                    return EngineResult(
                        content="",
                        success=False,
                        error="NVIDIA API returned an empty response.",
                    )
                logger.info("NVIDIA Request Succeeded: %d chars received", len(content))
                return EngineResult(content=content, success=True)

            # 1. Invalid API Key / Auth Failure (HTTP 401 / 403)
            except auth_err_cls as exc:
                body = getattr(exc, "body", getattr(exc, "response", str(exc)))
                logger.error("NVIDIA Auth Failure [HTTP 401/403] at %s | Error: %s | Body: %s", request_url, exc, body)
                return EngineResult(
                    content="",
                    success=False,
                    error=f"Invalid API Key (HTTP 401/403): {exc}. Please verify your NVIDIA API key in Settings.",
                )

            # 2. Model Not Found (HTTP 404)
            except not_found_cls as exc:
                body = getattr(exc, "body", getattr(exc, "response", str(exc)))
                logger.error("NVIDIA Model Not Found [HTTP 404] at %s | Model: '%s' | Body: %s", request_url, self._model, body)
                return EngineResult(
                    content="",
                    success=False,
                    error=f"Model Not Found (HTTP 404): Model '{self._model}' is not available on NVIDIA Build API.",
                )

            # 3. Timeout Error
            except timeout_cls as exc:
                last_error = exc
                logger.error("NVIDIA Timeout Exception at %s after %.1fs: %s", request_url, self._timeout, exc)
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning("NVIDIA Retry %d/%d after timeout at %s (waiting %.1fs)", attempt + 1, self._max_retries, request_url, delay)
                    time.sleep(delay)

            # 4. Network Failure / Connection Refused
            except conn_cls as exc:
                last_error = exc
                logger.error("NVIDIA Network Connection Failure at %s: %s", request_url, exc)
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    logger.warning("NVIDIA Retry %d/%d after network error (waiting %.1fs)", attempt + 1, self._max_retries, delay)
                    time.sleep(delay)

            # 5. Generic HTTP Status Error (400, 429, 500, 503)
            except status_err_cls as exc:
                last_error = exc
                status_code = getattr(exc, "status_code", "HTTP_ERROR")
                body = getattr(exc, "body", getattr(exc, "response", str(exc)))
                logger.error("NVIDIA Status Error [%s] at %s: %s | Body: %s", status_code, request_url, exc, body)
                if status_code in (400, 422):
                    return EngineResult(
                        content="",
                        success=False,
                        error=f"NVIDIA API Error [{status_code}]: {exc} | Details: {body}",
                    )
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    time.sleep(delay)

            # 6. Fallback General Exception Handling
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                logger.error("NVIDIA Unexpected Exception at %s: %s", request_url, exc, exc_info=True)
                if any(code in err_str for code in ("401", "403", "Authentication", "Unauthorized")):
                    return EngineResult(
                        content="",
                        success=False,
                        error=f"Invalid API Key / Auth Error: {err_str}",
                    )
                if any(code in err_str for code in ("404", "Not Found")):
                    return EngineResult(
                        content="",
                        success=False,
                        error=f"Model Not Found (HTTP 404): '{self._model}'",
                    )
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (attempt + 1)
                    time.sleep(delay)

        logger.error("NVIDIA Exhausted all %d retries for URL %s | Last Error: %s", self._max_retries, request_url, last_error)
        return EngineResult(
            content="",
            success=False,
            error=f"NVIDIA error after {self._max_retries} retries at {request_url}: {last_error}",
        )

    # ── Streaming ─────────────────────────────────────────────────────────

    def stream(self, prompt: str) -> Iterator[str]:
        """Stream tokens; falls back to non-streaming on failure."""
        self._refresh_config()
        if not self.is_available():
            yield "[Error] NVIDIA provider unavailable — check API key"
            return

        try:
            request_url = f"{self._base_url}/chat/completions"
            logger.info("NVIDIA Stream Request Initiated: URL=%s | Model=%s", request_url, self._model)
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
            logger.warning("NVIDIA Streaming failed (%s), falling back to generate()", exc)
            result = self.generate(prompt)
            if result.success:
                yield result.content
            else:
                yield f"[Error] {result.error}"

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._loaded = False
        self._client = None