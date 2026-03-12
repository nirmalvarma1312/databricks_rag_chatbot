"""Chatbot orchestration for retrieval, prompt building, and response generation."""

from __future__ import annotations

import logging

from openai import OpenAI

from config import settings
from rag.prompt_builder import build_prompt
from rag.retriever import Retriever
from utils.helpers import LOGGER_NAME
from utils.models import ChatResponse


logger = logging.getLogger(LOGGER_NAME + ".chatbot")


class DatabricksRAGChatbot:
    """High-level RAG chatbot service."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        self.retriever = Retriever()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def ask(self, question: str) -> ChatResponse:
        """Run the full RAG flow and return grounded response with citations."""
        question = question.strip()
        if not question:
            return ChatResponse(
                answer="Please enter a question.",
                citations=[],
                found_in_docs=False,
            )

        chunks = self.retriever.retrieve(question, top_k=settings.TOP_K)
        if not chunks:
            return ChatResponse(
                answer="I could not find this in the indexed Databricks docs.",
                citations=[],
                found_in_docs=False,
            )

        messages = build_prompt(question, chunks)

        try:
            response = self.openai_client.responses.create(
                model=settings.CHAT_MODEL,
                input=messages,
                temperature=0,
            )
            answer = (response.output_text or "").strip()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("LLM call failed: %s", exc)
            return ChatResponse(
                answer="I could not generate an answer due to an internal error.",
                citations=[],
                found_in_docs=False,
            )

        if not answer:
            answer = "I could not find this in the indexed Databricks docs."

        normalized = answer.lower()
        found = "could not find this in the indexed databricks docs" not in normalized

        citations: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for chunk in chunks:
            if chunk.url in seen_urls:
                continue
            citations.append({"title": chunk.title, "url": chunk.url})
            seen_urls.add(chunk.url)

        return ChatResponse(answer=answer, citations=citations, found_in_docs=found)
