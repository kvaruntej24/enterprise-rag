from app.ingestion.loaders import Document


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("\n"))
            if cut > chunk_size * 0.5:
                end = start + cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_documents(
    docs: list[Document], chunk_size: int = 1000, overlap: int = 150
) -> list[Document]:
    chunks = []
    for doc in docs:
        for i, piece in enumerate(chunk_text(doc.text, chunk_size, overlap)):
            chunks.append(Document(piece, {**doc.metadata, "chunk_index": i}))
    return chunks