from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    domain: str
    source: str
    location: str
    document_version: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, str]) -> "KnowledgeChunk":
        return cls(**value)


@dataclass(frozen=True)
class SearchResult:
    chunk: KnowledgeChunk
    score: float
