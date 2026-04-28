"""
AI Codebase Review System — Phase 3
FastAPI application entry point.

Startup sequence:
  1. init_db()  — creates SQLite tables if they don't exist yet
  2. Router registration
     - /api/v1/analyze      (submit job)
     - /api/v1/status/{id}  (poll status)
     - /api/v1/result/{id}  (fetch result)
     - /api/v1/jobs         (list jobs)
  3. /health                (liveness probe)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.database import init_db
from backend.app.routes import analyzer_controller, job_controller
from backend.app.services.cache_service import cache_service


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown — nothing to clean up


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Codebase Review System",
    version="3.0.0",
    description=(
        "Phase 3 — Scalable async code review powered by Celery + Redis + SQLite. "
        "Submit a ZIP, get a job_id, poll progress, fetch results."
    ),
    lifespan=lifespan,
)

# Allow all origins for local development (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(analyzer_controller.router, prefix="/api/v1")
app.include_router(job_controller.router,      prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root & Health
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "AI Codebase Review System",
        "version": "3.0.0",
        "phase":   "Phase 3 — Scalability & Production Readiness",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Liveness probe.

    Returns Redis / DB availability so you can monitor dependencies.
    """
    return {
        "status": "ok",
        "cache":  "connected" if cache_service.is_healthy() else "unavailable",
        "db":     "sqlite",
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
