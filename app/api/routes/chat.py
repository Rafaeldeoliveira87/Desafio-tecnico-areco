from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Request

from app.agents.orchestrator import AgentOrchestrator
from app.core.config import settings
from app.core.logging import log_execution
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
logger = logging.getLogger("aurora.execution")


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={422: {"description": "Pergunta inválida"}, 500: {"description": "Falha controlada"}},
)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    started = time.perf_counter()
    created_at = datetime.now(timezone.utc)
    execution_id = uuid4()
    chunks = request.app.state.knowledge_chunks
    provider = request.app.state.llm_provider
    orchestrator = AgentOrchestrator(settings.data_dir, chunks, provider)
    question_hash = hashlib.sha256(payload.question.encode("utf-8")).hexdigest()
    try:
        result = await orchestrator.answer(payload.question)
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        log_execution(
            logger,
            execution_id=str(execution_id),
            session_id_hash=hashlib.sha256(payload.session_id.encode()).hexdigest()[:16]
            if payload.session_id
            else None,
            question_sha256=question_hash,
            question_length=len(payload.question),
            category=result.classification.category.value,
            confidence=result.classification.confidence,
            rationale=result.classification.rationale,
            agent=result.agent,
            documents=[
                {"file": source.file, "location": source.location, "chunk_id": source.chunk_id}
                for source in result.sources
            ],
            duration_ms=elapsed,
            status=result.status,
        )
        return ChatResponse(
            execution_id=execution_id,
            question=payload.question,
            category=result.classification.category,
            confidence=result.classification.confidence,
            rationale=result.classification.rationale,
            agent=result.agent,
            answer=result.answer,
            sources=result.sources,
            processing_time_ms=elapsed,
            created_at=created_at,
            session_id=payload.session_id,
        )
    except Exception as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        log_execution(
            logger,
            execution_id=str(execution_id),
            question_sha256=question_hash,
            question_length=len(payload.question),
            duration_ms=elapsed,
            status="error",
            error_type=type(exc).__name__,
        )
        return ChatResponse(
            execution_id=execution_id,
            question=payload.question,
            category="fora_do_escopo",
            confidence=0,
            rationale="A execução encontrou uma falha controlada.",
            agent="orchestrator",
            answer="Não foi possível processar a solicitação agora. Tente novamente.",
            sources=[],
            processing_time_ms=elapsed,
            created_at=created_at,
            session_id=payload.session_id,
        )
