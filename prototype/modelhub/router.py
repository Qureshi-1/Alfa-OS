"""Model Router — intelligent routing for provider/model selection."""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from prototype.modelhub.base import (
    GenerateRequest, GenerateResponse, ModelInfo, ModelProvider, ProviderType,
    StreamChunk,
)
from prototype.modelhub.registry import ModelRegistry, get_model_registry

logger = logging.getLogger("alfa.modelhub.router")


@dataclass
class ProviderHealth:
    provider: ProviderType
    available: bool = True
    latency_ms: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    last_check: float = 0.0
    last_error: str = ""

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return 1.0 - (self.failed_requests / self.total_requests)


@dataclass
class RoutingPolicy:
    prefer_local: bool = True
    prefer_low_latency: bool = True
    max_latency_ms: float = 5000.0
    fallback_providers: List[ProviderType] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    provider_weights: Dict[ProviderType, float] = field(default_factory=dict)


class ModelRouter:
    """Routes generation requests to the best available provider/model.

    Decision factors:
    - Provider availability & health
    - Latency history
    - Model capabilities match
    - User preferences (local/cloud, provider)
    - Automatic fallback on failure
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        policy: Optional[RoutingPolicy] = None,
    ) -> None:
        self._registry = registry or get_model_registry()
        self._policy = policy or RoutingPolicy()
        self._health: Dict[ProviderType, ProviderHealth] = {}
        self._providers: Dict[ProviderType, ModelProvider] = {}
        self._default_model: Optional[str] = None
        self._lock = threading.RLock()

    def load(self) -> None:
        for ptype in self._registry.list_providers():
            provider = self._registry.get_provider(ptype)
            if provider:
                self._providers[ptype] = provider
                self._health[ptype] = ProviderHealth(provider=ptype)
        logger.info("Router loaded: %d providers", len(self._providers))

    # ── Provider Registration ──────────────────────────────────────────────

    def register_provider(self, provider: ModelProvider) -> None:
        ptype = provider.provider_type
        self._providers[ptype] = provider
        self._health[ptype] = ProviderHealth(provider=ptype)
        logger.info("Router registered provider: %s", ptype.value)

    def set_default_model(self, model_id: str) -> None:
        self._default_model = model_id

    def set_policy(self, policy: RoutingPolicy) -> None:
        self._policy = policy

    # ── Routing ────────────────────────────────────────────────────────────

    def route(self, request: GenerateRequest) -> Tuple[ModelProvider, GenerateRequest]:
        """Select best provider and adjust request for routing."""

        # Explicit model requested — route to its provider
        if request.model:
            provider = self._find_provider_for_model(request.model)
            if provider and self._is_healthy(provider.provider_type):
                return provider, request

        # Try local providers first if policy prefers
        if self._policy.prefer_local:
            for ptype in [ProviderType.OLLAMA, ProviderType.LLAMA_CPP, ProviderType.LM_STUDIO,
                          ProviderType.VLLM, ProviderType.MLX, ProviderType.HUGGINGFACE, ProviderType.JAN]:
                provider = self._providers.get(ptype)
                if provider and provider.is_available():
                    models = provider.list_models()
                    if models:
                        if not request.model or request.model == "auto":
                            request.model = models[0].id
                        return provider, request

        # Score and rank cloud providers
        candidates: List[Tuple[float, ModelProvider]] = []
        for ptype, provider in self._providers.items():
            if not provider.is_available():
                continue
            score = self._score_provider(ptype)
            if score > 0:
                candidates.append((score, provider))

        candidates.sort(key=lambda x: x[0], reverse=True)

        for score, provider in candidates:
            models = provider.list_models()
            if models:
                if not request.model or request.model == "auto":
                    request.model = models[0].id
                return provider, request

        # Fallback to mock or any provider
        for provider in self._providers.values():
            if provider.is_available():
                models = provider.list_models()
                if models:
                    request.model = models[0].id
                    return provider, request

        raise RuntimeError("No providers available")

    def route_with_model(self, request: GenerateRequest, model_id: str) -> Tuple[ModelProvider, GenerateRequest]:
        """Route to the provider that owns a specific model."""
        provider = self._find_provider_for_model(model_id)
        if not provider:
            raise RuntimeError(f"No provider found for model: {model_id}")
        request.model = model_id
        return provider, request

    def _find_provider_for_model(self, model_id: str) -> Optional[ModelProvider]:
        # Check registry first
        model_info = self._registry.get_model(model_id)
        if model_info:
            return self._providers.get(model_info.provider)

        # Try prefix match (e.g., "ollama:llama3")
        if ":" in model_id:
            prefix = model_id.split(":")[0]
            for ptype, provider in self._providers.items():
                if ptype.value == prefix or ptype.value.replace("_", "") == prefix.replace(".", ""):
                    return provider

        # Search all providers
        for provider in self._providers.values():
            for model in provider.list_models():
                if model.id == model_id or model.name == model_id:
                    return provider
        return None

    def _score_provider(self, ptype: ProviderType) -> float:
        health = self._health.get(ptype)
        if not health or not health.available:
            return 0.0

        score = 1.0

        # Latency penalty
        if health.latency_ms > 0:
            latency_score = max(0, 1.0 - (health.latency_ms / self._policy.max_latency_ms))
            score *= (0.5 + 0.5 * latency_score)

        # Error rate penalty
        score *= health.success_rate

        # Weight bonus
        weight = self._policy.provider_weights.get(ptype, 1.0)
        score *= weight

        # Local preference bonus
        if self._policy.prefer_local and ptype in {
            ProviderType.OLLAMA, ProviderType.LLAMA_CPP, ProviderType.LM_STUDIO,
            ProviderType.VLLM, ProviderType.MLX, ProviderType.HUGGINGFACE,
        }:
            score *= 1.5

        return score

    def _is_healthy(self, ptype: ProviderType) -> bool:
        health = self._health.get(ptype)
        return health is not None and health.available

    # ── Execution ──────────────────────────────────────────────────────────

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Route and generate with automatic fallback."""
        provider, adjusted_request = self.route(request)
        start = time.time()

        try:
            response = provider.generate(adjusted_request)
            self._record_success(provider.provider_type, (time.time() - start) * 1000)
            return response
        except Exception as exc:
            self._record_failure(provider.provider_type, str(exc))
            # Try fallback
            for fallback_ptype in self._policy.fallback_providers:
                fallback = self._providers.get(fallback_ptype)
                if fallback and fallback.is_available() and fallback != provider:
                    try:
                        adjusted_request.model = ""
                        resp = fallback.generate(adjusted_request)
                        self._record_success(fallback_ptype, (time.time() - start) * 1000)
                        return resp
                    except Exception:
                        continue
            return GenerateResponse(
                content="", model=request.model, provider=provider.provider_type,
                success=False, error=str(exc), latency_ms=(time.time() - start) * 1000,
            )

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        """Route and stream."""
        provider, adjusted_request = self.route(request)
        try:
            yield from provider.stream(adjusted_request)
        except Exception as exc:
            yield StreamChunk(content=f"[Error] {exc}", finish_reason="error")

    # ── Health Tracking ────────────────────────────────────────────────────

    def _record_success(self, ptype: ProviderType, latency_ms: float) -> None:
        health = self._health.get(ptype)
        if health:
            health.total_requests += 1
            health.latency_ms = latency_ms
            health.available = True

    def _record_failure(self, ptype: ProviderType, error: str) -> None:
        health = self._health.get(ptype)
        if health:
            health.total_requests += 1
            health.failed_requests += 1
            health.last_error = error
            if health.failed_requests > 5 and health.success_rate < 0.3:
                health.available = False
                logger.warning("Provider %s marked unavailable (error rate: %.1f%%)", ptype.value, (1 - health.success_rate) * 100)

    def health_check(self) -> Dict[str, Any]:
        result = {}
        for ptype, health in self._health.items():
            provider = self._providers.get(ptype)
            result[ptype.value] = {
                "available": health.available and (provider.is_available() if provider else False),
                "latency_ms": health.latency_ms,
                "success_rate": health.success_rate,
                "total_requests": health.total_requests,
                "failed_requests": health.failed_requests,
                "last_error": health.last_error,
                "model_count": len(provider.list_models()) if provider else 0,
            }
        return result

    def shutdown(self) -> None:
        self._providers.clear()
        self._health.clear()


# ── Singleton ───────────────────────────────────────────────────────────────

_router_instance: Optional[ModelRouter] = None
_router_lock = threading.Lock()


def get_model_router(registry: Optional[ModelRegistry] = None) -> ModelRouter:
    global _router_instance
    with _router_lock:
        if _router_instance is None:
            _router_instance = ModelRouter(registry)
        return _router_instance


def reset_model_router() -> None:
    global _router_instance
    with _router_lock:
        _router_instance = None