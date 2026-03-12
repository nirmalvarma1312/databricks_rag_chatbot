"""Shared utility helpers for file IO, text normalization, and IDs."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any


LOGGER_NAME = "databricks_rag"


def setup_logging() -> None:
    """Configure application-wide logging once."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: Any) -> None:
    """Save data to JSON with UTF-8 encoding and pretty formatting."""
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Any:
    """Load JSON data from path."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    """Normalize whitespace for cleaner chunking and embeddings."""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def safe_filename(value: str) -> str:
    """Convert a string into a filesystem-safe filename."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9._-]+", "_", value)
    return value.strip("_") or "document"


def generate_id(value: str, length: int = 16) -> str:
    """Generate a deterministic short ID from string input."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]
