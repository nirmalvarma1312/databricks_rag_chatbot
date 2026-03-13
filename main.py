"""Minimal WSGI entrypoint for platforms (e.g., Vercel Python runtime).

This project is primarily a Streamlit app started with:
    streamlit run app/main.py

The `app` callable below exists so Python runtimes that require a root entrypoint
can boot successfully instead of failing with "No python entrypoint found".
"""

from __future__ import annotations

from typing import Iterable


def app(environ: dict, start_response) -> Iterable[bytes]:
    """Return a simple health/info response for WSGI runtimes."""
    status = "200 OK"
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response(status, headers)

    body = (
        "Databricks RAG Chatbot repository is healthy. "
        "Run the Streamlit UI with: streamlit run app/main.py"
    )
    return [body.encode("utf-8")]
