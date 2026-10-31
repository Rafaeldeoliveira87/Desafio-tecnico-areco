from pathlib import Path

import pytest

from app.knowledge.loaders import load_internal_chunks
from app.knowledge.retrieval import search


def test_internal_loader_and_sources(internal_chunks):
    assert len({chunk.source for chunk in internal_chunks}) == 11
    assert all(chunk.domain == "informacoes_internas" for chunk in internal_chunks)
    assert all(chunk.chunk_id and chunk.document_version and chunk.location for chunk in internal_chunks)


def test_retrieval_matches_policy_and_faq(internal_chunks):
    results = search(
        "Quais são as aprovações para uma compra de R$ 12.000?", internal_chunks, "informacoes_internas", 3
    )
    assert results
    assert any(
        "03_aprovacao_de_compras.md" in result.chunk.source or "FAQ-004" in result.chunk.location
        for result in results[:2]
    )


def test_retrieval_filters_by_domain(internal_chunks):
    assert search("Como solicito férias?", internal_chunks, "ouvidoria", 4) == []


def test_absent_document_terms_return_no_results(internal_chunks):
    assert search("procedimento de viagens interplanetárias", internal_chunks, "informacoes_internas", 4) == []


def test_loader_rejects_document_resolved_outside_knowledge_root(tmp_path, monkeypatch):
    internal_dir = tmp_path / "informacoes_internas"
    internal_dir.mkdir()
    document = internal_dir / "policy.md"
    document.write_text("# Política\nConteúdo de teste.", encoding="utf-8")
    outside = tmp_path / "outside.md"
    original_resolve = Path.resolve

    def resolve(path, strict=False):
        if path == document:
            return outside
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="fora do diretório"):
        load_internal_chunks(tmp_path, max_chars=900, overlap_chars=120)
