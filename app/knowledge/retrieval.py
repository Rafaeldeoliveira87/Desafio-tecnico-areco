from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from app.knowledge.models import KnowledgeChunk, SearchResult

STOPWORDS = {
    "como",
    "qual",
    "quais",
    "que",
    "para",
    "com",
    "uma",
    "uns",
    "por",
    "dos",
    "das",
    "de",
    "do",
    "da",
    "e",
    "o",
    "a",
    "os",
    "as",
    "em",
    "um",
    "me",
    "sobre",
    "foi",
}


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(char for char in normalized if not unicodedata.combining(char))
    terms: list[str] = []
    for term in re.findall(r"[a-z0-9]+", plain):
        if term.endswith("oes") and len(term) > 5:
            term = term[:-3] + "ao"
        elif term.endswith("ais") and len(term) > 5:
            term = term[:-3] + "al"
        elif term.endswith("s") and len(term) > 4:
            term = term[:-1]
        if len(term) > 1 and term not in STOPWORDS:
            terms.append(term)
    return terms


def _title_terms(source: str, location: str = "") -> set[str]:
    """Termos do nome do documento (ex.: 07_fluxo_de_incidentes.md -> fluxo, incidente).

    Para itens de FAQ, usa o documento-alvo indicado em "FAQ-001 → 01_politica_ferias.md".
    """
    name = location.split("→")[-1].strip() if "→" in location else source
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return {term for term in tokenize(stem.replace("_", " ")) if not term.isdigit()}


TITLE_BOOST = 3.0  # multiplicado pelo IDF: termo raro no título pesa mais que termo genérico


def search(query: str, chunks: list[KnowledgeChunk], domain: str, top_k: int = 4) -> list[SearchResult]:
    query_terms = tokenize(query)
    documents = [chunk for chunk in chunks if chunk.domain == domain]
    if not query_terms or not documents or top_k < 1:
        return []
    tokenized = [tokenize(chunk.text) for chunk in documents]
    avg_len = sum(map(len, tokenized)) / len(tokenized) or 1
    doc_freq: Counter[str] = Counter()
    for words in tokenized:
        doc_freq.update(set(words))
    k1, b = 1.5, 0.75
    results: list[SearchResult] = []
    for chunk, words in zip(documents, tokenized):
        frequencies = Counter(words)
        score = 0.0
        for term in query_terms:
            freq = frequencies[term]
            if not freq:
                continue
            idf = math.log(1 + (len(documents) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            score += idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * len(words) / avg_len))
        if score > 0:
            # Termos da pergunta presentes no nome do documento indicam o tema do documento inteiro.
            for term in set(query_terms) & _title_terms(chunk.source, chunk.location):
                idf = math.log(1 + (len(documents) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
                score += TITLE_BOOST * idf
            results.append(SearchResult(chunk, score))
    return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]
