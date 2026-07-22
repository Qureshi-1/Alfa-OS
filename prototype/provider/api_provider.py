"""Abstract base provider interface for Alfa COS."""

from abc import ABC, abstractmethod
from typing import Iterator

from prototype.common import EngineResult


class ProviderUnavailable(Exception):
    """Raised when a provider cannot fulfil a request."""


class Provider(ABC):
    """Base class for all LLM providers.

    Every provider must implement ``load``, ``generate``, and ``shutdown``.
    ``stream`` has a default implementation that falls back to ``generate``.
    """

    @abstractmethod
    def load(self) -> None:
        """Initialise the provider (connect, authenticate, etc.)."""

    @abstractmethod
    def generate(self, prompt: str) -> EngineResult:
        """Synchronous, non-streaming generation."""

    def stream(self, prompt: str) -> Iterator[str]:
        """Yield tokens one at a time.  Default falls back to ``generate``."""
        result = self.generate(prompt)
        if result.success:
            yield result.content
        else:
            yield f"[Error] {result.error}"

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources."""

    # Convenience ──────────────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        return type(self).__name__