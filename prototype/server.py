"""FastAPI REST Server for Alfa COS Cognitive Core.

Exposes REST APIs for Desktop, Mobile (Flutter), and external integrations.
All requests interact directly with the single source of truth: AlfaRuntime.
"""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from prototype.common import Goal, EngineResult
from prototype.config import get_settings_manager
from prototype.runtime import AlfaRuntime

LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "logs"
LOG_DIRECTORY.mkdir(exist_ok=True)
SESSION_LOG_PATH = LOG_DIRECTORY / "session.log"

logging.basicConfig(
    filename=str(SESSION_LOG_PATH),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("alfa.server")


# ── Pydantic Request / Response Schemas ────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    success: bool
    error: Optional[str] = None
    provider_used: str
    latency_ms: float = 0.0
    execution_id: Optional[str] = None


class GoalRequest(BaseModel):
    name: str = Field(min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    action: str = Field(default="create", description="create, cancel, or retry")
    name: str = Field(min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ExecuteRequest(BaseModel):
    action: str = Field(min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class WorkerExecuteRequest(BaseModel):
    worker_name: str = Field(min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class LearnRequest(BaseModel):
    insight: str = Field(min_length=1)
    source: str = Field(default="user_input")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ReflectionRequest(BaseModel):
    execution_id: str
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)


class ProviderSwitchRequest(BaseModel):
    provider: str = Field(min_length=1)


class PluginActionRequest(BaseModel):
    plugin_name: str = Field(min_length=1)


class SettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    memory_enabled: Optional[bool] = None
    logging_level: Optional[str] = None
    theme: Optional[str] = None


class MemoryClearRequest(BaseModel):
    target: str = Field(default="all", description="working, persistent, or all")


# ── Server Lifespan ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    runtime = AlfaRuntime()
    runtime.load()
    application.state.runtime = runtime
    logger.info("Alfa COS Server runtime v0.3.0 started with provider=%s", runtime.provider_name)
    yield
    runtime.shutdown()
    logger.info("Alfa COS Server runtime stopped")


app = FastAPI(
    title="Alfa COS API",
    description="Cognitive Operating System REST Backend",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception on %s: %s", request.url, exc, exc_info=True)
    return Response(
        content=json.dumps({"success": False, "error": f"Internal Server Error: {str(exc)}"}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json",
    )


def get_runtime() -> AlfaRuntime:
    runtime: AlfaRuntime = app.state.runtime
    return runtime


# ── Health & Status Endpoints ─────────────────────────────────────────────────

@app.get("/health")
@app.get("/healthz")
def healthcheck() -> Dict[str, Any]:
    runtime = get_runtime()
    return {
        "status": "ok",
        "provider": runtime.provider_name,
        "loaded": runtime._loaded,
        "version": "0.3.0",
    }


@app.get("/status")
def get_status() -> Dict[str, Any]:
    runtime = get_runtime()
    return runtime.get_stats()


@app.get("/logs")
def get_logs(lines: int = Query(default=100, ge=1, le=1000)) -> Dict[str, Any]:
    if not SESSION_LOG_PATH.exists():
        return {"logs": [], "total": 0}
    try:
        with open(SESSION_LOG_PATH, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.readlines()
        log_lines = [line.strip() for line in content[-lines:]]
        return {"logs": log_lines, "total": len(content)}
    except Exception as exc:
        logger.error("Error reading logs: %s", exc)
        return {"logs": [f"Error reading logs: {exc}"], "total": 0}


# ── Chat & Processing Endpoints ───────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    import time
    runtime = get_runtime()
    start_time = time.time()
    try:
        result = runtime.process(request.message)
        latency = round((time.time() - start_time) * 1000, 2)
        logger.info("Chat processed success=%s latency=%.2fms", result.success, latency)
        return ChatResponse(
            reply=result.content,
            success=result.success,
            error=result.error,
            provider_used=runtime.provider_name,
            latency_ms=latency,
            execution_id=getattr(result, "execution_id", None),
        )
    except Exception as exc:
        latency = round((time.time() - start_time) * 1000, 2)
        logger.error("Chat exception: %s", exc, exc_info=True)
        return ChatResponse(
            reply="",
            success=False,
            error=str(exc),
            provider_used=runtime.provider_name,
            latency_ms=latency,
        )


@app.post("/goal")
def post_goal(request: GoalRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    goal = Goal(name=request.name, parameters=request.parameters)
    context = runtime.context_manager.build_context(goal=goal)
    execution = runtime.executive.execute_goal(goal, context)
    return {
        "success": True,
        "execution_id": execution.execution_id,
        "goal_name": goal.name,
        "status": execution.status.value,
    }


@app.post("/task")
def post_task(request: TaskRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    if request.action == "cancel":
        cancelled = runtime.executive.cancel_execution(request.name)
        return {"success": cancelled, "action": "cancel", "execution_id": request.name}

    goal = Goal(name=request.name, parameters=request.parameters)
    context = runtime.context_manager.build_context(goal=goal)
    execution = runtime.executive.execute_goal(goal, context)
    return {
        "success": True,
        "action": "create",
        "execution_id": execution.execution_id,
        "status": execution.status.value,
    }


@app.get("/tasks/list")
def list_tasks() -> Dict[str, Any]:
    runtime = get_runtime()
    history = runtime.executive.get_execution_history()
    active = runtime.executive.get_active_executions()
    return {
        "active": [
            {
                "execution_id": ex.execution_id,
                "goal_name": ex.goal.name if ex.goal else "",
                "status": ex.status.value,
                "priority": ex.priority.name,
                "created_at": ex.created_at,
            }
            for ex in active
        ],
        "history": [
            {
                "execution_id": ex.execution_id,
                "goal_name": ex.goal.name if ex.goal else "",
                "status": ex.status.value,
                "priority": ex.priority.name,
                "completed_at": ex.completed_at,
                "error": ex.error,
            }
            for ex in history
        ],
        "stats": runtime.executive.get_stats(),
    }


@app.post("/execute")
def execute_action(request: ExecuteRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    if request.action in runtime.tool_manager.get_tool_names():
        res = runtime.tool_manager.execute(request.action, request.parameters)
        return {"success": res.success, "type": "tool", "result": str(res.result), "error": res.error}

    result = runtime.process(request.action)
    return {
        "success": result.success,
        "type": "pipeline",
        "result": result.content,
        "error": result.error,
    }


# ── Worker Framework Endpoints ────────────────────────────────────────────────

@app.get("/workers")
def get_workers() -> Dict[str, Any]:
    runtime = get_runtime()
    return {
        "workers": runtime.worker_manager.registry.list_workers(),
        "stats": runtime.worker_manager.get_stats(),
    }


@app.post("/workers/execute")
def execute_worker(request: WorkerExecuteRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    result = runtime.worker_manager.execute_worker(
        request.worker_name, request.parameters
    )
    return {
        "success": result.success,
        "task_id": result.task_id,
        "worker_name": result.worker_name,
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
    }


# ── Cognitive Reflection & Learning Endpoints ──────────────────────────────────

@app.post("/learn")
def post_learn(request: LearnRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    lesson = runtime.learning.learn(
        lesson_text=request.insight,
        source=request.source,
        confidence=request.confidence,
    )
    return {
        "success": True,
        "lesson_id": lesson.lesson_id,
        "insight": lesson.lesson,
    }


@app.post("/reflection")
def post_reflection(request: ReflectionRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    reflection = runtime.reflection.reflect(
        execution_id=request.execution_id,
        result=None,
        latency_ms=0.0,
        memory_used=False,
        goal_name="API_REFLECTION",
    )
    return {
        "success": True,
        "reflection_id": reflection.reflection_id,
        "quality_score": reflection.quality_score,
        "recommendations": reflection.recommendations,
    }


# ── Memory Endpoints ──────────────────────────────────────────────────────────

@app.get("/memory")
def get_memory() -> Dict[str, Any]:
    runtime = get_runtime()
    working_items = runtime.working_memory.get_working_memory()
    persistent_items = runtime.persistent_memory.list_all()
    return {
        "stats": runtime.memory_manager.get_stats(),
        "working_memory": [item.to_dict() if hasattr(item, "to_dict") else str(item) for item in working_items],
        "persistent_memory": [item.to_dict() if hasattr(item, "to_dict") else str(item) for item in persistent_items],
    }


@app.get("/memory/history")
def get_memory_history() -> Dict[str, Any]:
    runtime = get_runtime()
    working_items = runtime.working_memory.get_working_memory()
    history = []
    for item in working_items:
        if hasattr(item, "to_dict"):
            history.append(item.to_dict())
        else:
            history.append({"content": str(item)})
    return {"history": history, "count": len(history)}


@app.get("/memory/search")
def search_memory(query: str = Query(min_length=1)) -> Dict[str, Any]:
    runtime = get_runtime()
    results = runtime.memory_manager.recall(query, limit=20)
    formatted = [item.to_dict() if hasattr(item, "to_dict") else str(item) for item in results]
    return {"query": query, "results": formatted, "count": len(formatted)}


@app.post("/memory/clear")
def clear_memory(request: Optional[MemoryClearRequest] = None) -> Dict[str, Any]:
    runtime = get_runtime()
    target = request.target if request else "all"
    if target in ("working", "all"):
        runtime.working_memory.clear()
    if target in ("persistent", "all"):
        runtime.persistent_memory.clear()
    return {"success": True, "target_cleared": target}


# ── Provider Management Endpoints ─────────────────────────────────────────────

@app.get("/providers")
def get_providers() -> Dict[str, Any]:
    runtime = get_runtime()
    settings = get_settings_manager()
    conn_test = settings.test_connection()
    return {
        "active_provider": runtime.provider_name,
        "active_model": settings.get_model(),
        "valid_providers": ["mock", "nvidia", "openrouter", "ollama"],
        "connection_test": conn_test,
        "provider_config": settings.get_provider_config(),
    }


@app.post("/providers/switch")
def switch_provider(request: ProviderSwitchRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    valid = ("mock", "nvidia", "openrouter", "ollama")
    if request.provider not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{request.provider}'. Valid providers: {', '.join(valid)}",
        )
    try:
        runtime.switch_provider(request.provider)
        return {
            "success": True,
            "provider": runtime.provider_name,
            "model": runtime._settings.get_model(),
        }
    except Exception as exc:
        logger.error("Provider switch failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Plugin & Tool Management Endpoints ─────────────────────────────────────────

@app.get("/plugins")
def get_plugins() -> Dict[str, Any]:
    runtime = get_runtime()
    return {
        "plugins": runtime.plugin_manager.list_plugins(),
        "tools": runtime.tool_manager.list_tools(),
    }


@app.post("/plugins/enable")
def enable_plugin(request: PluginActionRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    res = runtime.plugin_manager.enable(request.plugin_name)
    return {"success": res, "plugin": request.plugin_name, "enabled": True}


@app.post("/plugins/disable")
def disable_plugin(request: PluginActionRequest) -> Dict[str, Any]:
    runtime = get_runtime()
    res = runtime.plugin_manager.disable(request.plugin_name)
    return {"success": res, "plugin": request.plugin_name, "enabled": False}


@app.post("/plugins/reload")
def reload_plugins() -> Dict[str, Any]:
    runtime = get_runtime()
    runtime.plugin_manager.load()
    return {"success": True, "plugins": runtime.plugin_manager.list_plugins()}


# ── Configuration & Settings Endpoints ────────────────────────────────────────

@app.get("/settings")
def get_settings() -> Dict[str, Any]:
    settings = get_settings_manager()
    return settings.get_all()


@app.post("/settings")
def update_settings(request: SettingsUpdateRequest) -> Dict[str, Any]:
    settings = get_settings_manager()
    runtime = get_runtime()

    if request.provider is not None:
        runtime.switch_provider(request.provider)

    if request.model is not None:
        settings.set_model(request.model)

    if request.temperature is not None:
        settings.set("temperature", request.temperature)

    if request.max_tokens is not None:
        settings.set("max_tokens", request.max_tokens)

    if request.api_key is not None and request.api_key.strip():
        settings.set_api_key(request.api_key.strip())

    if request.openrouter_api_key is not None and request.openrouter_api_key.strip():
        settings.set("openrouter_api_key", request.openrouter_api_key.strip())

    if request.openrouter_model is not None:
        settings.set("openrouter_model", request.openrouter_model)

    if request.ollama_model is not None:
        settings.set("ollama_model", request.ollama_model)

    if request.ollama_base_url is not None:
        settings.set("ollama_base_url", request.ollama_base_url)

    if request.memory_enabled is not None:
        settings.set("memory_enabled", request.memory_enabled)

    if request.logging_level is not None:
        settings.set("logging_level", request.logging_level)

    if request.theme is not None:
        settings.set("theme", request.theme)

    settings.save()
    return {"success": True, "settings": settings.get_all()}
