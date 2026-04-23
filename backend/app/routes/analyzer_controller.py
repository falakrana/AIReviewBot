from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.models.schemas import AnalysisResponse, FileAnalysisResult, ChunkAnalysisResult, FileSummary
from backend.app.services.parser_service import ParserService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.analyzer_service import AnalyzerService
from backend.app.utils.file_utils import save_upload_file, extract_zip, cleanup_directory
import os
import uuid
import logging
from collections import defaultdict

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.c', '.cpp', '.cc', '.hpp', '.h')

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_project(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    upload_path = f"storage/{session_id}"
    os.makedirs(upload_path, exist_ok=True)
    
    zip_path = os.path.join(upload_path, file.filename)
    
    try:
        # 1. Save and extract
        save_upload_file(file, zip_path)
        extract_dir = os.path.join(upload_path, "project")
        extract_zip(zip_path, extract_dir)
        
        # 2. Services
        parser = ParserService()
        chunker = ChunkingService()
        analyzer = AnalyzerService()
        
        # 3. Process files
        file_results_map = defaultdict(list)
        
        for root, dirs, files in os.walk(extract_dir):
            for filename in files:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, extract_dir)
                    
                    extracted_data = parser.parse_file(file_path, relative_path)
                    chunks = chunker.create_chunks(extracted_data)
                    
                    for chunk in chunks:
                        analysis = analyzer.analyze_code(chunk)
                        
                        chunk_result = ChunkAnalysisResult(
                            chunk_name=chunk.name,
                            chunk_type=chunk.type,
                            file=chunk.file,
                            start_line=chunk.start_line,
                            analysis=analysis
                        )
                        file_results_map[relative_path].append(chunk_result)
        
        # 4. Aggregate results by file
        final_results = []
        for file_path, chunk_results in file_results_map.items():
            summary = FileSummary()
            for res in chunk_results:
                analysis = res.analysis
                summary.total_issues += (len(analysis.bugs) + len(analysis.warnings) + 
                                       len(analysis.performance_issues) + len(analysis.security_issues) + 
                                       len(analysis.suggestions))
                summary.critical_issues += (len(analysis.bugs) + len(analysis.security_issues))
                summary.warnings += len(analysis.warnings)
                summary.performance += len(analysis.performance_issues)
                summary.suggestions += len(analysis.suggestions)
            
            final_results.append(FileAnalysisResult(
                file=file_path,
                summary=summary,
                details=chunk_results
            ))
            
        return AnalysisResponse(
            session_id=session_id,
            status="completed",
            results=final_results
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup could be moved to a background task
        # cleanup_directory(upload_path)
        pass
