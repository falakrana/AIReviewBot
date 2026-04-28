"""
POST /analyze  — submit a project ZIP for async background analysis.

The endpoint:
  1. Validates & saves the uploaded ZIP
  2. Extracts it to a session-scoped directory
  3. Creates a Job record in the DB
  4. Dispatches the Celery background task
  5. Returns job_id immediately (non-blocking)
"""
import os
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.services import job_service
from backend.app.workers.tasks import analyze_project_task
from backend.app.utils.file_utils import save_upload_file, extract_zip

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze", status_code=202)
async def submit_analysis(file: UploadFile = File(...)):
    """
    Submit a project ZIP file for asynchronous AI code review.

    Returns a **job_id** immediately. Poll `/status/{job_id}` for progress
    and fetch the final report from `/result/{job_id}`.

    Example response:
    ```json
    {
      "job_id": "3fa85f64-...",
      "status": "pending",
      "message": "Job queued. Use the URLs below to track progress.",
      "tracking": {
        "status_url": "/api/v1/status/3fa85f64-...",
        "result_url": "/api/v1/result/3fa85f64-..."
      }
    }
    ```
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only .zip archives are accepted.",
        )

    session_id = str(uuid.uuid4())
    upload_path = os.path.join("storage", session_id)
    os.makedirs(upload_path, exist_ok=True)

    zip_path = os.path.join(upload_path, file.filename)

    # --- Save & extract ---
    try:
        save_upload_file(file, zip_path)
        extract_dir = os.path.join(upload_path, "project")
        extract_zip(zip_path, extract_dir)
    except Exception as exc:
        logger.error(f"Upload/extract failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process the uploaded archive: {exc}",
        )

    # --- Create DB record ---
    job_id = job_service.create_job(
        filename=file.filename,
        upload_path=upload_path,
    )

    # --- Dispatch Celery task (non-blocking) ---
    analyze_project_task.delay(job_id, extract_dir, file.filename)

    logger.info(f"Job {job_id} queued for '{file.filename}'")

    return {
        "job_id":  job_id,
        "status":  "pending",
        "message": "Job queued. Use the URLs below to track progress.",
        "tracking": {
            "status_url": f"/api/v1/status/{job_id}",
            "result_url": f"/api/v1/result/{job_id}",
        },
    }
