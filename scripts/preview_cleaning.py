import sys
from pathlib import Path

import pymupdf

from app.ingestion.cleaning import clean_documents
from app.ingestion.loaders import load_document

pymupdf.TOOLS.mupdf_display_errors(False)

path = Path(sys.argv[1])
index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

raw = load_document(path)
cleaned = clean_documents(raw)

print(f"Chars before: {sum(len(d.text) for d in raw):,}")
print(f"Chars after:  {sum(len(d.text) for d in cleaned):,}")
print("-" * 60)
print(cleaned[index].text[:1200])