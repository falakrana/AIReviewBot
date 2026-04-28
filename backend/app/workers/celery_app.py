"""
Celery application factory.

Windows note:
    The default 'prefork' pool does not work on Windows.
    We explicitly set worker_pool='solo' which runs tasks in the same
    process/thread — fully functional for development and light production.
    For high throughput on Linux, remove the worker_pool override and let
    Celery use 'prefork' (default).
"""
from celery import Celery
from backend.app.config import settings

celery_app = Celery(
    "aireviewbot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.app.workers.tasks"],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_track_started=True,
    task_acks_late=True,         # ack only after task completes
    worker_prefetch_multiplier=1, # one task at a time per worker process

    # Windows-compatible pool (no fork())
    worker_pool="solo",

    # Timeouts
    task_soft_time_limit=300,    # raises SoftTimeLimitExceeded after 5 min
    task_time_limit=600,         # hard kill after 10 min

    # Result expiry
    result_expires=3600,         # keep Celery backend results for 1 h
)
