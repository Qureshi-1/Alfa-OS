"""Ponytail skill plugin for Alfa COS.

Bundles the Ponytail agent skill as a first-class Alfa plugin without adding
new runtime dependencies or bypassing the plugin manager.
"""

from pathlib import Path
from typing import Literal

from prototype.plugins.base_plugin import BasePlugin, PluginManifest

PonytailMode = Literal["lite", "full", "ultra", "off"]


class PonytailPlugin(BasePlugin):
    """Expose the bundled Ponytail minimal-coding skill."""

    def __init__(self, skill_path: Path | None = None, mode: PonytailMode = "full") -> None:
        self._mode: PonytailMode = mode
        self._skill_path = skill_path or Path(__file__).resolve().parents[2] / "skills" / "ponytail" / "SKILL.md"
        self._loaded = False

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="ponytail",
            version="1.0.0",
            author="DietrichGebert/ponytail, packaged for Alfa COS",
            description="Minimal-code senior-dev coding ruleset: YAGNI, stdlib first, shortest correct diff.",
            entry="prototype.plugins.ponytail_plugin:PonytailPlugin",
            permissions=[],
            capabilities=["coding_guidance", "skill", "minimal_implementation"],
            enabled=True,
            metadata={
                "mode": self._mode,
                "skill_path": str(self._skill_path),
                "source": "https://github.com/DietrichGebert/ponytail",
                "license": "MIT",
            },
        )

    def on_load(self) -> None:
        if not self._skill_path.exists():
            raise FileNotFoundError(f"Ponytail skill file not found: {self._skill_path}")
        self._loaded = True

    def on_unload(self) -> None:
        self._loaded = False

    def health(self) -> bool:
        return self._loaded and self._skill_path.exists()

    def set_mode(self, mode: PonytailMode) -> None:
        if mode not in {"lite", "full", "ultra", "off"}:
            raise ValueError("mode must be one of: lite, full, ultra, off")
        self._mode = mode

    def get_skill_text(self) -> str:
        return self._skill_path.read_text(encoding="utf-8")

    def get_prompt_context(self) -> str:
        if self._mode == "off":
            return ""
        return f"Ponytail mode: {self._mode}\n\n{self.get_skill_text()}"
