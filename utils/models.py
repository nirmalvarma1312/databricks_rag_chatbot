"""Data models used across ingestion, retrieval, and chat layers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Document:
    """Processed documentation page."""

    doc_id: str
    title: str
    url: str
    source: str
    section: str
    text: str


@dataclass
class Chunk:
    """Chunked text unit used for embedding and retrieval."""

    chunk_id: str
    doc_id: str
    title: str
    url: str
    source: str
    section: str
    text: str
    chunk_index: int


@dataclass
class RetrievedChunk:
    """Retrieved chunk returned from vector search."""

    chunk_id: str
    title: str
    url: str
    text: str
    score: float | None = None


@dataclass
class ChatResponse:
    """Final chatbot response payload."""

    answer: str
    citations: list[dict[str, str]] = field(default_factory=list)
    found_in_docs: bool = True
