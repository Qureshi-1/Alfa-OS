# Alfa COS v0.1 — Cognitive Operating System

A modular, conversational AI operating system with pluggable LLM providers, an internal settings system, structured logging, and an extensible memory engine.

---

## Architecture

```
User Input
    │
    ▼
  Kernel  ◄── GoalInterpreter (classifies commands vs. conversation)
    │
    ├──► Planner        (classifies action type)
    ├──► Memory         (remember / recall / forget / list / clear)
    ├──► Provider       (MockProvider │ NVIDIAProvider │ OpenRouterProvider)
    │
    ▼
  Response
    │
    ▼
  Logging   (structured, API-key-safe session.log)
```

All components are loaded, wired, and shut down through the **Kernel**. The CLI and HTTP server both use the same `AlfaRuntime` composition root.

### Module Map

| Module | Path | Purpose |
|--------|------|---------|
| **Kernel** | `prototype/kernel/` | Central orchestrator — routes input through the pipeline |
| **GoalInterpreter** | `prototype/kernel/goal_interpreter.py` | Classifies user input into goals (REMEMBER, RECALL, EXIT, etc.) |
| **Planner** | `prototype/planner/` | Classifies goals into action types (memory, conversation, control) |
| **Memory** | `prototype/memory/` | Working + long-term episodic memory with keyword search |
| **Provider** | `prototype/provider/` | Abstract `Provider` base + Mock, NVIDIA, OpenRouter implementations |
| **Config** | `prototype/config/` | Single-source settings manager with JSON persistence |
| **Context** | `prototype/context/` | Builds execution context for each request |
| **CLI** | `prototype/cli/` | Interactive terminal interface |
| **Runtime** | `prototype/runtime.py` | Composition root for CLI and HTTP API |
| **Server** | `prototype/server.py` | FastAPI HTTP bridge for mobile/web clients |
| **Common** | `prototype/common/` | Shared data types, event bus |

---

## Providers

### Mock Provider
- No external dependencies or API keys required
- Returns canned responses for testing the full pipeline
- Answers memory-backed questions ("What is my name?")

### NVIDIA Provider
- Connects to NVIDIA Build (`integrate.api.nvidia.com/v1`)
- Uses the `openai` Python SDK
- Supports streaming with automatic fallback to non-streaming
- Automatic retry with exponential backoff (configurable)
- Auth errors (401/403) fail fast without retrying

### OpenRouter Provider
- Connects to OpenRouter (`openrouter.ai`)
- Uses `urllib` (no extra dependencies beyond stdlib)
- SSE streaming with fallback
- Rate-limit detection (429)
- Automatic retry with backoff

### Provider Abstraction
All providers inherit from `Provider` (ABC) in `api_provider.py`:
```python
class Provider(ABC):
    def load(self) -> None: ...
    def generate(self, prompt: str) -> EngineResult: ...
    def stream(self, prompt: str) -> Iterator[str]: ...
    def shutdown(self) -> None: ...
```

---

## Settings System

**No Windows environment variables required.** All configuration is stored internally in `prototype/config/config.json`.

### Configuration Keys

| Key | Default | Description |
|-----|---------|-------------|
| `provider` | `mock` | Active provider: `mock`, `nvidia`, `openrouter` |
| `model` | `z-ai/glm-5.2` | Model for NVIDIA provider |
| `openrouter_model` | `qwen/qwen3-32b` | Model for OpenRouter provider |
| `temperature` | `0.7` | Generation temperature |
| `max_tokens` | `4096` | Max response tokens |
| `timeout` | `30` | Request timeout in seconds |
| `api_key` | `""` | NVIDIA API key |
| `openrouter_api_key` | `""` | OpenRouter API key |
| `max_retries` | `3` | Retry count for failed requests |
| `retry_delay` | `1.0` | Base retry delay in seconds |

### Runtime Commands

```
provider [name]  — Show or change provider (mock/nvidia/openrouter)
model [name]     — Show or change model
apikey <key>     — Set API key for the current provider
settings         — Show all settings (API keys masked)
test             — Test provider connectivity
```

