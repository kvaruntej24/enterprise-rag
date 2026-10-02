from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup


@dataclass
class Document:
    text: str
    metadata: dict = field(default_factory=dict)


def load_pdf(path: Path) -> list[Document]:
    docs = []
    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text()
            if text.strip():
                docs.append(Document(text, {
                    "source": path.name,
                    "doc_type": "pdf",
                    "page": page_number,
                }))
    return docs


def load_html(path: Path) -> list[Document]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else path.stem

    root = soup.find("main")
    if root is None:
        root = soup

    for tag in root(["script", "style", "noscript", "svg", "nav", "header", "footer", "aside"]):
        tag.decompose()

    text = root.get_text(separator="\n")
    return [Document(text, {
        "source": path.name,
        "doc_type": "html",
        "title": title,
    })]


def load_markdown(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [Document(text, {"source": path.name, "doc_type": "markdown"})]


LOADERS = {
    ".pdf": load_pdf,
    ".html": load_html,
    ".htm": load_html,
    ".md": load_markdown,
}


def load_document(path: Path) -> list[Document]:
    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file type: {path}")
    return loader(path)