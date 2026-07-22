#!/usr/bin/env python3
"""
Alfa COS — Cognitive Operating System  v0.1
Boot Sequence, CLI Loop, and Structured Logging
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from prototype.kernel import Kernel
from prototype.context import ContextManager
from prototype.memory import Memory
from prototype.planner import Planner
from prototype.cli import CLI
from prototype.config import SettingsManager, get_settings_manager, reset_settings_manager
from prototype.provider import MockProvider, NVIDIAProvider, OpenRouterProvider, Provider

# ── Logging setup ─────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "session.log"),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("alfa.main")


# ── Provider factory ──────────────────────────────────────────────────────────


def create_provider(settings: SettingsManager) -> Provider:
    """Create a provider instance based on the current configuration."""
    name = settings.get_provider()
    if name == "nvidia":
        return NVIDIAProvider(settings)
    elif name == "openrouter":
        return OpenRouterProvider(settings)
    return MockProvider()


# ── Structured interaction logger ─────────────────────────────────────────────


def log_interaction(
    user_input: str,
    response: str,
    latency_ms: float,
    provider: str,
    error: Optional[str] = None,
) -> None:
    """Append a structured log entry — never includes API keys."""
    logger.info(
        "interaction user=%r provider=%s latency_ms=%.2f success=%s",
        user_input[:80],
        provider,
        latency_ms,
        error is None,
    )
    if error:
        logger.error("interaction_error: %s", error)


# ── Boot sequence ─────────────────────────────────────────────────────────────


def boot_sequence() -> None:
    print("=" * 40)
    print("  Alfa COS v0.1 — Boot Sequence")
    print("=" * 40)
    print()

    # Settings (single source of truth)
    reset_settings_manager()
    settings = get_settings_manager()

    # Components
    kernel = Kernel()
    context_manager = ContextManager()
    memory = Memory()
    planner = Planner()
    provider = create_provider(settings)
    cli = CLI()

    components = [
        ("Kernel", kernel),
        ("Context", context_manager),
        ("Memory", memory),
        ("Planner", planner),
        ("Provider", provider),
        ("CLI", cli),
    ]

    for name, component in components:
        component.load()
        print(f"[\u2713] {name} Loaded")

    # Wire dependencies
    kernel.set_dependencies(planner=planner, memory=memory, provider=provider)
    cli.set_dependencies(
        kernel=kernel,
        context_manager=context_manager,
        memory=memory,
        settings=settings,
    )

    provider_name = settings.get_provider()
    model_name = settings.get_model()
    print()
    print(f"Provider : {provider_name}")
    print(f"Model    : {model_name}")
    print()
    print("Alfa COS Ready.")
    print("Type 'help' for available commands.")
    print()

    logger.info(
        "boot provider=%s model=%s", provider_name, model_name
    )

    # ── Main loop ─────────────────────────────────────────────────────────

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                break

            # ── Settings commands (handled in main, not kernel) ───────────
            if _handle_settings_command(
                user_input, settings, kernel, planner, memory, context_manager, cli
            ):
                continue

            # ── Standard pipeline ─────────────────────────────────────────
            from prototype.common import Goal

            goal = Goal(name="USER_INPUT", parameters={"input": user_input})
            context = context_manager.build_context(goal=goal)

            start = time.time()
            result = kernel.process(user_input, context)
            latency_ms = (time.time() - start) * 1000

            if result.content:
                print(f"{result.content}")
            if latency_ms > 1.0:
                print(f"[{settings.get_provider()} | {latency_ms:.0f}ms]")
            if result.error:
                print(f"Error: {result.error}")

            log_interaction(
                user_input,
                result.content,
                latency_ms,
                settings.get_provider(),
                result.error if not result.success else None,
            )

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break
        except Exception as exc:
            logger.exception("Unhandled error in main loop")
            print(f"Error: {exc}")

    # ── Shutdown ──────────────────────────────────────────────────────────

    print()
    print("Shutting down...")
    for name, component in reversed(components):
        try:
            component.shutdown()
            print(f"[\u2713] {name} Shutdown")
        except Exception:
            logger.exception("Shutdown error for %s", name)

    print()
    print("Alfa COS Stopped.")
    logger.info("shutdown complete")


# ── Settings command dispatcher ───────────────────────────────────────────────


def _handle_settings_command(
    user_input: str,
    settings: SettingsManager,
    kernel: Kernel,
    planner,
    memory,
    context_manager,
    cli,
) -> bool:
    """Handle settings-related CLI commands. Returns True if handled."""
    parts = user_input.split()
    cmd = parts[0].lower()

    if cmd == "settings":
        config = settings.get_all()
        print("Current Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        return True

    if cmd == "provider":
        if len(parts) == 1:
            print(f"Current provider: {settings.get_provider()}")
            print("Available: mock, nvidia, openrouter")
        elif len(parts) == 2:
            name = parts[1].lower()
            try:
                settings.set_provider(name)
                print(f"Provider changed to: {name}")
                new_provider = create_provider(settings)
                new_provider.load()
                kernel.set_dependencies(
                    planner=planner, memory=memory, provider=new_provider
                )
                print(f"Model: {settings.get_model()}")
            except ValueError as exc:
                print(str(exc))
        else:
            print("Usage: provider [name]")
        return True

    if cmd == "model":
        if len(parts) == 1:
            print(f"Current model: {settings.get_model()}")
        elif len(parts) == 2:
            settings.set_model(parts[1])
            print(f"Model changed to: {parts[1]}")
        else:
            print("Usage: model [name]")
        return True

    if cmd == "apikey":
        if len(parts) == 2:
            settings.set_api_key(parts[1])
            print(f"API key set for {settings.get_provider()}")
            # Reload provider with new key
            new_provider = create_provider(settings)
            new_provider.load()
            kernel.set_dependencies(
                planner=planner, memory=memory, provider=new_provider
            )
            print("Provider reloaded.")
        else:
            print("Usage: apikey <key>")
        return True

    if cmd == "test":
        print("Testing connection...")
        result = settings.test_connection()
        if result["connected"]:
            print(f"[OK] Connected to {result['provider']}")
            print(f"Latency: {result['latency_ms']:.2f}ms")
        else:
            print(f"[FAIL] {result.get('error', 'Unknown error')}")
            if result.get("message"):
                print(f"Hint: {result['message']}")
        return True

    return False


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    boot_sequence()