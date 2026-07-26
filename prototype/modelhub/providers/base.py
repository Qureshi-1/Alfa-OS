"""Provider base — re-exports from modelhub.base for backward compatibility."""

from prototype.modelhub.base import (
    GenerateRequest,
    GenerateResponse,
    ModelCapabilities,
    ModelInfo,
    ModelModality,
    ModelProvider,
    ProviderType,
    StreamChunk,
)

__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "ModelCapabilities",
    "ModelInfo",
    "ModelModality",
    "ModelProvider",
    "ProviderType",
    "StreamChunk",
]