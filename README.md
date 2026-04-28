# AI Codebase Reviewer

An AI-powered codebase review system that analyzes uploaded project archives (.zip) using tree-sitter for parsing and Groq (Llama) for generating structured feedback. The system uses an asynchronous architecture with Celery and Redis to handle large projects efficiently.

## Features

- **Asynchronous Processing**: Non-blocking API that handles project analysis in the background via Celery.
- **Project Uploads**: Accepts `.zip` archives containing project source code.
- **Multi-language Support**: Parses Python, JavaScript, TypeScript, Java, C, and C++ files using `tree-sitter`.
- **Intelligent Chunking**: Chunks code by parsing functions and classes to stay within LLM context limits.
- **Intelligent Caching**: Uses Redis to cache analysis results for code chunks (SHA-256), preventing redundant LLM calls.
- **Job Tracking**: Persistent job status and results stored in SQLite (or PostgreSQL).
- **AI-Powered Analysis**: Utilizes Groq (Llama 3.1) to identify bugs, security vulnerabilities, performance bottlenecks, and structural warnings.

## Tech Stack

- **Backend**: FastAPI, Python 3.12+
- **Task Queue**: Celery + Redis
- **Database**: SQLAlchemy (SQLite default)
- **Parsing**: `tree-sitter`
- **AI Integration**: `groq` Python SDK
- **Dependency Management**: Poetry

## Prerequisites

- Python 3.12 or higher
- [Poetry](https://python-poetry.org/)
- **Redis** (for Celery and Caching)
- Groq API Key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/falakrana/AIReviewBot.git
   cd AIReviewBot
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables (`.env`):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   REDIS_URL=redis://localhost:6379/0
   DATABASE_URL=sqlite:///./storage/aireviewbot.db
   ```

## Usage

You need to run two processes:

1. **Start the API Server**:
   ```bash
   poetry run python -m backend.app.main
   ```

2. **Start the Celery Worker**:
   ```bash
   # Windows
   poetry run celery -A backend.app.workers.celery_app.celery_app worker --loglevel=info --pool=solo

   # Linux/Mac
   poetry run celery -A backend.app.workers.celery_app.celery_app worker --loglevel=info
   ```

## API Reference

- `POST /api/v1/analyze`: Submit a ZIP file for analysis (returns `job_id`).
- `GET /api/v1/status/{job_id}`: Check analysis progress.
- `GET /api/v1/result/{job_id}`: Fetch the final analysis report.
- `GET /api/v1/jobs`: List recent analysis jobs.

## Documentation

For a detailed walkthrough of the architecture and setup, see [walkthrough.md](./walkthrough.md).
