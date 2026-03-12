"""Streamlit UI for Databricks docs RAG chatbot."""

from __future__ import annotations

import logging

import streamlit as st

from app.chatbot import DatabricksRAGChatbot
from utils.helpers import setup_logging


setup_logging()
logger = logging.getLogger("databricks_rag.ui")


@st.cache_resource
def get_chatbot() -> DatabricksRAGChatbot:
    """Create chatbot instance once per Streamlit process."""
    return DatabricksRAGChatbot()


def main() -> None:
    """Render Streamlit app."""
    st.set_page_config(page_title="Databricks Docs RAG Chatbot", page_icon="📘", layout="centered")

    st.title("Databricks Documentation RAG Chatbot")
    st.write(
        "Ask questions about indexed Databricks docs. "
        "Answers are grounded in retrieved documentation chunks with citations."
    )

    question = st.text_input("Your question", placeholder="What is Unity Catalog in Databricks?")
    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question.")
            return

        try:
            chatbot = get_chatbot()
            response = chatbot.ask(question)
            st.subheader("Answer")
            st.write(response.answer)

            if response.citations:
                st.subheader("Sources")
                for idx, item in enumerate(response.citations, start=1):
                    st.markdown(f"{idx}. [{item['title']}]({item['url']})")

            if not response.found_in_docs:
                st.warning("No relevant answer found in the indexed Databricks docs.")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("App error: %s", exc)
            st.error("An error occurred. Check logs and environment configuration.")


if __name__ == "__main__":
    main()
