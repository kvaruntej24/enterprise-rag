import random
from pathlib import Path

import pymupdf

from app.ingestion.chunking import chunk_documents
from app.ingestion.cleaning import clean_documents
from app.ingestion.loaders import LOADERS, load_document

pymupdf.TOOLS.mupdf_display_errors(False)

RAW_DIR = Path("data/raw")
SETTINGS = [(500, 75), (1000, 150), (1500, 225)]

docs = []
for path in sorted(RAW_DIR.rglob("*")):
    if path.is_file() and path.suffix.lower() in LOADERS:
        docs.extend(clean_documents(load_document(path)))
print(f"{len(docs)} cleaned pages/sections loaded\n")

random.seed(42)
for size, overlap in SETTINGS:
    chunks = chunk_documents(docs, size, overlap)
    lengths = [len(c.text) for c in chunks]
    tiny = sum(1 for n in lengths if n < 200)
    no_end = sum(
        1 for c in chunks if not c.text.rstrip().endswith((".", "!", "?", ":"))
    )
    print(f"size={size} overlap={overlap}")
    print(f"  chunks: {len(chunks):,}   avg length: {sum(lengths) // len(lengths)}")
    print(f"  tiny (<200 chars): {tiny}   not ending at a sentence end: {no_end}")
    sample = random.choice(chunks)
    print(f"  sample metadata: {sample.metadata}")
    print("  " + sample.text[:600].replace("\n", "\n  "))
    print("-" * 60)