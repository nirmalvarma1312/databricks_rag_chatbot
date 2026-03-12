"""Chunk processed documents into overlap-preserving chunks."""

from __future__ import annotations

import logging

from config import settings
from utils.helpers import LOGGER_NAME, load_json, normalize_text, save_json, setup_logging
from utils.models import Chunk, Document


logger = logging.getLogger(LOGGER_NAME + ".chunker")


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into paragraph-aware chunks with deterministic overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = normalize_text(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)

        # Split very long paragraph deterministically to respect chunk_size.
        if paragraph_len > chunk_size:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            start = 0
            step = chunk_size - chunk_overlap
            while start < paragraph_len:
                end = start + chunk_size
                chunks.append(paragraph[start:end])
                if end >= paragraph_len:
                    break
                start += step
            continue

        extra_len = paragraph_len if not current else paragraph_len + 2
        if current_len + extra_len <= chunk_size:
            current.append(paragraph)
            current_len += extra_len
            continue

        if current:
            chunks.append("\n\n".join(current))

        # Build overlap context from the previous chunk tail.
        overlap_text = chunks[-1][-chunk_overlap:] if chunks and chunk_overlap > 0 else ""
        current = [overlap_text, paragraph] if overlap_text else [paragraph]
        current_len = len("\n\n".join(current))

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_document(doc: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Chunk one document and preserve source metadata."""
    texts = split_text(doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[Chunk] = []

    for idx, chunk_text in enumerate(texts):
        chunks.append(
            Chunk(
                chunk_id=f"{doc.doc_id}_{idx}",
                doc_id=doc.doc_id,
                title=doc.title,
                url=doc.url,
                source=doc.source,
                section=doc.section,
                text=chunk_text,
                chunk_index=idx,
            )
        )

    return chunks


def chunk_all_documents() -> list[Chunk]:
    """Chunk all parsed documents and save as JSON."""
    docs_payload = load_json(settings.PROCESSED_DATA_DIR / "documents.json")
    documents = [Document(**item) for item in docs_payload]

    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(
            chunk_document(
                doc,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
        )

    save_json(settings.CHUNKS_DATA_DIR / "chunks.json", [c.__dict__ for c in all_chunks])
    return all_chunks


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    try:
        chunks = chunk_all_documents()
        logger.info("Saved %d chunks", len(chunks))
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Chunking failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
