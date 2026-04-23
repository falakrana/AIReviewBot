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
