"""Parse raw HTML files into clean documentation documents."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import trafilatura

from config import settings
from utils.helpers import LOGGER_NAME, load_json, normalize_text, save_json, setup_logging
from utils.models import Document


logger = logging.getLogger(LOGGER_NAME + ".parse_html")


def _extract_text(html: str) -> str:
    """Extract readable text with trafilatura fallback to BeautifulSoup."""
    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
    )
    if extracted:
        return normalize_text(extracted)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript", "svg", "form"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"})
    target = main if main is not None else soup.body
    text = target.get_text("\n", strip=True) if target else ""
    return normalize_text(text)


def _extract_title(html: str) -> str:
    """Extract page title."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return normalize_text(h1.get_text(" ", strip=True))
    if soup.title and soup.title.get_text(strip=True):
        return normalize_text(soup.title.get_text(" ", strip=True))
    return "Untitled"


def _extract_section(url: str) -> str:
    """Extract a rough section from URL path."""
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2:
        return parts[1]
    if parts:
        return parts[0]
    return "general"


def parse_html_documents() -> list[Document]:
    """Convert raw manifest HTML files into normalized document records."""
    manifest_payload = load_json(settings.RAW_DATA_DIR / "raw_manifest.json")
    manifest = manifest_payload.get("manifest", [])

    documents: list[Document] = []

    for item in manifest:
        doc_id = item["doc_id"]
        url = item["url"]
        path = item["path"]

        try:
            html = Path(path).read_text(encoding="utf-8")
            text = _extract_text(html)
            if not text:
                logger.warning("Skipping empty text for %s", url)
                continue

            doc = Document(
                doc_id=doc_id,
                title=_extract_title(html),
                url=url,
                source="databricks_docs",
                section=_extract_section(url),
                text=text,
            )
            documents.append(doc)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to parse %s: %s", url, exc)

    payload = [doc.__dict__ for doc in documents]
    save_json(settings.PROCESSED_DATA_DIR / "documents.json", payload)
    return documents


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    try:
        docs = parse_html_documents()
        logger.info("Saved %d processed documents", len(docs))
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Parse stage failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
