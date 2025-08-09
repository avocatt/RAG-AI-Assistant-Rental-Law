# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) AI assistant application that answers questions about Turkish tenancy law, specifically the Housing and Roofed Workplace Rentals section of the Turkish Code of Obligations (TBK). The application uses a FastAPI backend for AI processing and a Streamlit frontend for user interaction.

## Architecture

**Two-service architecture:**
- **Backend (FastAPI)**: Handles ChromaDB vector database queries, OpenAI API interactions, and legal document retrieval (`main.py`)
- **Frontend (Streamlit)**: Provides password-protected user interface that communicates with backend via REST API (`app_ui.py`)

**Key Components:**
- `legal_parser.py`: Parses Turkish legal text into structured articles with regex patterns for MADDE (article) identification
- `ingest_data.py`: Processes legal documents and stores them in ChromaDB vector database with OpenAI embeddings
- `source_data/TBK_Konut_ve_Catili_Isyeri_Kiralari.txt`: Source legal text file
- `chroma_db_store/`: Persistent ChromaDB vector database storage
- `parsed_articles.json`: Structured output from legal text parsing

## Common Development Commands

**Initial Setup:**
```bash
pip install -r requirements.txt
python ingest_data.py  # Create vector database from legal documents
```

**Development Servers:**
```bash
# Backend (port 8000)
uvicorn main:app --reload

# Frontend (port 8501) - in separate terminal
streamlit run app_ui.py
```

**Environment Configuration:**
Create `.env` file with:
```
OPENAI_API_KEY="your_openai_api_key_here"
DEMO_PASSWORD="your_secret_demo_password_here"
```

## Key Configuration

- **ChromaDB Collection**: `tbk_kira_articles` (configured in both `main.py` and `ingest_data.py`)
- **Embedding Model**: `text-embedding-ada-002` (OpenAI)
- **LLM Model**: `gpt-3.5-turbo` (configurable to `gpt-4o` in `main.py:17`)
- **Backend URL**: `http://127.0.0.1:8000/query` (configured in `app_ui.py:9`)
- **Retrieval**: Top 3 similar documents (`TOP_K_RESULTS = 3`)

## Development Container

The project includes devcontainer configuration (`.devcontainer/devcontainer.json`) with:
- Python 3.11 base image
- Auto-installation of requirements
- Streamlit server auto-start on port 8501
- VS Code Python extensions pre-configured

## Legal Text Processing

The `legal_parser.py` uses regex patterns to identify:
- Article headers: `MADDE \d+` pattern
- Structured content: Roman numerals, letters, and numbered subsections
- Article boundaries and content extraction

When modifying legal text processing, ensure compatibility with Turkish legal document structure and UTF-8 encoding.

## Database Operations

- **Ingestion**: Run `python ingest_data.py` after modifying source documents
- **Storage**: ChromaDB persists in `./chroma_db_store/` directory
- **Queries**: Vector similarity search with OpenAI embeddings for semantic matching

## Security Notes

- Frontend implements password protection via `DEMO_PASSWORD` environment variable
- OpenAI API key is managed securely in backend only
- No sensitive information should be committed to repository