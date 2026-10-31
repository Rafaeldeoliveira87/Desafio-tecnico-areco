from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.knowledge.indexing import build_index
from app.models.schemas import ReindexResponse

router = APIRouter(tags=["knowledge"])


@router.post("/knowledge/reindex", response_model=ReindexResponse)
def reindex(request: Request) -> ReindexResponse:
    if not settings.reindex_enabled or settings.app_env == "production":
        raise HTTPException(status_code=404, detail="Endpoint indisponível.")
    chunks = build_index(
        settings.data_dir, settings.processed_dir, settings.chunk_size_chars, settings.chunk_overlap_chars
    )
    request.app.state.knowledge_chunks = chunks
    return ReindexResponse(status="ok", documents=len({chunk.source for chunk in chunks}), chunks=len(chunks))
