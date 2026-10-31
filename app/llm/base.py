from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    async def classify(self, question: str) -> dict[str, object]: ...

    async def generate(self, system_prompt: str, user_prompt: str) -> str: ...
