from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List
from models.api_models import DocumentChunk, ProcessingStatus, DocumentInfo
from core.llm import get_embedding
from db.weaviate_client import weaviate_client
from utils.text_processing import chunk_document
import asyncio
import uuid
import PyPDF2

router = APIRouter()

# Processing status storage
processing_status = {
    "total_chunks": 0,
    "processed_chunks": 0,
    "status": "idle",  # idle, processing, completed, error
    "current_document": None
}

async def process_chunks(chunks: List[dict], document_id: str, filename: str):
    """Process chunks in parallel batches using batch insert to Weaviate."""
    try:
        processing_status["total_chunks"] = len(chunks)
        processing_status["processed_chunks"] = 0
        batch_size = 5  # Process 5 chunks at a time to avoid overloading

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            tasks = []
            valid_chunks = []
            for chunk in batch:
                if len(chunk['text']) >= 50:  # Skip very small chunks
                    tasks.append(get_embedding(chunk['text']))
                    valid_chunks.append(chunk)
            if not valid_chunks:
                continue
            embeddings = await asyncio.gather(*tasks)
            # Prepare document dicts for batch insert
            documents = []
            for chunk in valid_chunks:
                documents.append({
                    "content": chunk['text'],
                    "document_id": document_id,
                    "filename": filename,
                    "page": chunk.get('page', 0),
                    "start_line": chunk.get('start_line', 0),
                    "end_line": chunk.get('end_line', 0),
                    "chunk_index": chunk.get('chunk_index', 0)
                })
            await weaviate_client.add_documents_batch(documents, embeddings)
            processing_status["processed_chunks"] += len(valid_chunks)
        processing_status["status"] = "completed"
    except Exception as e:
        processing_status["status"] = "error"
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = 512,
    chunk_overlap: int = 50
):
    """Upload and process a text document with smart chunking"""
    try:
        content = await file.read()
        # Detect file type by extension
        if file.filename.lower().endswith('.pdf'):
            # Use PyPDF2 to extract text from PDF
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        else:
            # Assume plain text
            text = content.decode("utf-8")
        document_id = str(uuid.uuid4())
        
        # Reset processing status
        processing_status.update({
            "status": "processing",
            "total_chunks": 0,
            "processed_chunks": 0,
            "current_document": file.filename
        })
        
        # Create chunks using the new chunking strategy
        chunks = chunk_document(text, chunk_size, chunk_overlap)
        
        # Process chunks in the background
        background_tasks.add_task(
            process_chunks,
            chunks,
            document_id,
            file.filename
        )
        
        return {
            "message": f"Document upload started. Use the /status endpoint to monitor progress.",
            "document_id": document_id,
            "filename": file.filename
        }
        
    except Exception as e:
        processing_status["status"] = "error"
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all document chunks in the vector store"""
    try:
        documents = await weaviate_client.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents")
async def delete_documents():
    """Delete all documents from the vector store"""
    try:
        await weaviate_client.delete_all_documents()
        return {"message": "Successfully deleted all documents"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=ProcessingStatus)
async def get_processing_status() -> ProcessingStatus:
    progress = (processing_status["processed_chunks"] / processing_status["total_chunks"] * 100) if processing_status["total_chunks"] > 0 else 0
    return ProcessingStatus(
        status=processing_status["status"],
        progress=progress,
        total_chunks=processing_status["total_chunks"],
        processed_chunks=processing_status["processed_chunks"],
        current_document=processing_status["current_document"]
    )
