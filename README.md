# Databricks Documentation RAG Chatbot

## Project Overview
This project builds an end-to-end Retrieval-Augmented Generation (RAG) chatbot over official Databricks documentation.
It ingests documentation URLs from the Databricks sitemap, crawls and parses pages, chunks text, embeds chunks with OpenAI, stores vectors in ChromaDB, retrieves relevant chunks for user questions, and generates grounded answers with source citations.

## Architecture Summary
1. `ingestion/fetch_sitemap.py`: fetch and filter Databricks docs URLs.
2. `ingestion/crawl_pages.py`: download raw HTML pages.
3. `ingestion/parse_html.py`: clean and extract title + text + metadata.
4. `ingestion/chunker.py`: deterministic chunking with overlap.
5. `rag/embed_store.py`: OpenAI embeddings + persistent Chroma storage.
6. `rag/retriever.py`: query embedding + top-k vector retrieval.
7. `rag/prompt_builder.py`: strict grounded prompt assembly.
8. `app/chatbot.py`: retrieve -> prompt -> LLM -> citations.
9. `app/main.py`: Streamlit interface.

## Folder Structure
```text
databricks_rag_chatbot/
  app/
    main.py
    chatbot.py
  ingestion/
    fetch_sitemap.py
    crawl_pages.py
    parse_html.py
    chunker.py
  rag/
    embed_store.py
    retriever.py
    prompt_builder.py
  utils/
    helpers.py
    models.py
  data/
    raw/
    processed/
    chunks/
  db/
  logs/
  tests/
    test_chunker.py
    test_retriever.py
  config.py
  requirements.txt
  .env.example
  README.md
  AGENTS.md
```

## Setup
### 1) Create virtual environment
```bash
cd ~/Desktop/RAG/databricks_rag_chatbot
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Set environment variables
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

## Exact Command Order
1. Fetch sitemap URLs
```bash
python -m ingestion.fetch_sitemap
```
2. Crawl pages
```bash
python -m ingestion.crawl_pages
```
3. Parse HTML
```bash
python -m ingestion.parse_html
```
4. Chunk documents
```bash
python -m ingestion.chunker
```
5. Embed and store in Chroma
```bash
python -m rag.embed_store
```
6. Run Streamlit app
```bash
streamlit run app/main.py
```

## Example Query
`What is Unity Catalog in Databricks and why is it used?`

## Known Limitations
- HTML structure changes in docs pages can reduce parsing quality.
- Paragraph-aware chunking can still split content on very long sections.
- Retrieval quality depends on indexed coverage and embedding model.
- No reranking stage in v1.


## I used the below site to fetch the documents from the XML file.
https://docs.databricks.com/en/doc-sitemap.xml