from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.knowledge.loaders import load_internal_chunks
from app.knowledge.models import KnowledgeChunk


def build_index(data_dir: Path, processed_dir: Path, max_chars: int, overlap_chars: int) -> list[KnowledgeChunk]:
    chunks = load_internal_chunks(data_dir, max_chars, overlap_chars)
    processed_dir.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="knowledge-", suffix=".json", dir=processed_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                {"version": 1, "chunks": [chunk.to_dict() for chunk in chunks]}, stream, ensure_ascii=False, indent=2
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, processed_dir / "knowledge_index.json")
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return chunks


def read_index(path: Path) -> list[KnowledgeChunk]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("version") != 1 or not isinstance(value.get("chunks"), list):
        raise ValueError("Formato de índice não suportado.")
    return [KnowledgeChunk.from_dict(item) for item in value["chunks"]]
