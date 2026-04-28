"""
ORM models for persisting job metadata and results.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from backend.app.db.database import Base


class Job(Base):
    """
    Stores the full lifecycle of one analysis job.

    status lifecycle:
        pending  →  parsing  →  analyzing  →  completed
                                           ↘  failed
    """
    __tablename__ = "jobs"

    id               = Column(String(36),  primary_key=True, index=True)
    status           = Column(String(20),  nullable=False, default="pending")
    progress         = Column(Float,       nullable=False, default=0.0)
    message          = Column(String(512), nullable=True)

    # Upload metadata
    filename         = Column(String(512), nullable=True)
    upload_path      = Column(String(512), nullable=True)

    # Chunk counters (used to compute progress %)
    total_chunks     = Column(Integer, nullable=False, default=0)
    processed_chunks = Column(Integer, nullable=False, default=0)

    # Final aggregated result (JSON blob)
    result           = Column(JSON, nullable=True)

    # Error info when status == "failed"
    error            = Column(Text, nullable=True)

    # Timestamps
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    completed_at     = Column(DateTime(timezone=True), nullable=True)
