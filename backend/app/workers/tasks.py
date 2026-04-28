"""
Background Celery task: analyze_project_task

Flow:
    pending → parsing → analyzing → completed
                                  ↘ failed

Parallel processing:
    All code chunks are submitted to a ThreadPoolExecutor so multiple
    Groq API calls run concurrently (I/O-bound → threads are ideal).
    MAX_PARALLEL_CHUNKS controls the thread pool size (default 5).

Caching:
    Before calling the LLM, cache_service.get(code) is checked.
    On a cache hit the stored AnalysisIssue dict is returned immediately,
    skipping the API call entirely.  Results are cached after every
    successful analysis.
"""
import os
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.app.workers.celery_app import celery_app
from backend.app.services.parser_service import ParserService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.analyzer_service import AnalyzerService
from backend.app.services.cache_service import cache_service
from backend.app.services import job_service
from backend.app.models.schemas import (
    CodeChunk,
    AnalysisIssue,
    ChunkAnalysisResult,
    FileAnalysisResult,
    FileSummary,
)
from backend.app.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".c", ".cpp", ".cc", ".hpp", ".h",
)


# ---------------------------------------------------------------------------
# Helper: analyse one chunk (with cache check)
# ---------------------------------------------------------------------------

def _analyse_chunk(
    chunk: CodeChunk,
    analyzer: AnalyzerService,
) -> tuple[CodeChunk, AnalysisIssue]:
    """
    Try the cache first; fall back to the LLM.
    Thread-safe: each call has its own stack frame; the shared
    AnalyzerService.client (Groq HTTP client) is stateless.
    """
    cached = cache_service.get(chunk.code)
    if cached:
        logger.info(f"[Cache HIT] {chunk.file}::{chunk.name}")
        return chunk, AnalysisIssue(**cached)

    logger.info(f"[LLM]       {chunk.file}::{chunk.name}")
    result = analyzer.analyze_code(chunk)

    # Store result in cache for future jobs
    cache_service.set(chunk.code, result.model_dump())
    return chunk, result


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="analyze_project_task")
def analyze_project_task(self, job_id: str, extract_dir: str, filename: str):
    """
    Main background task.

    Args:
        job_id:      UUID string matching a Job row in the database.
        extract_dir: Absolute path to the already-extracted project directory.
        filename:    Original ZIP filename (for metadata only).
    """
    logger.info(f"[Task] Job {job_id} started — '{filename}'")

    try:
        # ------------------------------------------------------------------
        # Phase A: Parsing
        # ------------------------------------------------------------------
        job_service.update_job_status(
            job_id, "parsing", 5.0, "Scanning and parsing source files…"
        )

        parser = ParserService()
        chunker = ChunkingService()
        analyzer = AnalyzerService()

        all_chunks: list[CodeChunk] = []
        file_chunk_map: dict[str, list[CodeChunk]] = defaultdict(list)

        for root, _dirs, files in os.walk(extract_dir):
            for fname in files:
                if not fname.lower().endswith(SUPPORTED_EXTENSIONS):
                    continue
                file_path = os.path.join(root, fname)
                relative_path = os.path.relpath(file_path, extract_dir)
                try:
                    extracted = parser.parse_file(file_path, relative_path)
                    chunks = chunker.create_chunks(extracted)
                    all_chunks.extend(chunks)
                    file_chunk_map[relative_path].extend(chunks)
                except Exception as exc:
                    logger.error(f"[Task] Parse error {relative_path}: {exc}")

        total_chunks = len(all_chunks)
        logger.info(
            f"[Task] Job {job_id}: {total_chunks} chunks across "
            f"{len(file_chunk_map)} files"
        )

        if total_chunks == 0:
            job_service.complete_job(
                job_id,
                {
                    "job_id": job_id,
                    "status": "completed",
                    "filename": filename,
                    "total_files": 0,
                    "total_chunks": 0,
                    "results": [],
                    "message": "No supported code chunks found in the uploaded project.",
                },
            )
            return

        # ------------------------------------------------------------------
        # Phase B: Parallel LLM analysis
        # ------------------------------------------------------------------
        job_service.update_job_status(
            job_id,
            "analyzing",
            10.0,
            f"Analysing {total_chunks} code chunks in parallel…",
        )
        job_service.update_job_progress(job_id, 0, total_chunks)

        # results_map: file_path → list of (CodeChunk, AnalysisIssue)
        results_map: dict[str, list[tuple[CodeChunk, AnalysisIssue]]] = defaultdict(list)
        processed = 0

        with ThreadPoolExecutor(max_workers=settings.MAX_PARALLEL_CHUNKS) as pool:
            future_to_chunk = {
                pool.submit(_analyse_chunk, chunk, analyzer): chunk
                for chunk in all_chunks
            }

            for future in as_completed(future_to_chunk):
                original_chunk = future_to_chunk[future]
                try:
                    chunk, analysis = future.result()
                except Exception as exc:
                    logger.error(
                        f"[Task] Chunk failed {original_chunk.name}: {exc}"
                    )
                    chunk = original_chunk
                    analysis = AnalysisIssue(
                        bugs=[f"Analysis failed: {exc}"],
                        suggestions=["Check API limits or network connectivity."],
                    )

                results_map[chunk.file].append((chunk, analysis))
                processed += 1
                job_service.update_job_progress(job_id, processed, total_chunks)

        # ------------------------------------------------------------------
        # Phase C: Aggregate results per file
        # ------------------------------------------------------------------
        final_results = []

        for file_path, chunk_tuples in results_map.items():
            summary = FileSummary()
            chunk_results = []

            for chunk, analysis in chunk_tuples:
                summary.total_issues += (
                    len(analysis.bugs)
                    + len(analysis.warnings)
                    + len(analysis.performance_issues)
                    + len(analysis.security_issues)
                    + len(analysis.suggestions)
                )
                summary.critical_issues += (
                    len(analysis.bugs) + len(analysis.security_issues)
                )
                summary.warnings    += len(analysis.warnings)
                summary.performance += len(analysis.performance_issues)
                summary.suggestions += len(analysis.suggestions)

                chunk_results.append(
                    ChunkAnalysisResult(
                        chunk_name=chunk.name,
                        chunk_type=chunk.type,
                        file=chunk.file,
                        start_line=chunk.start_line,
                        analysis=analysis,
                    ).model_dump()
                )

            final_results.append(
                FileAnalysisResult(
                    file=file_path,
                    summary=summary,
                    details=[ChunkAnalysisResult(**cr) for cr in chunk_results],
                ).model_dump()
            )

        # ------------------------------------------------------------------
        # Phase D: Persist and mark complete
        # ------------------------------------------------------------------
        result_payload = {
            "job_id":       job_id,
            "status":       "completed",
            "filename":     filename,
            "total_files":  len(final_results),
            "total_chunks": total_chunks,
            "results":      final_results,
        }

        job_service.complete_job(job_id, result_payload)
        logger.info(f"[Task] Job {job_id} completed successfully.")

    except Exception as exc:
        logger.error(f"[Task] Job {job_id} FAILED: {exc}", exc_info=True)
        job_service.fail_job(job_id, str(exc))
        # Do NOT retry at task level — LLM retries are handled inside
        # AnalyzerService.analyze_code().  A task-level failure means
        # something structural went wrong (bad zip, DB down, etc.).
        raise
