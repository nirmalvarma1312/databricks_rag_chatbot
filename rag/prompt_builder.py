"""Prompt construction for strict grounded RAG responses."""

from __future__ import annotations

from utils.models import RetrievedChunk


SYSTEM_PROMPT = (
    "You are a Databricks documentation assistant. "
    "Answer only from the provided context. "
    "Do not use outside knowledge. "
    "If the answer is not present in the context, say exactly: "
    "'I could not find this in the indexed Databricks docs.' "
    "Cite sources using [1], [2], etc."
)


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    """Build strict grounded chat messages with source-indexed context."""
    context_parts: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[{idx}] Title: {chunk.title}\n"
            f"URL: {chunk.url}\n"
            f"Content:\n{chunk.text}\n"
        )

    context_block = "\n".join(context_parts)
    user_prompt = (
        "Use only the following retrieved Databricks documentation context.\n\n"
        f"{context_block}\n"
        "Instructions:\n"
        "1. Answer strictly from context.\n"
        "2. If missing, say: I could not find this in the indexed Databricks docs.\n"
        "3. Keep the answer concise and factual.\n"
        "4. Include citations like [1], [2].\n\n"
        f"Question: {question}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
