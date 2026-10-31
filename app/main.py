from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import agents, chat, knowledge
from app.core.config import settings
from app.core.logging import configure_logging
from app.knowledge.indexing import build_index
from app.llm.factory import get_provider
from app.models.schemas import HealthResponse

configure_logging(settings.logs_dir)
logger = logging.getLogger("aurora.api")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.knowledge_chunks = build_index(
        settings.data_dir, settings.processed_dir, settings.chunk_size_chars, settings.chunk_overlap_chars
    )
    application.state.llm_provider = get_provider()
    yield


app = FastAPI(
    title="Agente de Conhecimento Areco",
    description="Orquestrador demonstrativo para Financeiro, Informações Internas e Ouvidoria.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"detail": "Entrada inválida. Confira os campos e limites informados."}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception", extra={"fields": {"path": request.url.path, "exception_type": type(exc).__name__}}
    )
    return JSONResponse(status_code=500, content={"detail": "Não foi possível processar a solicitação."})


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}
