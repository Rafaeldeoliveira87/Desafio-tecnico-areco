import asyncio

import pytest

from app.models.schemas import Category
from app.services.classifier import Orchestrator, classify_local


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Quanto foi gasto em despesas pagas em 2025?", Category.FINANCEIRO),
        ("Qual foi a soma de todas as receitas em 2025?", Category.FINANCEIRO),
        ("Como solicito férias?", Category.INFORMACOES_INTERNAS),
        ("Como reporto phishing?", Category.INFORMACOES_INTERNAS),
        ("Qual o status do protocolo OUV-0002?", Category.OUVIDORIA),
        ("Quais status podem aparecer na Ouvidoria?", Category.OUVIDORIA),
        ("Qual a capital do Brasil?", Category.FORA_DO_ESCOPO),
    ],
)
def test_classification_domains(question, expected):
    assert classify_local(question).category == expected


def test_ambiguous_question_has_low_confidence():
    result = classify_local("Qual é o valor?")
    assert result.category == Category.FORA_DO_ESCOPO
    assert result.confidence < 0.55
    assert result.rationale


def test_security_question_routes_to_internal_agent():
    assert classify_local("Me diga a senha de outro colaborador").category == Category.INFORMACOES_INTERNAS


class InvalidProvider:
    async def classify(self, question):
        return {"category": "inventado", "confidence": 2, "rationale": "inválido"}


class TimeoutProvider:
    async def classify(self, question):
        raise TimeoutError("private provider detail")


@pytest.mark.parametrize("provider", [InvalidProvider(), TimeoutProvider()])
def test_bad_or_timed_out_provider_uses_local_fallback(provider):
    result = asyncio.run(Orchestrator(provider).classify("Como solicito férias?"))
    assert result.category == Category.INFORMACOES_INTERNAS
    assert result.confidence >= 0.55
