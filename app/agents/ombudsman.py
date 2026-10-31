from __future__ import annotations

from pathlib import Path

from app.services.ombudsman import answer_ombudsman


class OmbudsmanAgent:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    async def answer(self, question: str):
        return answer_ombudsman(question, self.data_dir)
