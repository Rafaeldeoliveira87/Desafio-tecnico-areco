from __future__ import annotations

import hashlib
import re

from app.knowledge.models import KnowledgeChunk


def _chunk_id(source: str, location: str, text: str) -> str:
    raw = f"{source}\0{location}\0{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def split_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if max_chars < 100 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("Configuração de chunking inválida.")
    remaining = " ".join(text.split())
    chunks: list[str] = []
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        boundary = remaining.rfind(" ", 0, max_chars + 1)
        if boundary < max_chars // 2:
            boundary = max_chars
        part = remaining[:boundary].strip()
        if part:
            chunks.append(part)
        remaining = remaining[max(1, boundary - overlap_chars) :].strip()
    return chunks


def markdown_chunks(source: str, text: str, version: str, max_chars: int, overlap_chars: int) -> list[KnowledgeChunk]:
    sections = re.split(r"(?m)(?=^#{1,3}\s+)", text)
    chunks: list[KnowledgeChunk] = []
    current_heading = "Introdução"
    for section in sections:
        lines = section.splitlines()
        heading = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), current_heading)
        if any(line.startswith("#") for line in lines):
            current_heading = heading
        content = "\n".join(line for line in lines if line.strip() and not line.startswith("#"))
        for number, part in enumerate(split_text(content, max_chars, overlap_chars), start=1):
            location = current_heading if number == 1 else f"{current_heading} (parte {number})"
            chunks.append(
                KnowledgeChunk(
                    _chunk_id(source, location, part), "informacoes_internas", source, location, version, part
                )
            )
    return chunks


def faq_chunks(items: list[dict[str, str]]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for item in items:
        faq_id = item.get("id", "FAQ")
        text = f"Pergunta: {item['pergunta']} Resposta: {item['resposta']}"
        source = "informacoes_internas/faq_interno.json"
        location = f"{faq_id} → {item['documento']}"
        chunks.append(
            KnowledgeChunk(_chunk_id(source, location, text), "informacoes_internas", source, location, "FAQ", text)
        )
    return chunks
