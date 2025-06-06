from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # Optional: query specific document
    
class DocumentChunk(BaseModel):
    text: str
    source: str
    
class StreamingResponse(BaseModel):
    answer: str
    references: List[str]
    done: bool
    
class HealthResponse(BaseModel):
    status: str
    ollama_status: bool
    weaviate_status: bool

class ProcessingStatus(BaseModel):
    status: str
    progress: float
    total_chunks: int
    processed_chunks: int
    current_document: Optional[str]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int
    upload_date: str
