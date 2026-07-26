# Alfa COS v0.3 — Artificial Cognitive Operating System

A modular, production-ready Artificial Cognitive Operating System with an Executive Controller, Decision Engine, Reflection Engine, Learning Engine, Persistent SQLite Memory Manager, Tool & Plugin Frameworks, Worker Framework, interchangeable LLM providers (Mock, NVIDIA, OpenRouter, Ollama), PySide6 Desktop Developer Client, and Flutter Android Client.

---

## Cognitive Architecture

```
                                USER / CLIENTS
                           (Desktop PySide6 | Android Flutter)
                                        │
                                        ▼
                                  Input Layer
                                        │
                                 Context Builder
                                        │
                                Goal Interpreter
                                        │
                              Executive Controller
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
          Attention              Working Memory             Event Bus
                │                       │                       │
                └───────────────────────┼───────────────────────┘
                                        │
                                 Decision Engine
                                        │
                                 Reasoning Engine
                                        │
                                 Planning Engine
                                        │
                               Tool Execution Manager
                                        │
                                 Worker Framework
                                        │
                                Reflection Engine
                                        │
                                 Learning Engine
                                        │
                       Memory Manager (SQLite + Working)
                                        │
                                Response Builder
                                        │
                                        ▼
                                  Response Output
```

All components are compositionally wired and managed through the **AlfaRuntime** root.

---

## Module Map

| Module | Path | Purpose |
|--------|------|---------|
| **Kernel** | `prototype/kernel/` | Execution coordinator — routes requests through the pipeline |
| **Executive Controller** | `prototype/executive/` | Manages cognitive execution, task scheduling, retries, and recovery |
| **Decision Engine** | `prototype/decision/` | Evaluates cognitive state and selects optimal next actions |
| **Reflection Engine** | `prototype/reflection/` | Post-execution evaluation, quality scoring, and recommendation generation |
| **Learning Engine** | `prototype/learning/` | Foundation storage for insights and lessons from reflections |
| **Memory Manager** | `prototype/memory/` | Unified interface over working memory and SQLite persistent memory |
| **Persistent Memory** | `prototype/memory/persistent_memory.py` | SQLite backend for long-term episodic/semantic memories |
| **Planner** | `prototype/planner/` | Classifies goals and generates execution steps |
| **Providers** | `prototype/provider/` | Abstract `Provider` interface + Mock, NVIDIA, OpenRouter, Ollama |
| **Tool Framework** | `prototype/tools/` | Tool registry, built-in tools (calculator, datetime, system_info) |
| **Plugin Framework** | `prototype/plugins/` | Dynamic plugin discovery, lifecycle, permissions, and tool extensions |
| **Worker Framework** | `prototype/worker/` | Permanent background worker infrastructure with FIFO scheduler & validation worker |
| **Config** | `prototype/config/` | Single source of truth settings manager with `config.json` persistence |
| **Context** | `prototype/context/` | Builds execution context for each turn |
| **Desktop Client** | `prototype/desktop/` | PySide6 Developer GUI (Chat, Memory, Inspector, Tasks, Logs, Settings, Providers, Plugins, Timeline) |
| **Android Client** | `android/` | Flutter mobile client reusing Cognitive Core APIs |
| **Server** | `prototype/server.py` | FastAPI HTTP bridge for clients |
| **Runtime** | `prototype/runtime/` | Composition Root wiring all cognitive subsystems |

---id Client** | `android/` | Flutter mobile client reusing Cognitive Core APIs |
| **Server** | `prototype/server.py` | FastAPI HTTP bridge for clients |
| **Runtime** | `prototype/runtime/` | Phase 2 Composition Root wiring all subsystems |

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- Flutter SDK 3.18+ (for Android builds)
- Android SDK 29+ (for Android APK generation)

### Installation
```bash
# Clone the repository
git clone https://github.com/Qureshi-1/Alfa-OS.git
cd Alfa-OS

# Install Python dependencies
pip install -r requirements.txt

# Install Android Flutter dependencies
cd android
flutter pub get
cd ..
```

---

## Running Locally

```bash
# Interactive CLI
python -m prototype.main

# PySide6 Desktop Application
python -m prototype.desktop.main_window

# FastAPI HTTP Server (for Mobile Client connection)
uvicorn prototype.server:app --reload --host 0.0.0.0 --port 8000
```

---

## Building Desktop Application

### Windows Standalone Executable
```cmd
cmd /c build_windows.bat
# Output: release/desktop/AlfaDesktop.exe
```

### Linux Standalone Executable
```bash
chmod +x build_linux.sh
./build_linux.sh
# Output: release/desktop/AlfaDesktop-linux
```

### Manual PyInstaller Build
```bash
python -m PyInstaller --clean alfa_desktop.spec
```

---

## Building Android Application

### Automated Build (APK + AppBundle)
```cmd
# Windows
cmd /c build_android.bat

# Linux / macOS
chmod +x build_android.sh
./build_android.sh
```

### Manual Flutter Build
```bash
cd android
flutter pub get
flutter analyze
flutter test
flutter build apk --release
flutter build appbundle --release
```

Output location:
- APK: `release/android/alfa-cos-mobile.apk`
- AppBundle: `release/android/alfa-cos-mobile.aab`

---

## Testing

```bash
# Run complete Python test suite (107 tests)
python -m pytest tests/ -v

# Run Flutter mobile unit and widget tests
cd android
flutter test
cd ..
```

---

## Developer Setup & Architecture Rules

1. **Single Source of Truth Configuration**: All settings are stored in `prototype/config/config.json`. API keys are never logged or stored in environment variables.
2. **Strict Layer Isolation**: Business logic belongs **only** inside the Cognitive Core (`prototype/`). Desktop (PySide6) and Mobile (Flutter) clients must **never** contain business logic.
3. **No Direct Database Access**: All memory operations pass through `MemoryManager`.
4. **Interchangeable Providers**: All providers inherit from `Provider` (ABC) in `api_provider.py`. Switching providers requires zero architecture changes.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `PySide6` display issues on Linux | Headless environment missing X11/Wayland | Run with `QT_QPA_PLATFORM=offscreen python -m pytest tests/` |
| Ollama provider fails | Local Ollama daemon not running | Ensure `ollama serve` is running at `http://localhost:11434` |
| Android API connection error | Emulator using localhost | Ensure Android uses `http://10.0.2.2:8000` to connect to host |
| `config.json` corrupted | Invalid JSON manual edits | Delete `prototype/config/config.json` — it auto-resets on next launch |

---

## Release Process

Full release artifacts are generated inside `release/`:
- `release/desktop/AlfaDesktop.exe` — Windows PySide6 standalone executable
- `release/android/alfa-cos-mobile.apk` — Production Android APK
- `release/android/alfa-cos-mobile.aab` — Production Android AppBundle

CI/CD is automated via GitHub Actions in `.github/workflows/desktop.yml` and `.github/workflows/android.yml`.

---

## License

Alfa COS Production Release.


