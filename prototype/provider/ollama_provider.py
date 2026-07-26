"""Ollama provider — connects to locally running Ollama instances.

Uses urllib for HTTP (no extra dependencies). Compatible with the
Ollama REST API at http://localhost:11434.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, Iterator, Optional

from prototype.common import EngineResult
from prototype.provider.api_provider import Provider

logger = logging.getLogger("alfa.provider.ollama")


class OllamaProvider(Provider):
    """Connects to a local Ollama instance.

    Ollama API endpoint: http://localhost:11434/api/chat
    """

    def __init__(self, settings_manager=None) -> None:
        self._loaded = False

        if settings_manager is not None:
            cfg = settings_manager.get_provider_config()
        else:
            cfg = {}

        self._model: str = cfg.get("model", "llama3.2")
        self._endpoint: str = cfg.get(
            "base_url", "http://localhost:11434"
        )
        self._timeout: int = int(cfg.get("timeout", 60))
        self._temperature: float = float(cfg.get("temperature", 0.7))

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(self) -> None:
        self._loaded = True
        logger.info("Ollama provider loaded (model=%s)", self._model)

    def is_available(self) -> bool:
        """Check if Ollama is running locally."""
        if not self._loaded:
            return False
        try:
            req = urllib.request.Request(
                f"{self._endpoint}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    # ── Generate ──────────────────────────────────────────────────────────

    def generate(self, prompt: str) -> EngineResult:
        if not self._loaded:
            return EngineResult(content="", success=False, error="Provider not loaded")

        try:
            payload = json.dumps({
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": self._temperature},
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._endpoint}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                content = data.get("message", {}).get("content", "")
                if not content:
                    return EngineResult(
                        content="", success=False, error="Empty response from Ollama"
                    )
                return EngineResult(content=content.strip(), success=True)

        except urllib.error.URLError as exc:
            logger.error("Ollama connection failed: %s", exc)
            return EngineResult(
                content="",
                success=False,
                error=f"Ollama connection failed: {exc}",
            )
        except Exception as exc:
            logger.exception("Ollama generate failed")
            return EngineResult(content="", success=False, error=str(exc))

    # ── Streaming ─────────────────────────────────────────────────────────

    def stream(self, prompt: str) -> Iterator[str]:
        """Stream tokens from Ollama. Falls back to non-streaming on failure."""
        if not self._loaded:
            yield "[Error] Ollama provider not loaded"
            return

        try:
            payload = json.dumps({
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "options": {"temperature": self._temperature},
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._endpoint}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            logger.warning("Ollama streaming failed, falling back: %s", exc)
            result = self.generate(prompt)
            if result.success:
                yield result.content
            else:
                yield f"[Error] {result.error}"

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._loaded = False
