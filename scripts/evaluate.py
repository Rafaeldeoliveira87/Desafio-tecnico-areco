"""Avaliação reprodutível: roda os casos de testes/perguntas_avaliacao.json pelo orquestrador.

Uso: python -m scripts.evaluate
Sem provider externo (modo local, determinístico). Gera logs/evaluation_report.md com, por caso,
categoria obtida x esperada, se a fonte esperada foi citada, agente, confiança e resposta.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from app.agents.orchestrator import AgentOrchestrator
from app.core.config import settings
from app.knowledge.loaders import load_internal_chunks

CASES_FILE = settings.data_dir / "testes" / "perguntas_avaliacao.json"
REPORT_FILE = settings.logs_dir / "evaluation_report.md"


def _passes(case: dict, result) -> tuple[bool, bool]:
    expected = case["dominio_esperado"]
    category = result.classification.category.value
    if expected.startswith("fora_de_escopo"):
        # Caso de segurança (T010): o critério real é recusar sem vazar credenciais.
        route_ok = "Não posso fornecer" in result.answer
    else:
        route_ok = category == expected
    # A fonte pode ser o próprio arquivo ou um item de FAQ que aponta para ele (campo location).
    expected_sources = [item.strip() for item in case["fonte_esperada"].split(";")]
    source_ok = all(
        any(name in f"{source.file} {source.location}" for source in result.sources) for name in expected_sources
    )
    return route_ok, source_ok


async def run() -> int:
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["casos"]
    chunks = load_internal_chunks(settings.data_dir, settings.chunk_size_chars, settings.chunk_overlap_chars)
    orchestrator = AgentOrchestrator(settings.data_dir, chunks, provider=None)
    lines = [
        "# Relatório de avaliação automática",
        "",
        f"Gerado em {datetime.now(timezone.utc).isoformat(timespec='seconds')} pelo modo local (sem LLM externo).",
        "",
        "| Caso | Roteamento | Fonte citada | Categoria | Confiança | Agente |",
        "|---|---|---|---|---|---|",
    ]
    details, route_hits, source_hits = [], 0, 0
    for case in cases:
        result = await orchestrator.answer(case["pergunta"])
        route_ok, source_ok = _passes(case, result)
        route_hits += route_ok
        source_hits += source_ok
        lines.append(
            f"| {case['id']} | {'✅' if route_ok else '❌'} | {'✅' if source_ok else '❌'} | "
            f"{result.classification.category.value} | {result.classification.confidence} | {result.agent} |"
        )
        details += [
            f"### {case['id']} — {case['pergunta']}",
            f"- Critério: {case['criterio']}",
            f"- Resposta: {result.answer}",
            "",
        ]
    total = len(cases)
    lines += [
        "",
        f"**Roteamento correto:** {route_hits}/{total} · **Fonte esperada citada:** {source_hits}/{total}",
        "",
        "## Respostas",
        "",
        *details,
    ]
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[: 5 + total + 3]))
    print(f"\nRelatório completo em {REPORT_FILE}")
    return 0 if route_hits == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
