"""Retrieve relevant chunks from ChromaDB using OpenAI query embeddings."""

from __future__ import annotations

import logging

from config import settings
from utils.helpers import LOGGER_NAME
from utils.models import RetrievedChunk


logger = logging.getLogger(LOGGER_NAME + ".retriever")
COLLECTION_NAME = "databricks_docs_v1"
DEFAULT_MAX_DISTANCE = 1.0


def format_query_results(result: dict) -> list[RetrievedChunk]:
    """Convert raw Chroma query payload into RetrievedChunk models."""
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0] if result.get("distances") else []

    chunks: list[RetrievedChunk] = []
    for i, chunk_id in enumerate(ids):
        metadata = metadatas[i] if i < len(metadatas) else {}
        score = distances[i] if i < len(distances) else None
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                title=str(metadata.get("title", "Untitled")),
                url=str(metadata.get("url", "")),
                text=docs[i] if i < len(docs) else "",
                score=score,
            )
        )

    return chunks


class Retriever:
    """Query ChromaDB with OpenAI embeddings."""

    def __init__(self, max_distance: float = DEFAULT_MAX_DISTANCE) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        from openai import OpenAI
        import chromadb

        self.max_distance = max_distance
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Retrieve top-k most relevant chunks for query."""
        query = query.strip()
        if not query:
            return []

        k = top_k or settings.TOP_K

        try:
            emb = self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=query,
            )
            query_embedding = emb.data[0].embedding
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["metadatas", "documents", "distances"],
            )
            chunks = format_query_results(result)
            with_scores = [c for c in chunks if c.score is not None]
            if not with_scores:
                return chunks

            filtered = [c for c in chunks if c.score is not None and c.score <= self.max_distance]
            return filtered
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Retrieval failed: %s", exc)
            return []
