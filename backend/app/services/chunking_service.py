from typing import List
import logging
from backend.app.models.schemas import CodeChunk

logger = logging.getLogger(__name__)

class ChunkingService:
    def create_chunks(self, extracted_data: dict) -> List[CodeChunk]:
        chunks = []
        file_path = extracted_data.get("file", "unknown")
        
        try:
            # Add functions as chunks
            for func in extracted_data.get("functions", []):
                chunks.append(CodeChunk(
                    file=file_path,
                    name=func.get("name", "anonymous"),
                    type="function" if "function" in func.get("name", "").lower() or "(" in func.get("code", "") else "method",
                    code=func["code"],
                    start_line=func["start_line"],
                    end_line=func["end_line"]
                ))
                
            # Add classes as chunks
            for cls in extracted_data.get("classes", []):
                chunks.append(CodeChunk(
                    file=file_path,
                    name=cls.get("name", "anonymous"),
                    type="class",
                    code=cls["code"],
                    start_line=cls["start_line"],
                    end_line=cls["end_line"]
                ))
        except KeyError as e:
            logger.error(f"Missing expected key in extracted data for file {file_path}: {e}")
            
        return chunks
