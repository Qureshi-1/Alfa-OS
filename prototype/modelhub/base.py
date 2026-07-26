"""Base provider interface and core types for Universal Model Hub."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

logger = logging.getLogger("alfa.modelhub")


class ProviderType(Enum):
    """Supported model provider types."""
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    LM_STUDIO = "lm_studio"
    JAN = "jan"
    MLX = "mlx"
    VLLM = "vllm"
    HUGGINGFACE = "huggingface"
    OPENAI_COMPATIBLE = "openai_compatible"
    GEMINI = "gemini"
    CLAUDE = "claude"
    GROQ = "groq"
    NVIDIA = "nvidia"
    OPENROUTER = "openrouter"
    MOCK = "mock"


class ModelModality(Enum):
    """Model input/output modalities."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class ModelProviderError(Exception):
    """Base exception for model provider errors."""
    pass


class ProviderUnavailable(ModelProviderError):
    """Raised when a provider is unavailable or not configured."""
    pass


class ModelNotFound(ModelProviderError):
    """Raised when a requested model is not found."""
    pass


class GenerationError(ModelProviderError):
    """Raised when generation fails."""
    pass


@dataclass
class ModelCapabilities:
    """Capabilities and features supported by a model."""
    streaming: bool = True
    function_calling: bool = False
    vision: bool = False
    audio: bool = False
    video: bool = False
    max_context_length: int = 4096
    max_output_tokens: int = 4096
    supports_system_prompt: bool = True
    supports_temperature: bool = True
    supports_top_p: bool = True
    supports_stop_sequences: bool = True
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "streaming": self.streaming,
            "function_calling": self.function_calling,
            "vision": self.vision,
            "audio": self.audio,
            "video": self.video,
            "max_context_length": self.max_context_length,
            "max_output_tokens": self.max_output_tokens,
            "supports_system_prompt": self.supports_system_prompt,
            "supports_temperature": self.supports_temperature,
            "supports_top_p": self.supports_top_p,
            "supports_stop_sequences": self.supports_stop_sequences,
            **self.custom_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelCapabilities":
        return cls(
            streaming=data.get("streaming", True),
            function_calling=data.get("function_calling", False),
            vision=data.get("vision", False),
            audio=data.get("audio", False),
            video=data.get("video", False),
            max_context_length=data.get("max_context_length", 4096),
            max_output_tokens=data.get("max_output_tokens", 4096),
            supports_system_prompt=data.get("supports_system_prompt", True),
            supports_temperature=data.get("supports_temperature", True),
            supports_top_p=data.get("supports_top_p", True),
            supports_stop_sequences=data.get("supports_stop_sequences", True),
            custom_fields={k: v for k, v in data.items() if k not in {
                "streaming", "function_calling", "vision", "audio", "video",
                "max_context_length", "max_output_tokens", "supports_system_prompt",
                "supports_temperature", "supports_top_p", "supports_stop_sequences"
            }},
        )


@dataclass
class ModelInfo:
    """Complete model metadata."""
    id: str
    name: str
    provider: ProviderType
    family: str = ""
    architecture: str = ""
    modality: ModelModality = ModelModality.TEXT
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    tokenizer: str = ""
    runtime: str = ""
    local: bool = False
    path: Optional[str] = None
    size_bytes: int = 0
    quantization: str = ""
    parameter_count: int = 0
    license: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0

    @property
    def display_name(self) -> str:
        return self.name or self.id

    @property
    def is_cloud(self) -> bool:
        return not self.local

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "family": self.family,
            "architecture": self.architecture,
            "modality": self.modality.value,
            "capabilities": self.capabilities.to_dict(),
            "tokenizer": self.tokenizer,
            "runtime": self.runtime,
            "local": self.local,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "quantization": self.quantization,
            "parameter_count": self.parameter_count,
            "license": self.license,
            "description": self.description,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        capabilities = ModelCapabilities.from_dict(data.get("capabilities", {}))
        return cls(
            id=data["id"],
            name=data["name"],
            provider=ProviderType(data["provider"]),
            family=data.get("family", ""),
            architecture=data.get("architecture", ""),
            modality=ModelModality(data.get("modality", "text")),
            capabilities=capabilities,
            tokenizer=data.get("tokenizer", ""),
            runtime=data.get("runtime", ""),
            local=data.get("local", False),
            path=data.get("path"),
            size_bytes=data.get("size_bytes", 0),
            quantization=data.get("quantization", ""),
            parameter_count=data.get("parameter_count", 0),
            license=data.get("license", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            discovered_at=datetime.fromisoformat(data["discovered_at"]) if data.get("discovered_at") else datetime.now(),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            usage_count=data.get("usage_count", 0),
        )


@dataclass
class GenerateRequest:
    """Request for text generation."""
    prompt: str
    model: str = ""
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 0
    max_tokens: int = 4096
    stop: List[str] = field(default_factory=list)
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerateResponse:
    """Response from text generation."""
    content: str
    model: str = ""
    provider: ProviderType = ProviderType.MOCK
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider.value,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class StreamChunk:
    """Single chunk from a streaming response."""
    content: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class ModelProvider(ABC):
    """Abstract base class for all model providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._loaded = False
        self._models: Dict[str, ModelInfo] = {}

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Unique provider identifier."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    def load(self) -> None:
        """Initialize the provider and discover available models."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is ready to serve requests."""

    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """List all available models."""

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Synchronous generation."""

    def stream(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        """Stream generation. Default falls back to generate()."""
        response = self.generate(request)
        if response.success:
            yield StreamChunk(content=response.content, finish_reason=response.finish_reason)
        else:
            yield StreamChunk(content=f"[Error] {response.error}", finish_reason="error")

    async def agenerate(self, request: GenerateRequest) -> GenerateResponse:
        """Async generation. Default runs sync in executor."""
        return await asyncio.get_event_loop().run_in_executor(None, self.generate, request)

    async def astream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        """Async streaming. Default falls back to sync stream."""
        for chunk in self.stream(request):
            yield chunk

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup resources."""

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_type.value,
            "available": self.is_available(),
            "model_count": len(self._models),
        }

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        for model in self.list_models():
            if model.id == model_id or model.name == model_id:
                return model
        return None

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> None:
        self._config.update(config)