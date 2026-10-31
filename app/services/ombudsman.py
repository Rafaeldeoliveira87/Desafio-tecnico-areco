from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from app.core.exceptions import InsufficientEvidence
from app.models.schemas import Source
from app.services.classifier import _normalize


def answer_ombudsman(question: str, data_dir: Path) -> tuple[str, list[Source]]:
    q = _normalize(question)
    csv_path = data_dir / "ouvidoria" / "manifestacoes.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    protocol_match = re.search(r"\bouv[- ]?\d{4}\b", q)
    if protocol_match:
        protocol = protocol_match.group(0).replace(" ", "-").upper()
        row = next((item for item in rows if item["protocolo"] == protocol), None)
        if row is None:
            return f"Não encontrei o protocolo {protocol} na base fornecida.", [
                Source(
                    file="ouvidoria/manifestacoes.csv",
                    location=protocol,
                    excerpt="Consulta exata sem correspondência na base sintética.",
                )
            ]
        answer = f"Protocolo {protocol}: status {row['status']}; categoria {row['categoria']}; prioridade {row['prioridade']}; aberto em {row['data_abertura']}."
        if row.get("data_resposta"):
            answer += f" Respondido em {row['data_resposta']}."
        answer += " A base contém dados sintéticos."
        source = Source(
            file="ouvidoria/manifestacoes.csv",
            location=protocol,
            excerpt=f"{protocol}: status={row['status']}; categoria={row['categoria']}; prioridade={row['prioridade']}; data_abertura={row['data_abertura']}; data_resposta={row.get('data_resposta') or 'sem resposta registrada'}.",
        )
        return answer, [source]

    reference = json.loads((data_dir / "ouvidoria" / "referencia_ouvidoria.json").read_text(encoding="utf-8"))
    for key, label in (
        ("status_validos", "status"),
        ("categorias", "categorias"),
        ("prioridades_validas", "prioridades"),
    ):
        if label in q or (label == "status" and "situacoes" in q):
            values = reference[key]
            return f"{label.capitalize()} disponíveis: " + ", ".join(values) + ".", [
                Source(
                    file="ouvidoria/referencia_ouvidoria.json",
                    location=key,
                    excerpt=f"Valores enumerados: {', '.join(values)}.",
                )
            ]

    if any(term in q for term in ("abrir", "registrar", "criar", "enviar manifestacao", "fazer reclamacao")):
        return (
            "Esta aplicação consulta a base sintética e não abre nem registra novas manifestações. Use o canal oficial da empresa para essa ação.",
            [
                Source(
                    file="ouvidoria/referencia_ouvidoria.json",
                    location="limites do sistema",
                    excerpt="A base fornecida permite consultas; não há integração para criar manifestações.",
                )
            ],
        )

    status = next((value for value in reference["status_validos"] if _normalize(value) in q), None)
    if status and any(word in q for word in ("quantas", "quantos", "listar", "consultar", "manifestacoes")):
        matches = [row for row in rows if row["status"] == status]
        return f"Há {len(matches)} manifestações com status '{status}' na base sintética.", [
            Source(
                file="ouvidoria/manifestacoes.csv",
                location=f"status={status}",
                excerpt=f"Contagem exata: {len(matches)} de {len(rows)} registros.",
            )
        ]
    raise InsufficientEvidence(
        "Posso consultar um protocolo exato ou informar status, categorias e prioridades da base. Qual informação você procura?"
    )
