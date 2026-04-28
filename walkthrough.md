# 🚀 AI Codebase Review System — Setup & Usage Guide

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | FastAPI + Tree-sitter parsing | ✅ Done |
| 2 | Real LLM integration (Groq) | ✅ Done |
| 3 | Async job queue + DB + caching | ✅ Done |
| 4 | Interactive Frontend (React/Next.js) | ⏳ Planned |

---

## 📁 Project Structure (Phase 3)

```
AIReviewBot/
├── .env
├── pyproject.toml
├── storage/                        ← uploaded ZIPs + SQLite DB live here
└── backend/
    └── app/
        ├── main.py                 ← FastAPI app (lifespan, routers, /health)
        ├── config.py               ← All settings (Pydantic BaseSettings)
        ├── models/
        │   └── schemas.py          ← Pydantic models incl. Job schemas
        ├── routes/
        │   ├── analyzer_controller.py  ← POST /analyze (non-blocking)
        │   └── job_controller.py       ← GET /status, /result, /jobs
        ├── services/
        │   ├── parser_service.py   ← Tree-sitter multi-language parser
        │   ├── chunking_service.py ← Function/class chunker
        │   ├── analyzer_service.py ← Groq LLM integration + retry logic
        │   ├── job_service.py      ← Job CRUD (DB operations)
        │   └── cache_service.py    ← Redis cache (hash → result)
        ├── workers/
        │   ├── celery_app.py       ← Celery config (Windows: solo pool)
        │   └── tasks.py            ← analyze_project_task (parallel)
        ├── db/
        │   ├── database.py         ← SQLAlchemy engine + session factory
        │   └── models.py           ← Job ORM model
        └── utils/
            └── file_utils.py       ← save/extract/cleanup helpers
```

---

## 🛠️ Prerequisites

- Python 3.10+
- Poetry (`pip install poetry`)
- **Redis** — required for Celery broker and caching

### Install Redis on Windows

**Option A — Docker (recommended):**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Option B — Windows binary:**
Download from https://github.com/microsoftarchive/redis/releases
Run `redis-server.exe`

---

## 📦 Installation

```bash
# From the project root
poetry install
```

---

## ⚙️ Environment Variables (`.env`)

```env
# LLM
GROQ_API_KEY=your_key_here
MODEL_NAME=llama-3.1-8b-instant
MAX_RETRIES=3
RETRY_DELAY=2

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=86400              # seconds (24 hours)

# Database (SQLite default; swap to PostgreSQL DSN for production)
DATABASE_URL=sqlite:///./storage/aireviewbot.db

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Parallel Workers
MAX_PARALLEL_CHUNKS=5
```

---

## 🏃 Running the System

You need **two** terminal windows.

### Terminal 1 — FastAPI server
```bash
# From project root
poetry run python -m backend.app.main
```
Server starts at `http://localhost:8000`

### Terminal 2 — Celery worker
```bash
# From project root
poetry run celery -A backend.app.workers.celery_app.celery_app worker --loglevel=info --pool=solo
```

> **Windows note:** `--pool=solo` is required. On Linux you can omit it.

---

## 🔌 API Reference

### POST `/api/v1/analyze` — Submit a job
Upload a `.zip` file. Returns immediately with a `job_id`.

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
     -F "file=@my_project.zip"
```

**Response (HTTP 202):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "message": "Job queued. Use the URLs below to track progress.",
  "tracking": {
    "status_url": "/api/v1/status/3fa85f64-...",
    "result_url": "/api/v1/result/3fa85f64-..."
  }
}
```

---

### GET `/api/v1/status/{job_id}` — Poll progress

```bash
curl http://localhost:8000/api/v1/status/3fa85f64-...
```

**Response:**
```json
{
  "job_id": "3fa85f64-...",
  "status": "analyzing",
  "progress": 42.5,
  "message": "Analysing 24 code chunks in parallel…",
  "filename": "my_project.zip",
  "total_chunks": 24,
  "processed_chunks": 10,
  "created_at": "2024-01-01T12:00:00+00:00",
  "updated_at": "2024-01-01T12:00:05+00:00"
}
```

**Status values:**

| Status | Meaning |
|--------|---------|
| `pending` | Queued, not yet started |
| `parsing` | Worker scanning source files |
| `analyzing` | LLM reviewing chunks (progress updates) |
| `completed` | Done — fetch result |
| `failed` | Error — check `error` field |

---

### GET `/api/v1/result/{job_id}` — Fetch final report

```bash
curl http://localhost:8000/api/v1/result/3fa85f64-...
```

