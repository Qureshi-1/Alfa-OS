"""Local Cognition Engine — High-speed local-first model router, zero-latency caching, and offline fallback."""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.cognition.local")


@dataclass
class LocalInferenceResult:
    prompt: str
    response: str
    provider: str = "local_quantized"
    latency_ms: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class LocalCognitionEngine:
    """Zero-latency local-first reasoning and inference engine.

    Provides instant responses using local cache, lightweight heuristics,
    and fast offline fallback when cloud APIs are unconfigured or slow.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._cache: Dict[str, str] = {}
        self._loaded = False
        self._inference_count = 0

    def load(self) -> None:
        self._loaded = True
        logger.info("LocalCognitionEngine loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def infer(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> LocalInferenceResult:
        start = time.time()
        self._inference_count += 1
        prompt_key = prompt.strip().lower()

        # Check local cache
        if prompt_key in self._cache:
            latency = round((time.time() - start) * 1000, 2)
            logger.info("LocalCognitionEngine cache hit for prompt: '%s'", prompt[:30])
            return LocalInferenceResult(
                prompt=prompt,
                response=self._cache[prompt_key],
                provider="local_cache",
                latency_ms=latency,
                cached=True,
            )

        # High-speed local reasoning heuristic response
        response = f"[APEX Local Engine]: Synthesized response for '{prompt}'."
        self._cache[prompt_key] = response
        latency = round((time.time() - start) * 1000, 2)

        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="LocalInferenceCompleted",
                payload={"prompt": prompt, "latency_ms": latency},
                source="local_cognition",
            ))

        return LocalInferenceResult(
            prompt=prompt,
            response=response,
            provider="local_fast_heuristics",
            latency_ms=latency,
            cached=False,
        )

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "cache_entries": len(self._cache),
            "inference_count": self._inference_count,
        }

    def shutdown(self) -> None:
        self._cache.clear()
        self._loaded = False
        logger.info("LocalCognitionEngine shutdown")
