"""Fetch and parse Databricks sitemap URLs."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Set

import requests

from config import settings
from utils.helpers import LOGGER_NAME, save_json, setup_logging


logger = logging.getLogger(LOGGER_NAME + ".fetch_sitemap")


def _is_relevant_doc_url(url: str) -> bool:
    """Return True if URL belongs to English Databricks docs pages."""
    return "docs.databricks.com" in url and "/en/" in url


def _parse_sitemap(xml_content: str) -> tuple[list[str], list[str]]:
    """Parse XML and return (page_urls, child_sitemaps)."""
    root = ET.fromstring(xml_content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    page_urls: list[str] = []
    for loc in root.findall(".//sm:url/sm:loc", ns):
        url = (loc.text or "").strip()
        if url and _is_relevant_doc_url(url):
            page_urls.append(url)

    child_sitemaps: list[str] = []
    for loc in root.findall(".//sm:sitemap/sm:loc", ns):
        url = (loc.text or "").strip()
        if url and "docs.databricks.com" in url:
            child_sitemaps.append(url)

    return page_urls, child_sitemaps


def _fetch_xml(url: str) -> str:
    """Fetch XML from URL with configured timeout."""
    response = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def _collect_urls_recursive(
    sitemap_url: str,
    visited_sitemaps: Set[str],
    collected_urls: Set[str],
) -> None:
    """Recursively collect URLs from urlset/sitemapindex documents."""
    if sitemap_url in visited_sitemaps:
        return
    visited_sitemaps.add(sitemap_url)

    logger.info("Fetching sitemap from %s", sitemap_url)
    xml_content = _fetch_xml(sitemap_url)
    page_urls, child_sitemaps = _parse_sitemap(xml_content)

    for url in page_urls:
        collected_urls.add(url)

    for child in child_sitemaps:
        _collect_urls_recursive(child, visited_sitemaps, collected_urls)


def fetch_sitemap() -> dict:
    """Download sitemap and return a URL payload."""
    visited_sitemaps: set[str] = set()
    urls: set[str] = set()
    _collect_urls_recursive(settings.SITEMAP_URL, visited_sitemaps, urls)

    payload = {
        "sitemap_url": settings.SITEMAP_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(urls),
        "urls": sorted(urls),
    }
    return payload


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    output_path = settings.PROCESSED_DATA_DIR / "sitemap_urls.json"

    try:
        payload = fetch_sitemap()
        save_json(output_path, payload)
        logger.info("Saved %d URLs to %s", payload["count"], output_path)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to fetch sitemap: %s", exc)
        raise


if __name__ == "__main__":
    main()
