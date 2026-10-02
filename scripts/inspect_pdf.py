import sys

import pymupdf

path = sys.argv[1]
page_number = int(sys.argv[2]) if len(sys.argv) > 2 else 0

doc = pymupdf.open(path)
print(f"Pages: {len(doc)}")

near_empty_pages = [
    i + 1 for i, page in enumerate(doc) if len(page.get_text().strip()) < 50
]
print(f"Pages with almost no text: {near_empty_pages}")

print("-" * 60)
print(f"Page {page_number + 1} text:")
print(doc[page_number].get_text()[1400:3500])