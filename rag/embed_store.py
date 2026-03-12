"""Embed chunks with OpenAI and store vectors in ChromaDB."""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from openai import OpenAI

from config import settings
from utils.helpers import LOGGER_NAME, load_json, setup_logging
from utils.models import Chunk


logger = logging.getLogger(LOGGER_NAME + ".embed_store")
COLLECTION_NAME = "databricks_docs_v1"


def batched(items: list[Any], batch_size: int) -> list[list[Any]]:
    """Split a list into fixed-size batches."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def embed_and_store(batch_size: int = 64) -> int:
    """Read chunks, create embeddings, and upsert into ChromaDB."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")

    payload = load_json(settings.CHUNKS_DATA_DIR / "chunks.json")
    chunks = [Chunk(**item) for item in payload]
    logger.info("Loaded %d chunks", len(chunks))

    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    total_upserted = 0
    for batch in batched(chunks, batch_size=batch_size):
        texts = [item.text for item in batch]

        try:
            emb_response = openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts,
            )
            embeddings = [row.embedding for row in emb_response.data]

            ids = [item.chunk_id for item in batch]
            docs = texts
            metadatas = [
                {
                    "doc_id": item.doc_id,
                    "title": item.title,
                    "url": item.url,
                    "source": item.source,
                    "section": item.section,
                    "chunk_index": item.chunk_index,
                }
                for item in batch
            ]

            collection.upsert(
                ids=ids,
                documents=docs,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            total_upserted += len(batch)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Embedding/upsert failed for batch: %s", exc)

    logger.info("Upserted %d chunks to Chroma", total_upserted)
    return total_upserted


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    try:
        embed_and_store()
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Embed/store stage failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
