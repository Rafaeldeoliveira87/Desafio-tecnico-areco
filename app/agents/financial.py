from __future__ import annotations

from pathlib import Path

from app.services.finance import answer_financial


class FinancialAgent:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    async def answer(self, question: str):
        return answer_financial(question, self.data_dir)
