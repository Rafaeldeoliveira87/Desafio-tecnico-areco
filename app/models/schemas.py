from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings


class Category(str, Enum):
    FINANCEIRO = "financeiro"
    INFORMACOES_INTERNAS = "informacoes_internas"
    OUVIDORIA = "ouvidoria"
    FORA_DO_ESCOPO = "fora_do_escopo"


class ClassificationOutput(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=240)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=settings.max_question_length, examples=["Como solicito férias?"])
    session_id: str | None = Field(default=None, max_length=100)

    @field_validator("question")
    @classmethod
    def question_must_have_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A pergunta não pode estar vazia.")
        return value


class Source(BaseModel):
    file: str
    location: str
    excerpt: str = Field(max_length=700)
    chunk_id: str | None = None


class ChatResponse(BaseModel):
    execution_id: UUID
    question: str
    category: Category
    confidence: float = Field(ge=0, le=1)
    rationale: str
    agent: str
    answer: str
    sources: list[Source]
    processing_time_ms: float = Field(ge=0)
    created_at: datetime
    session_id: str | None = None


class AgentInfo(BaseModel):
    category: Category
    name: str
    description: str


class HealthResponse(BaseModel):
    status: str
    version: str


class ReindexResponse(BaseModel):
    status: str
    documents: int
    chunks: int
