"""Streamlit UI for Databricks docs RAG chatbot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# Ensure repo root is importable in Streamlit cloud/runtime environments.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.chatbot import DatabricksRAGChatbot
from utils.helpers import setup_logging


setup_logging()
logger = logging.getLogger("databricks_rag.ui")


@st.cache_resource
def get_chatbot() -> DatabricksRAGChatbot:
    """Create chatbot instance once per Streamlit process."""
    return DatabricksRAGChatbot()


FOLLOW_UP_PREFIXES = (
    "why",
    "how",
    "what about",
    "and",
    "also",
    "can you explain",
    "what is important",
    "is it",
    "does it",
    "when",
    "where",
)


def _looks_like_follow_up(question: str) -> bool:
    """Heuristic check for short, context-dependent follow-up questions."""
    cleaned = question.strip().lower()
    if not cleaned:
        return False

    word_count = len(cleaned.split())
    if word_count <= 6:
        return True

    return cleaned.startswith(FOLLOW_UP_PREFIXES)


def _last_user_question() -> str:
    """Get the most recent user question from session chat history."""
    for msg in reversed(st.session_state.get("messages", [])):
        if msg.get("role") == "user" and msg.get("content"):
            return str(msg["content"]).strip()
    return ""


def main() -> None:
    """Render Streamlit app."""
    st.set_page_config(page_title="Databricks Docs RAG Chatbot", page_icon="📘", layout="centered")

    st.title("Databricks Documentation RAG Chatbot")
    st.write(
        "Ask questions about indexed Databricks docs. "
        "Answers are grounded in retrieved documentation chunks with citations."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("citations"):
                st.markdown("**Sources**")
                for idx, item in enumerate(msg["citations"], start=1):
                    st.markdown(f"{idx}. [{item['title']}]({item['url']})")
            if msg["role"] == "assistant" and not msg.get("found_in_docs", True):
                st.warning("No relevant answer found in the indexed Databricks docs.")

    question = st.chat_input("Ask about Databricks docs...")
    if not question:
        return

    previous_user_question = _last_user_question()
    retrieval_query = question
    if previous_user_question and _looks_like_follow_up(question):
        retrieval_query = f"{previous_user_question}\nFollow-up: {question}"

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    try:
        chatbot = get_chatbot()
        with st.spinner("Searching indexed docs..."):
            response = chatbot.ask(question, retrieval_query=retrieval_query)

        assistant_message = {
            "role": "assistant",
            "content": response.answer,
            "citations": response.citations,
            "found_in_docs": response.found_in_docs,
        }
        st.session_state.messages.append(assistant_message)

        with st.chat_message("assistant"):
            st.write(response.answer)
            if response.citations:
                st.markdown("**Sources**")
                for idx, item in enumerate(response.citations, start=1):
                    st.markdown(f"{idx}. [{item['title']}]({item['url']})")
            if not response.found_in_docs:
                st.warning("No relevant answer found in the indexed Databricks docs.")
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("App error: %s", exc)
        st.error("An error occurred. Check logs and environment configuration.")


if __name__ == "__main__":
    main()
