"""Global configuration for the Databricks docs RAG chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
DOTENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "gpt-4.1-mini")

    CHROMA_DIR: Path = Path(os.getenv("CHROMA_DIR", "./db/chroma"))
    RAW_DATA_DIR: Path = Path(os.getenv("RAW_DATA_DIR", "./data/raw"))
    PROCESSED_DATA_DIR: Path = Path(os.getenv("PROCESSED_DATA_DIR", "./data/processed"))
    CHUNKS_DATA_DIR: Path = Path(os.getenv("CHUNKS_DATA_DIR", "./data/chunks"))

    SITEMAP_URL: str = os.getenv(
        "SITEMAP_URL", "https://docs.databricks.com/en/doc-sitemap.xml"
    )

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "20"))


settings = Settings()
