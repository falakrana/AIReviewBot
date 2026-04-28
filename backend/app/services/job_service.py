"""
CRUD operations for Job records.

All functions open their own short-lived session so they can be called safely
from both FastAPI request handlers AND Celery workers (different threads/processes).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.app.db.database import SessionLocal
from backend.app.db import models

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_to_dict(job: models.Job) -> dict:
    return {
        "job_id":           job.id,
        "status":           job.status,
        "progress":         job.progress,
        "message":          job.message,
        "filename":         job.filename,
        "upload_path":      job.upload_path,
        "total_chunks":     job.total_chunks,
        "processed_chunks": job.processed_chunks,
        "result":           job.result,
        "error":            job.error,
        "created_at":       job.created_at.isoformat() if job.created_at else None,
        "updated_at":       job.updated_at.isoformat() if job.updated_at else None,
        "completed_at":     job.completed_at.isoformat() if job.completed_at else None,
    }


def _get_job_row(db, job_id: str) -> Optional[models.Job]:
    return db.query(models.Job).filter(models.Job.id == job_id).first()


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def create_job(filename: str, upload_path: str) -> str:
    """Persist a new job record and return the generated job_id."""
    job_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        job = models.Job(
            id=job_id,
            status="pending",
            progress=0.0,
            filename=filename,
            upload_path=upload_path,
        )
        db.add(job)
        db.commit()
        logger.info(f"[JobService] Created job {job_id} for '{filename}'")
        return job_id
    finally:
        db.close()


def update_job_status(
    job_id: str,
    status: str,
    progress: Optional[float] = None,
    message: Optional[str] = None,
) -> None:
    """Update status, optionally progress % and a human-readable message."""
    db = SessionLocal()
    try:
        job = _get_job_row(db, job_id)
        if not job:
            logger.warning(f"[JobService] update_job_status: job {job_id} not found")
            return
        job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def update_job_progress(job_id: str, processed: int, total: int) -> None:
    """Recalculate progress % from processed/total chunk counters."""
    db = SessionLocal()
    try:
        job = _get_job_row(db, job_id)
        if not job:
            return
        job.processed_chunks = processed
        job.total_chunks = total
        job.progress = round((processed / total) * 100, 1) if total > 0 else 0.0
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def complete_job(job_id: str, result: dict) -> None:
    """Mark a job completed and store the JSON result blob."""
    db = SessionLocal()
    try:
        job = _get_job_row(db, job_id)
        if not job:
            return
        job.status = "completed"
        job.progress = 100.0
        job.result = result
        now = datetime.now(timezone.utc)
        job.completed_at = now
        job.updated_at = now
        db.commit()
        logger.info(f"[JobService] Job {job_id} completed.")
    finally:
        db.close()


def fail_job(job_id: str, error: str) -> None:
    """Mark a job as failed with an error message."""
    db = SessionLocal()
    try:
        job = _get_job_row(db, job_id)
        if not job:
            return
        job.status = "failed"
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"[JobService] Job {job_id} failed: {error}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_job(job_id: str) -> Optional[dict]:
    """Return job metadata dict, or None if not found."""
    db = SessionLocal()
    try:
        job = _get_job_row(db, job_id)
        return _job_to_dict(job) if job else None
    finally:
        db.close()


def list_jobs(limit: int = 20, offset: int = 0) -> list[dict]:
    """Return recent jobs ordered by creation time (newest first)."""
    db = SessionLocal()
    try:
        jobs = (
            db.query(models.Job)
            .order_by(models.Job.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [_job_to_dict(j) for j in jobs]
    finally:
        db.close()