**Response (completed):**
```json
{
  "job_id": "3fa85f64-...",
  "status": "completed",
  "filename": "my_project.zip",
  "total_files": 3,
  "total_chunks": 12,
  "results": [
    {
      "file": "app/main.py",
      "summary": {
        "total_issues": 5,
        "critical_issues": 1,
        "warnings": 2,
        "performance": 1,
        "suggestions": 1
      },
      "details": [
        {
          "chunk_name": "process_data",
          "chunk_type": "function",
          "file": "app/main.py",
          "start_line": 12,
          "analysis": {
            "bugs": ["Missing null-check on input"],
            "warnings": ["Bare except clause"],
            "performance_issues": [],
            "security_issues": [],
            "suggestions": ["Add type hints"],
            "improved_code": "def process_data(data: dict) -> str:\n    ..."
          }
        }
      ]
    }
  ]
}
```

Returns **HTTP 202** if still in progress, **HTTP 500** if failed.

---

### GET `/api/v1/jobs` — List recent jobs

```bash
curl "http://localhost:8000/api/v1/jobs?limit=10&offset=0"
```

---

### GET `/health` — Liveness probe

```bash
curl http://localhost:8000/health
```
```json
{ "status": "ok", "cache": "connected", "db": "sqlite" }
```

---

## 🧠 Architecture: How Phase 3 Works

```
Client
  │
  ▼  POST /analyze (ZIP)
FastAPI ──► Save & Extract ZIP
         ──► Create Job record (SQLite)
         ──► celery.delay(job_id)   ← returns job_id immediately
  │
  │  (background)
  ▼
Celery Worker
  ├─ status: parsing
  │    └─ Tree-sitter parses all files → CodeChunks
  ├─ status: analyzing
  │    └─ ThreadPoolExecutor (5 threads)
  │         ├─ chunk 1 → Redis cache? HIT → reuse ✓
  │         ├─ chunk 2 → Redis cache? MISS → Groq LLM
  │         ├─ chunk 3 → Redis cache? MISS → Groq LLM
  │         └─ ... (progress updated after each chunk)
  └─ status: completed
       └─ Aggregate → store JSON result in SQLite

Client polls GET /status/{id}   ← reads SQLite (always fast)
Client fetches GET /result/{id} ← reads JSON blob from SQLite
```

---

## 🧪 Test Scenarios

### 1. Normal flow
```bash
# Submit
JOB=$(curl -s -X POST http://localhost:8000/api/v1/analyze -F "file=@sample.zip" | python -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

# Poll until done
watch -n 2 "curl -s http://localhost:8000/api/v1/status/$JOB | python -m json.tool"

# Fetch result
curl http://localhost:8000/api/v1/result/$JOB | python -m json.tool
```

### 2. Cache hit test
Submit the same ZIP twice. The second run should complete much faster — all chunks served from Redis cache.

### 3. Multiple concurrent jobs
```bash
for i in 1 2 3; do
  curl -X POST http://localhost:8000/api/v1/analyze -F "file=@sample.zip" &
done
```
All three get unique `job_id`s and process in parallel via Celery.

---

## 🗄️ Database Schema

**Table: `jobs`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PK | UUID job identifier |
| `status` | VARCHAR(20) | pending/parsing/analyzing/completed/failed |
| `progress` | FLOAT | 0.0 – 100.0 |
| `message` | VARCHAR(512) | Human-readable status message |
| `filename` | VARCHAR(512) | Original ZIP filename |
| `upload_path` | VARCHAR(512) | Server-side storage path |
| `total_chunks` | INTEGER | Total code chunks found |
| `processed_chunks` | INTEGER | Chunks analysed so far |
| `result` | JSON | Full analysis result (set on completion) |
| `error` | TEXT | Error message (set on failure) |
| `created_at` | DATETIME | Job creation time |
| `updated_at` | DATETIME | Last update time |
| `completed_at` | DATETIME | Completion time |

To switch to **PostgreSQL**, set in `.env`:
```env
DATABASE_URL=postgresql+psycopg2://user:pass@localhost/aireviewbot
```
Then run `poetry add psycopg2-binary`.

---

## 🧩 Module Breakdown

| File | Role |
|------|------|
| `main.py` | FastAPI app, lifespan startup, CORS, /health |
| `config.py` | All settings via Pydantic BaseSettings |
| `analyzer_controller.py` | Non-blocking POST /analyze |
| `job_controller.py` | GET /status, /result, /jobs |
| `job_service.py` | DB CRUD for Job records |
| `cache_service.py` | Redis cache (SHA-256 key → JSON result) |
| `celery_app.py` | Celery broker/backend config |
| `tasks.py` | Background task with parallel ThreadPoolExecutor |
| `db/database.py` | SQLAlchemy engine + init_db() |
| `db/models.py` | Job ORM model |
| `parser_service.py` | Tree-sitter multi-language parser |
| `chunking_service.py` | Function/class chunk builder |
| `analyzer_service.py` | Groq LLM client + retry logic |
