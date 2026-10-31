from app.core.config import settings
from app.knowledge.indexing import build_index


def main() -> None:
    chunks = build_index(
        settings.data_dir, settings.processed_dir, settings.chunk_size_chars, settings.chunk_overlap_chars
    )
    documents = len({chunk.source for chunk in chunks})
    print(f"Índice reconstruído: {documents} fontes, {len(chunks)} chunks em {settings.processed_dir}")


if __name__ == "__main__":
    main()
