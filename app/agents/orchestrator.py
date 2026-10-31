from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.agents.financial import FinancialAgent
from app.agents.internal_information import InternalInformationAgent
from app.agents.ombudsman import OmbudsmanAgent
from app.core.config import settings
from app.core.exceptions import InsufficientEvidence
from app.knowledge.models import KnowledgeChunk
from app.llm.base import LLMProvider
from app.models.schemas import Category, Source
from app.services.classifier import Classification, Orchestrator as ClassifierOrchestrator


@dataclass(frozen=True)
class AgentResponse:
    classification: Classification
    agent: str
    answer: str
    sources: list[Source]
    status: str


class AgentOrchestrator:
    def __init__(self, data_dir: Path, chunks: list[KnowledgeChunk], provider: LLMProvider | None = None):
        self.classifier = ClassifierOrchestrator(provider)
        self.agents = {
            Category.FINANCEIRO: FinancialAgent(data_dir),
            Category.INFORMACOES_INTERNAS: InternalInformationAgent(chunks, provider),
            Category.OUVIDORIA: OmbudsmanAgent(data_dir),
        }

    async def answer(self, question: str) -> AgentResponse:
        classification = await self.classifier.classify(question)
        if classification.confidence < settings.confidence_threshold:
            return AgentResponse(
                classification,
                "orchestrator",
                "Não consegui identificar com segurança o domínio. Pode esclarecer se a pergunta é sobre Financeiro, Informações Internas ou Ouvidoria?",
                [],
                "clarification",
            )
        agent = self.agents.get(classification.category)
        if agent is None:
            return AgentResponse(
                classification,
                "orchestrator",
                "Este assistente atende apenas Financeiro, Informações Internas e Ouvidoria. Reformule a pergunta dentro de um desses domínios.",
                [],
                "out_of_scope",
            )
        try:
            answer, sources = await agent.answer(question)
            return AgentResponse(classification, agent.__class__.__name__, answer, sources, "ok")
        except InsufficientEvidence as exc:
            return AgentResponse(classification, agent.__class__.__name__, str(exc), [], "insufficient_evidence")
