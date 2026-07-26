from pathlib import Path

import pytest

from prototype.plugins import PluginManager, PonytailPlugin


def test_ponytail_plugin_registers_and_exposes_skill() -> None:
    plugin = PonytailPlugin()
    manager = PluginManager()

    assert manager.register(plugin) is True

    listed = manager.list_plugins()[0]
    assert listed["name"] == "ponytail"
    assert listed["enabled"] is True
    assert listed["healthy"] is True
    assert "coding_guidance" in listed["capabilities"]
    assert "The ladder" in plugin.get_skill_text()
    assert "Ponytail mode: full" in plugin.get_prompt_context()


def test_ponytail_plugin_modes_and_missing_skill(tmp_path: Path) -> None:
    plugin = PonytailPlugin()
    plugin.set_mode("off")
    assert plugin.get_prompt_context() == ""

    with pytest.raises(ValueError):
        plugin.set_mode("maximum")  # type: ignore[arg-type]

    missing = PonytailPlugin(skill_path=tmp_path / "missing.md")
    assert PluginManager().register(missing) is False
