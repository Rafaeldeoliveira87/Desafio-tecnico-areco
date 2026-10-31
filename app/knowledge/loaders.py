from __future__ import annotations

import json
import re
from pathlib import Path

from app.knowledge.chunking import faq_chunks, markdown_chunks
from app.knowledge.models import KnowledgeChunk


def _version(text: str) -> str:
    match = re.search(r"Vers[aã]o\s+([\w.]+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else "sem-versao"


def load_internal_chunks(data_dir: Path, max_chars: int, overlap_chars: int) -> list[KnowledgeChunk]:
    internal_dir = (data_dir / "informacoes_internas").resolve()
    root = data_dir.resolve()
    if not internal_dir.is_relative_to(root):
        raise ValueError("Diretório de conhecimento fora da raiz permitida.")
    chunks: list[KnowledgeChunk] = []
    for path in sorted(internal_dir.glob("*.md")):
        resolved_path = path.resolve(strict=True)
        if not resolved_path.is_relative_to(internal_dir):
            raise ValueError("Documento aponta para fora do diretório de conhecimento permitido.")
        text = resolved_path.read_text(encoding="utf-8")
        source = path.relative_to(root).as_posix()
        chunks.extend(markdown_chunks(source, text, _version(text), max_chars, overlap_chars))
    faq_path = (internal_dir / "faq_interno.json").resolve()
    if not faq_path.is_relative_to(internal_dir):
        raise ValueError("FAQ aponta para fora do diretório de conhecimento permitido.")
    if faq_path.exists():
        faq = json.loads(faq_path.read_text(encoding="utf-8"))
        if not isinstance(faq, list):
            raise ValueError("O FAQ deve ser uma lista de itens.")
        chunks.extend(faq_chunks(faq))
    return chunks
