from __future__ import annotations

import re
import unicodedata
import logging
from dataclasses import dataclass

from app.core.config import settings
from app.models.schemas import Category, ClassificationOutput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Classification:
    category: Category
    confidence: float
    rationale: str


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def _contains(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def classify_local(question: str) -> Classification:
    q = _normalize(question)
    if not q.strip():
        return Classification(Category.FORA_DO_ESCOPO, 0.0, "A pergunta está vazia.")

    # Protocolo é identificador inequívoco do domínio Ouvidoria.
    if re.search(r"\bouv[- ]?\d{4}\b", q):
        return Classification(Category.OUVIDORIA, 0.99, "A pergunta contém um protocolo de Ouvidoria.")

    if re.search(r"\bcc\s?-?\d{3}\b", q):
        return Classification(Category.FINANCEIRO, 0.90, "A pergunta cita um centro de custo (CCnnn).")

    groups = {
        Category.OUVIDORIA: {
            "ouvidoria": 0.82,
            "manifestacao": 0.82,
            "reclamacao": 0.82,
            "protocolo": 0.78,
            "denuncia": 0.80,
            "manifestacoes": 0.82,
        },
        Category.FINANCEIRO: {
            "orcamento": 0.84,
            "orcamentos": 0.84,
            "receita": 0.83,
            "receitas": 0.83,
            "despesa": 0.78,
            "despesas": 0.78,
            "gasto": 0.78,
            "gastos": 0.78,
            "lancamento": 0.76,
            "lancamentos": 0.76,
            "financeiro": 0.73,
            "inadimplencia": 0.80,
            "execucao orcamentaria": 0.88,
            "centro de custo": 0.84,
            "faturamento": 0.82,
            "gastou": 0.78,
            "gastamos": 0.78,
            "gastei": 0.78,
            "custo": 0.74,
            "custos": 0.74,
            "inadimplente": 0.80,
        },
        Category.INFORMACOES_INTERNAS: {
            "ferias": 0.82,
            "reembolso": 0.82,
            "compra": 0.80,
            "compras": 0.80,
            "aprovacao": 0.78,
            "phishing": 0.84,
            "senha": 0.84,
            "credencial": 0.84,
            "acesso": 0.76,
            "incidente": 0.80,
            "home office": 0.82,
            "privacidade": 0.80,
            "holerite": 0.82,
            "politica": 0.74,
            "procedimento": 0.76,
            "colaborador": 0.73,
            "seguranca": 0.78,
            "trabalho remoto": 0.80,
        },
    }
    scores: dict[Category, float] = {}
    matched: dict[Category, list[str]] = {}
    for category, phrases in groups.items():
        hits = [phrase for phrase, weight in phrases.items() if _contains(q, _normalize(phrase))]
        if hits:
            matched[category] = hits
            scores[category] = min(0.98, max(phrases[hit] for hit in hits) + min(0.10, (len(hits) - 1) * 0.025))

    if not scores:
        unrelated = (
            "capital do brasil",
            "previsao do tempo",
            "receita de bolo",
            "futebol",
            "filme",
            "musica",
            "astronomia",
        )
        if any(term in q for term in unrelated):
            return Classification(Category.FORA_DO_ESCOPO, 0.92, "O assunto não pertence aos três domínios atendidos.")
        return Classification(
            Category.FORA_DO_ESCOPO, 0.35, "Não há sinais suficientes para identificar um dos três domínios."
        )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_category, best_score = ranked[0]
    if len(ranked) > 1 and best_score - ranked[1][1] < 0.10:
        tie_break = _break_tie(q, ranked[0][0], ranked[1][0], matched)
        if tie_break is not None:
            return tie_break
        return Classification(
            Category.FORA_DO_ESCOPO, 0.30, "A pergunta mistura domínios; indique qual informação deseja consultar."
        )
    rationale = "Sinais encontrados: " + ", ".join(matched[best_category][:3]) + "."
    return Classification(best_category, round(best_score, 2), rationale)


_PROCEDURE_CUES = (
    "como",
    "posso",
    "preciso",
    "quero",
    "prazo",
    "regra",
    "politica",
    "documento",
    "quem aprova",
    "o que fazer",
)
_QUANT_CUES = ("quanto", "quantos", "quantas", "total", "soma", "media", "valor", "maior", "menor", "por departamento")


def _break_tie(q: str, first: Category, second: Category, matched: dict[Category, list[str]]) -> Classification | None:
    """Desempata Interno x Financeiro (ex.: "reembolso de despesa de viagem") pela intenção da frase."""
    if {first, second} != {Category.INFORMACOES_INTERNAS, Category.FINANCEIRO}:
        return None
    asks_quantity = any(_contains(q, cue) for cue in _QUANT_CUES)
    asks_procedure = any(_contains(q, cue) for cue in _PROCEDURE_CUES)
    if asks_procedure and not asks_quantity:
        category = Category.INFORMACOES_INTERNAS
    elif asks_quantity and not asks_procedure:
        category = Category.FINANCEIRO
    else:
        return None
    return Classification(
        category,
        0.66,
        "Pergunta com sinais de dois domínios; desempate pela intenção (procedimento x consulta de valores): "
        + ", ".join(matched[category][:3])
        + ".",
    )


class Orchestrator:
    def __init__(self, provider=None):
        self.provider = provider

    async def classify(self, question: str) -> Classification:
        if self.provider is not None:
            try:
                output = await self.provider.classify(question)
                validated = ClassificationOutput.model_validate(output)
                return Classification(validated.category, validated.confidence, validated.rationale)
            except Exception as exc:
                # Provider failures are intentionally non-fatal; no provider details reach the user.
                logger.warning("classifier_provider_fallback", extra={"fields": {"error_type": type(exc).__name__}})
        return classify_local(question)


def confidence_threshold() -> float:
    return settings.confidence_threshold
