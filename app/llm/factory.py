from __future__ import annotations

import logging

from app.core.config import settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


def get_provider():
    if not settings.external_processing_enabled or settings.llm_provider in {"", "none", "disabled"}:
        return None
    if settings.llm_provider != "openai_compatible":
        logger.warning("unknown_llm_provider_fallback")
        return None
    try:
        from app.llm.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider()
    except (ImportError, ProviderError):
        logger.warning("llm_provider_missing_configuration_fallback")
        return None
