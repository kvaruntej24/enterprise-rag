from app.ingestion.cleaning import (
    clean_documents,
    find_repeated_lines,
    normalize_whitespace,
    simplify_markdown,
)
from app.ingestion.loaders import Document


def test_normalize_whitespace_collapses_blank_lines():
    assert normalize_whitespace("a  \n\n\n\nb") == "a\n\nb"


def test_find_repeated_lines_detects_header_only():
    pages = [f"HEADER\nbody {i}" for i in range(10)]
    repeated = find_repeated_lines(pages)
    assert "HEADER" in repeated
    assert "body 3" not in repeated


def test_clean_documents_removes_pdf_header_and_keeps_metadata():
    docs = [
        Document(f"HEADER\ncontent {i}", {"source": "x.pdf", "doc_type": "pdf", "page": i + 1})
        for i in range(10)
    ]
    cleaned = clean_documents(docs)
    assert [d.text for d in cleaned] == [f"content {i}" for i in range(10)]
    assert cleaned[4].metadata["page"] == 5


def test_markdown_links_and_bold_are_simplified():
    text = "See [the guide](http://x.com) for **details**"
    assert simplify_markdown(text) == "See the guide for details"


def test_markdown_link_with_parentheses_in_url():
    text = "[Wiper](https://en.wikipedia.org/wiki/Wiper_(malware))"
    assert simplify_markdown(text) == "Wiper"


def test_code_blocks_are_not_modified():
    text = "```python\ndef f(**kwargs):\n```"
    assert simplify_markdown(text) == text


def test_unbalanced_code_fences_leave_text_unchanged():
    text = "a ``` b **bold**"
    assert simplify_markdown(text) == text