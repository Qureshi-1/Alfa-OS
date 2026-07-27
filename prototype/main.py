#!/usr/bin/env python3
"""
Alfa COS — Cognitive Operating System Phase 2
Boot Sequence, Interactive CLI Loop, and Structured Logging
"""

import logging
import os
import sys
import time
from typing import Optional

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from prototype.config import get_settings_manager, reset_settings_manager
from prototype.runtime import AlfaRuntime

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
    print("=" * 50)
    print("  Alfa COS v1.0 — Cognitive Operating System")
    print("=" * 50)
    print()

    reset_settings_manager()
    settings = get_settings_manager()

    runtime = AlfaRuntime(settings=settings)
    runtime.load()

    print("[✓] Executive Controller Loaded")
    print("[✓] Decision Engine Loaded")
    print("[✓] Reflection Engine Loaded")
    print("[✓] Learning Engine Loaded")
    print("[✓] Memory Manager (Working + SQLite) Loaded")
    print("[✓] Tool Manager Loaded")
    print("[✓] Plugin Manager Loaded")
    print("[✓] Agent Runtime Loaded")
    print("[✓] CognitionRuntime Loaded (Perception → Planning → Reasoning → Execution → Reflection)")
    modelhub_count = len(runtime.model_registry.list_providers())
    print(f"[✓] ModelHub Loaded ({modelhub_count} providers)")
    print("[✓] Full Cognitive Pipeline Active")

    provider_name = runtime.provider_name
    model_name = settings.get_model()
    print()
    print(f"Provider : {provider_name}")
    print(f"Model    : {model_name}")
    print()
    print("Alfa COS v1.0 Ready.")
    print("Type 'help' for available commands or 'desktop' to launch PySide6 Desktop UI.")
    print()

    logger.info("boot provider=%s model=%s version=1.0", provider_name, model_name)

    # ── Main loop ─────────────────────────────────────────────────────────

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                break

            if user_input.lower() == "desktop":
                try:
                    from prototype.desktop import launch_desktop
                    print("Launching PySide6 Desktop Application...")
                    app, window = launch_desktop(runtime)
                    app.exec()
                except Exception as exc:
                    print(f"Error launching Desktop UI: {exc}")
                continue

            # Settings commands
            if _handle_settings_command(user_input, settings, runtime):
                continue

            start = time.time()
            result = runtime.process(user_input)
            latency_ms = (time.time() - start) * 1000

            if result.content:
                print(f"{result.content}")
            if latency_ms > 1.0:
                print(f"[{runtime.provider_name} | {latency_ms:.0f}ms]")
            if result.error:
                print(f"Error: {result.error}")

            log_interaction(
                user_input,
                result.content,
                latency_ms,
                runtime.provider_name,
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
    print("Shutting down Cognitive Core...")
    runtime.shutdown()
    print("[✓] Alfa COS Stopped.")
    logger.info("shutdown complete")


def _handle_settings_command(user_input: str, settings, runtime: AlfaRuntime) -> bool:
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
            print("Available: mock, nvidia, openrouter, ollama")
        elif len(parts) == 2:
            name = parts[1].lower()
            try:
                runtime.switch_provider(name)
                print(f"Provider changed to: {name}")
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
            runtime.switch_provider(settings.get_provider())
            print("Provider reloaded.")
        else:
            print("Usage: apikey <key>")
        return True

    if cmd == "test":
        print("Testing provider connection...")
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


if __name__ == "__main__":
    boot_sequence()