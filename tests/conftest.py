from pathlib import Path

import pytest

from app.knowledge.loaders import load_internal_chunks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def data_dir() -> Path:
    return ROOT


@pytest.fixture
def internal_chunks(data_dir):
    return load_internal_chunks(data_dir, max_chars=900, overlap_chars=120)
