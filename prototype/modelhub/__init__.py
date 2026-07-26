"""Universal Model Hub — unified interface for all model providers.

Provides a single Provider interface with adapters for:
Ollama, llama.cpp, LM Studio, Jan, MLX, vLLM, HuggingFace,
OpenAI Compatible, Gemini, Claude, Groq, NVIDIA, OpenRouter.
"""

from prototype.modelhub.base import (
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    ModelProvider,
    ModelInfo,
    ModelCapabilities,
    ModelModality,
    ProviderType,
    ModelProviderError,
    ProviderUnavailable,
)

from prototype.modelhub.registry import ModelRegistry, get_model_registry
from prototype.modelhub.router import ModelRouter, get_model_router
from prototype.modelhub.detector import ModelDetector, get_model_detector

__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "StreamChunk",
    "ModelProvider",
    "ModelInfo",
    "ModelCapabilities",
    "ModelModality",
    "ProviderType",
    "ModelProviderError",
    "ProviderUnavailable",
    "ModelRegistry",
    "get_model_registry",
    "ModelRouter",
    "get_model_router",
    "ModelDetector",
    "get_model_detector",
]