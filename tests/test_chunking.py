from app.ingestion.chunking import chunk_documents, chunk_text
from app.ingestion.loaders import Document


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []


def test_short_text_is_one_chunk():
    assert chunk_text("A short sentence.") == ["A short sentence."]


def test_chunks_respect_max_size():
    chunks = chunk_text("word " * 600, chunk_size=1000, overlap=150)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)


def test_consecutive_chunks_overlap():
    chunks = chunk_text("word " * 600, chunk_size=1000, overlap=150)
    assert chunks[0][-50:] in chunks[1]


def test_prefers_sentence_boundary():
    text = "A" * 700 + ". " + "B" * 600
    chunks = chunk_text(text, chunk_size=1000, overlap=150)
    assert chunks[0].endswith(".")


def test_terminates_when_overlap_is_large():
    chunks = chunk_text("a" * 50, chunk_size=10, overlap=9)
    assert len(chunks) > 0


def test_metadata_is_copied_to_every_chunk():
    doc = Document("x" * 2500, {"source": "a.pdf", "doc_type": "pdf", "page": 3})
    chunks = chunk_documents([doc], chunk_size=1000, overlap=150)
    assert len(chunks) > 1
    assert all(c.metadata["source"] == "a.pdf" and c.metadata["page"] == 3 for c in chunks)
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))