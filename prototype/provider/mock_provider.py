"""Mock provider for offline testing — no external API required."""

import re
from typing import Iterator

from prototype.common import EngineResult
from prototype.provider.api_provider import Provider


class MockProvider(Provider):
    """Returns canned responses for testing the full pipeline."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def generate(self, prompt: str) -> EngineResult:
        normalized = prompt.lower()
        memory_section = prompt.partition("Relevant memory:\n")[2].partition(
            "\n\nUser:"
        )[0]

        # Try to answer from memory
        if "what is my" in normalized and memory_section and memory_section != "(none)":
            question = normalized.rsplit("user:", 1)[-1]
            for line in memory_section.splitlines():
                _, _, memory = line.partition("|")
                memory = memory.strip()
                match = re.match(
                    r"my\s+(.+?)\s+is\s+(.+)", memory, flags=re.IGNORECASE
                )
                if match and match.group(1).lower() in question:
                    return EngineResult(
                        content=f"Your {match.group(1)} is {match.group(2)}.",
                        success=True,
                    )
            return EngineResult(content="I don't know that yet.", success=True)

        if "hello" in normalized or "hi " in normalized:
            return EngineResult(
                content="Hello! How can I help you today?", success=True
            )

        return EngineResult(
            content="I understand. (This is a simulated response from MockProvider)",
            success=True,
        )

    def stream(self, prompt: str) -> Iterator[str]:
        result = self.generate(prompt)
        for word in result.content.split():
            yield word + " "

    def shutdown(self) -> None:
        self._loaded = False