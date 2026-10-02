import sys
from pathlib import Path

import pymupdf

from app.ingestion.chunking import chunk_documents
from app.ingestion.cleaning import clean_documents
from app.ingestion.loaders import load_document

pymupdf.TOOLS.mupdf_display_errors(False)

path = Path(sys.argv[1])
size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
overlap = int(sys.argv[3]) if len(sys.argv) > 3 else 150

docs = clean_documents(load_document(path))
chunks = chunk_documents(docs, size, overlap)
lengths = [len(c.text) for c in chunks]

print(f"{len(docs)} pages/sections -> {len(chunks)} chunks")
print(f"length min/avg/max: {min(lengths)} / {sum(lengths) // len(lengths)} / {max(lengths)}")
print("-" * 60)
for c in chunks[:2]:
    print(c.metadata)
    print(c.text)
    print("-" * 60)