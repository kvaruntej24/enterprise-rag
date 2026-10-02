from pathlib import Path

from app.ingestion.loaders import LOADERS, load_document
import pymupdf

pymupdf.TOOLS.mupdf_display_errors(False)#this has to be removed later, used to silence warnings
RAW_DIR = Path("data/raw")

for path in sorted(p for p in RAW_DIR.rglob("*") if p.is_file()):
    name = path.relative_to(RAW_DIR)
    if path.suffix.lower() not in LOADERS:
        print(f"SKIPPED (unsupported type): {name}")
        continue
    docs = load_document(path)
    chars = sum(len(d.text) for d in docs)
    flag = "  <-- almost no text!" if chars < 500 else ""
    print(f"{len(docs):4d} docs {chars:10,d} chars  {name}{flag}")