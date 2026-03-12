"""Unit tests for chunking behavior."""

from ingestion.chunker import chunk_document
from utils.models import Document


def test_chunk_overlap_and_metadata_preserved() -> None:
    text = "A" * 1000
    doc = Document(
        doc_id="doc123",
        title="Test Doc",
        url="https://docs.databricks.com/en/test",
        source="databricks_docs",
        section="test",
        text=text,
    )

    chunks = chunk_document(doc, chunk_size=300, chunk_overlap=50)

    assert len(chunks) >= 4
    assert chunks[0].chunk_id == "doc123_0"
    assert chunks[1].chunk_id == "doc123_1"

    # Validate overlap by checking the boundary characters between chunk 0 and 1.
    assert chunks[0].text[-50:] == chunks[1].text[:50]

    # Metadata preservation
    assert chunks[0].title == "Test Doc"
    assert chunks[0].url == "https://docs.databricks.com/en/test"
    assert chunks[0].source == "databricks_docs"
    assert chunks[0].section == "test"
