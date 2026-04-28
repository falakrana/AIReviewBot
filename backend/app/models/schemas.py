from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CodeChunk(BaseModel):
    file: str
    name: str
    type: str  # 'function', 'class', 'method'
    code: str
    start_line: int
    end_line: int

class AnalysisIssue(BaseModel):
    bugs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    performance_issues: List[str] = Field(default_factory=list)
    security_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    improved_code: Optional[str] = None

class ChunkAnalysisResult(BaseModel):
    chunk_name: str
    chunk_type: str
    file: str
    start_line: int
    analysis: AnalysisIssue

class FileSummary(BaseModel):
    total_issues: int = 0
    critical_issues: int = 0  # Sum of bugs and security_issues
    warnings: int = 0
    performance: int = 0
    suggestions: int = 0

class FileAnalysisResult(BaseModel):
    file: str
    summary: FileSummary
    details: List[ChunkAnalysisResult]

class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    results: List[FileAnalysisResult]

# ---------------------------------------------------------------------------
# Phase 3 — Job tracking schemas
# ---------------------------------------------------------------------------

class JobSubmitResponse(BaseModel):
    """Returned immediately by POST /analyze."""
    job_id:  str
    status:  str = "pending"
    message: str
    tracking: Dict[str, str]

class JobStatusResponse(BaseModel):
    """Returned by GET /status/{job_id}."""
    job_id:           str
    status:           str
    progress:         float
    message:          Optional[str] = None
    filename:         Optional[str] = None
    total_chunks:     int = 0
    processed_chunks: int = 0
    created_at:       Optional[str] = None
    updated_at:       Optional[str] = None
    completed_at:     Optional[str] = None

class JobListResponse(BaseModel):
    """Returned by GET /jobs."""
    count: int
    jobs:  List[Dict[str, Any]]

