import re
from collections import Counter

from app.ingestion.loaders import Document

HTML_JUNK_LINES = {
    "Skip to main content",
    "Download & print article PDF",
    "Show",
    "Show All",
    "Back to top",
}


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def find_repeated_lines(pages: list[str], min_fraction: float = 0.4) -> set[str]:
    counts = Counter()
    for page in pages:
        counts.update({line.strip() for line in page.splitlines() if line.strip()})
    cutoff = max(3, int(len(pages) * min_fraction))
    return {line for line, n in counts.items() if n >= cutoff}


def simplify_markdown(text: str) -> str:
    parts = text.split("```")
    if len(parts) % 2 == 0:  # unbalanced code fences: leave the text unchanged
        return text
    for i in range(0, len(parts), 2):  # even parts are prose, odd parts are code
        parts[i] = re.sub(
            r"!?\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)", r"\1", parts[i]
        )
        parts[i] = parts[i].replace("**", "")
    return "```".join(parts)


def drop_html_junk(text: str) -> str:
    kept = [
        line for line in text.splitlines()
        if line.strip() not in HTML_JUNK_LINES
        and not re.match(r"^\s*icons?/", line)
    ]
    return "\n".join(kept)


def clean_documents(docs: list[Document]) -> list[Document]:
    pages_by_source: dict[str, list[str]] = {}
    for doc in docs:
        if doc.metadata["doc_type"] == "pdf":
            pages_by_source.setdefault(doc.metadata["source"], []).append(doc.text)
    repeated = {src: find_repeated_lines(p) for src, p in pages_by_source.items()}

    cleaned = []
    for doc in docs:
        text = doc.text
        doc_type = doc.metadata["doc_type"]
        if doc_type == "pdf":
            drop = repeated[doc.metadata["source"]]
            text = "\n".join(l for l in text.splitlines() if l.strip() not in drop)
        elif doc_type == "markdown":
            text = simplify_markdown(text)
        elif doc_type == "html":
            text = drop_html_junk(text)
        text = normalize_whitespace(text)
        if text:
            cleaned.append(Document(text, dict(doc.metadata)))
    return cleaned