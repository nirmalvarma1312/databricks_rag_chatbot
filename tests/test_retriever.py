"""Unit tests for retriever result formatting."""

from rag.retriever import format_query_results


def test_format_query_results_maps_fields() -> None:
    raw = {
        "ids": [["id_1", "id_2"]],
        "documents": [["chunk text 1", "chunk text 2"]],
        "metadatas": [[
            {"title": "Doc 1", "url": "https://docs.databricks.com/en/a"},
            {"title": "Doc 2", "url": "https://docs.databricks.com/en/b"},
        ]],
        "distances": [[0.11, 0.22]],
    }

    chunks = format_query_results(raw)

    assert len(chunks) == 2
    assert chunks[0].chunk_id == "id_1"
    assert chunks[0].title == "Doc 1"
    assert chunks[0].url.endswith("/a")
    assert chunks[0].text == "chunk text 1"
    assert chunks[0].score == 0.11
