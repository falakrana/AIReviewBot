"""
Job tracking endpoints:

  GET /status/{job_id}  — live status + progress
  GET /result/{job_id}  — final analysis result (only when completed)
  GET /jobs             — list recent jobs
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from backend.app.services import job_service

router = APIRouter(tags=["Jobs"])
logger = logging.getLogger(__name__)

_IN_PROGRESS = {"pending", "parsing", "analyzing"}


# ---------------------------------------------------------------------------
# GET /status/{job_id}
# ---------------------------------------------------------------------------

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Returns current status and progress for a job.

    Possible status values:
    - **pending**   — job is in the queue, not yet started
    - **parsing**   — worker is reading and parsing source files
    - **analyzing** — LLM is reviewing code chunks
    - **completed** — analysis finished; fetch result via `/result/{job_id}`
    - **failed**    — unrecoverable error; check the `error` field

    Example response:
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
    """
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return {
        "job_id":           job["job_id"],
        "status":           job["status"],
        "progress":         job["progress"],
        "message":          job["message"],
        "filename":         job["filename"],
        "total_chunks":     job["total_chunks"],
        "processed_chunks": job["processed_chunks"],
        "created_at":       job["created_at"],
        "updated_at":       job["updated_at"],
        "completed_at":     job["completed_at"],
    }


# ---------------------------------------------------------------------------
# GET /result/{job_id}
# ---------------------------------------------------------------------------

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    """
    Returns the full analysis report for a **completed** job.

    - Returns **HTTP 202** if the job is still in progress.
    - Returns **HTTP 500** if the job failed.
    - Returns **HTTP 404** if the job_id is unknown.

    Example (completed) response:
    ```json
    {
      "job_id": "3fa85f64-...",
      "status": "completed",
      "filename": "my_project.zip",
      "total_files": 3,
      "total_chunks": 12,
      "results": [
        {
          "file": "main.py",
          "summary": { "total_issues": 4, "critical_issues": 1, ... },
          "details": [ ... ]
        }
      ]
    }
    ```
    """
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    if job["status"] in _IN_PROGRESS:
        raise HTTPException(
            status_code=202,
            detail={
                "message":  "Analysis is still in progress.",
                "status":   job["status"],
                "progress": job["progress"],
            },
        )

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Analysis job failed.",
                "error":   job["error"],
            },
        )

    return job["result"]


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------

@router.get("/jobs")
async def list_jobs(
    limit:  int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0,  ge=0,         description="Pagination offset"),
):
    """
    Returns a paginated list of recent analysis jobs (newest first).

    Example response:
    ```json
    {
      "count": 3,
      "jobs": [
        { "job_id": "...", "status": "completed", "progress": 100, ... },
        ...
      ]
    }
    ```
    """
    jobs = job_service.list_jobs(limit=limit, offset=offset)
    return {"count": len(jobs), "jobs": jobs}