### Security
- API keys are **never logged**
- `settings` command masks keys: `***cdef`
- `get_all()` always returns masked values

### Migration
On first run, if environment variables (e.g. `ALFA_NVIDIA_API_KEY`) are set, they are migrated into `config.json` once. After that, `config.json` is the sole authority.

---

## Memory

In-process episodic memory with keyword-based recall.

| Command | Action |
|---------|--------|
| `remember <text>` | Store a memory |
| `recall <query>` | Search memories by keyword |
| `list` | List all memories |
| `forget <id>` | Delete a memory by ID prefix |
| `clear` | Delete all memories |
| `history` | Alias for list |

Memory commands **bypass the LLM** — they are handled directly by the Kernel.

---

## Logging

Structured logging to `logs/session.log`:

```
2026-07-22 10:30:00 INFO alfa.main interaction user='hello' provider=mock latency_ms=0.12 success=True
2026-07-22 10:30:00 INFO alfa.kernel Memory stored: id=abc12345
2026-07-22 10:30:01 WARNING alfa.provider.nvidia NVIDIA attempt 1 failed, retrying in 1.0s: timeout
```

Fields logged:
- Timestamps (ISO 8601)
- User input (truncated to 80 chars)
- Assistant response length
- Provider name
- Latency (ms)
- Errors and warnings
- **Never** API keys

---

## Startup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m prototype.main

# Run the HTTP server
uvicorn prototype.server:app --reload
```

### Boot Sequence
1. Load `SettingsManager` from `config.json`
2. Create components (Kernel, Context, Memory, Planner, Provider, CLI)
3. Call `.load()` on each component
4. Wire dependencies via `kernel.set_dependencies()`
5. Enter interactive loop

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Quick run
python -m pytest -q
```

### Test Coverage

| Test Class | Tests | Covers |
|-----------|-------|--------|
| `TestSettingsManager` | 12 | Defaults, persistence, masking, provider config, validation |
| `TestGoalInterpreter` | 9 | All command types + freeform |
| `TestMemory` | 6 | CRUD, search, clear |
| `TestPlanner` | 2 | Action classification |
| `TestMockProvider` | 4 | Generate, stream, lifecycle |
| `TestKernel` | 8 | Full pipeline, memory integration, edge cases |
| `TestContextManager` | 2 | Build and clear |
| `TestRuntime` | 2 | Process and memory via runtime |
| `TestEventBus` | 2 | Pub/sub and unsubscribe |
| `TestProviderAbstraction` | 2 | ABC enforcement, isinstance |

**Total: 49 tests, all passing.**

---

## Error Handling

The system **never crashes**. All errors are caught and returned as `EngineResult(success=False, error="...")`:

| Error | Handling |
|-------|----------|
| Missing API key | Returned immediately, no retry |
| Invalid provider | `ValueError` caught at settings level |
| Auth failure (401/403) | Fast fail, no retry |
| Timeout | Retry with backoff |
| Network failure | Retry with backoff |
| Streaming failure | Automatic fallback to non-streaming |
| JSON parse error | Caught, returned as error |
| Empty response | Returned as error |
| Rate limit (429) | Retry with backoff, logged as warning |
| Corrupt config.json | Reset to defaults |
| Any unhandled exception | Caught in main loop, logged |

---

## Future Extension Points

### For v0.2

1. **Persistent Memory** — SQLite or file-based storage for memories that survive restarts
2. **Conversation History** — Track multi-turn conversations with context window management
3. **Android Support** — The settings system is designed with no OS-specific dependencies; `config.json` works on any platform
4. **Plugin System** — The `Provider` ABC and event bus enable third-party extensions
5. **Multi-Agent** — The `Agent` data type and event bus are scaffolded for agent-to-agent communication
6. **Tool Use** — The `Tool` data type is defined for future function-calling support
7. **Security / Policy Layer** — `SecurityCheck` and `PolicyCheck` types are defined for future guardrails
8. **WebSocket Streaming** — Server-side streaming via WebSocket for the mobile client
9. **User Authentication** — Session management for multi-user deployments
10. **Metrics Dashboard** — Latency, token usage, and error rate tracking

---

## License

Internal prototype — not for distribution.
