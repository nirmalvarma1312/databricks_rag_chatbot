"""Download documentation pages from saved sitemap URLs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings
from utils.helpers import LOGGER_NAME, generate_id, load_json, save_json, setup_logging


logger = logging.getLogger(LOGGER_NAME + ".crawl_pages")


USER_AGENT = "databricks-rag-bot/1.0 (+https://docs.databricks.com)"


def build_session() -> requests.Session:
    """Create requests session with retry behavior."""
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def crawl_pages() -> dict:
    """Download URL list and persist raw HTML files plus manifest."""
    input_path = settings.PROCESSED_DATA_DIR / "sitemap_urls.json"
    payload = load_json(input_path)
    urls: list[str] = payload.get("urls", [])

    session = build_session()
    manifest: list[dict] = []
    failed: list[dict] = []

    for idx, url in enumerate(urls, start=1):
        doc_id = generate_id(url)
        html_path = settings.RAW_DATA_DIR / f"{doc_id}.html"

        try:
            response = session.get(url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(response.text, encoding="utf-8")

            manifest.append({"doc_id": doc_id, "url": url, "path": str(html_path)})
            if idx % 50 == 0:
                logger.info("Downloaded %d/%d pages", idx, len(urls))
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to fetch %s: %s", url, exc)
            failed.append({"url": url, "error": str(exc)})

    result = {
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "total": len(urls),
        "succeeded": len(manifest),
        "failed": len(failed),
        "manifest": manifest,
        "failures": failed,
    }

    save_json(settings.RAW_DATA_DIR / "raw_manifest.json", result)
    return result


def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    try:
        result = crawl_pages()
        logger.info(
            "Crawl complete. success=%d failed=%d",
            result["succeeded"],
            result["failed"],
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Crawling failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
