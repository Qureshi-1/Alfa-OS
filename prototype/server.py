"""Small HTTP bridge used by the Alfa COS mobile client."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from prototype.runtime import AlfaRuntime

LOG_DIRECTORY = Path(__file__).resolve().parent.parent / "logs"
LOG_DIRECTORY.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(LOG_DIRECTORY / "session.log"),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("alfa.server")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)


class ChatResponse(BaseModel):
    reply: str
    success: bool
    error: str | None = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    runtime = AlfaRuntime()
    runtime.load()
    application.state.runtime = runtime
    logger.info("runtime started provider=%s", runtime.provider_name)
    yield
    runtime.shutdown()
    logger.info("runtime stopped")


app = FastAPI(title="Alfa COS API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    runtime: AlfaRuntime = app.state.runtime
    return {"status": "ok", "provider": runtime.provider_name}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    runtime: AlfaRuntime = app.state.runtime
    result = runtime.process(request.message)
    logger.info(
        "chat success=%s input_length=%d", result.success, len(request.message)
    )
    return ChatResponse(
        reply=result.content, success=result.success, error=result.error
    )
