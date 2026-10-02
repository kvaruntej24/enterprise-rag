import hashlib
import json
import logging
from pathlib import Path

import pymupdf

from app.core.config import settings
from app.ingestion.chunking import chunk_documents
from app.ingestion.cleaning import clean_documents
from app.ingestion.loaders import LOADERS, load_document

pymupdf.TOOLS.mupdf_display_errors(False)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("ingest")

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/processed/chunks.jsonl")
MIN_CHARS = 1000


def make_chunk_id(metadata: dict, text: str) -> str:
    key = f"{metadata['source']}|{metadata.get('page', '')}|{metadata['chunk_index']}|{text}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for path in sorted(RAW_DIR.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in LOADERS:
                log.warning("Skipping unsupported file: %s", path.name)
                continue
            try:
                docs = clean_documents(load_document(path))
            except Exception:
                log.exception("Failed to parse %s", path.name)
                continue

            chars = sum(len(d.text) for d in docs)
            if chars < MIN_CHARS:
                log.warning("Very little text (%d chars) in %s", chars, path.name)

            chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)
            for c in chunks:
                record = {
                    "chunk_id": make_chunk_id(c.metadata, c.text),
                    "text": c.text,
                    "metadata": c.metadata,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
            total += len(chunks)
            log.info("%-60s %4d chunks", path.name, len(chunks))
    log.info("Wrote %d chunks to %s", total, OUT_PATH)


if __name__ == "__main__":
    main()