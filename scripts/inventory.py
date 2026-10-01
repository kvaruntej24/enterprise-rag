from collections import Counter
from pathlib import Path

RAW_DIR = Path("data/raw")

files = sorted(p for p in RAW_DIR.rglob("*") if p.is_file())
by_type = Counter(p.suffix.lower() for p in files)
total_bytes = sum(p.stat().st_size for p in files)

for p in files:
    size_kb = p.stat().st_size / 1024
    print(f"{size_kb:9.1f} KB  {p.relative_to(RAW_DIR)}")

print()
print(f"Total files: {len(files)} ({total_bytes / 1024 / 1024:.1f} MB)")
for ext, count in by_type.most_common():
    print(f"  {ext or '(no extension)'}: {count}")