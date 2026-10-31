from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def _as_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str
    data_dir: Path
    processed_dir: Path
    logs_dir: Path
    confidence_threshold: float
    max_question_length: int
    chunk_size_chars: int
    chunk_overlap_chars: int
    retrieval_top_k: int
    allowed_origins: tuple[str, ...]
    reindex_enabled: bool
    llm_provider: str
    llm_api_key: str | None
    llm_base_url: str
    llm_model: str | None
    llm_timeout_seconds: float
    llm_max_retries: int
    external_processing_enabled: bool

    @classmethod
    def from_env(cls) -> "Settings":
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        origins = tuple(x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip())
        return cls(
            app_env=app_env,
            data_dir=Path(os.getenv("DATA_DIR", str(ROOT_DIR))).resolve(),
            processed_dir=Path(os.getenv("PROCESSED_DIR", str(ROOT_DIR / "data" / "processed"))).resolve(),
            logs_dir=Path(os.getenv("LOGS_DIR", str(ROOT_DIR / "logs"))).resolve(),
            confidence_threshold=float(os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.55")),
            max_question_length=int(os.getenv("MAX_QUESTION_LENGTH", "1500")),
            chunk_size_chars=int(os.getenv("CHUNK_SIZE_CHARS", "900")),
            chunk_overlap_chars=int(os.getenv("CHUNK_OVERLAP_CHARS", "120")),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "4")),
            allowed_origins=origins,
            reindex_enabled=_as_bool("REINDEX_ENABLED", app_env != "production"),
            llm_provider=os.getenv("LLM_PROVIDER", "none").strip().lower(),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip(),
            llm_model=os.getenv("LLM_MODEL") or None,
            llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "12")),
            llm_max_retries=max(0, min(int(os.getenv("LLM_MAX_RETRIES", "1")), 3)),
            external_processing_enabled=_as_bool("EXTERNAL_PROCESSING_ENABLED", False),
        )


settings = Settings.from_env()
