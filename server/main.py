from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any, AsyncGenerator
import httpx
import numpy as np
from pathlib import Path
import os
from dotenv import load_dotenv
import json
import asyncio
from fastapi.responses import JSONResponse
import io
from PyPDF2 import PdfReader
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure
import uuid
from streaming import StreamingJSONResponse

# Load environment variables from .env file
load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application"""
    # Startup: Initialize Weaviate schema
    if weaviate_client:
        setup_weaviate_schema()
    
    yield
    
    # Shutdown: Close Weaviate connection
    if weaviate_client:
        weaviate_client.close()

app = FastAPI(lifespan=lifespan)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Weaviate configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "https://your-cluster.weaviate.network")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "your-api-key")

# Debug: Print Weaviate configuration
# print("Attempting to connect to Weaviate with:")
# print(f"URL: {WEAVIATE_URL}")
# print(f"API Key: {WEAVIATE_API_KEY}")

# Initialize Weaviate client
try:
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
    )
except Exception as e:
    print(f"Failed to connect to Weaviate: {e}")
    weaviate_client = None

# Processing status storage
processing_status = {
    "total_chunks": 0,
    "processed_chunks": 0,
    "status": "idle",  # idle, processing, completed, error
    "current_document": None
}

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # Optional: query specific document

class Reference(BaseModel):
    page: int
    start_line: int
    end_line: int
    content: str
    similarity_score: float

class QueryResponse(BaseModel):
    answer: str
    references: List[Reference]
    
def generate_streamed_response(answer: str, references: List[Reference]) -> Dict[str, Any]:
    """Generate a streamed response for the query"""
    return {
        "answer": answer,
        "references": [ref.dict() for ref in references]
    }

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

def setup_weaviate_schema():
    """Setup Weaviate collection schema"""
    if not weaviate_client:
        return False
    
    try:
        # Check if collection exists
        if weaviate_client.collections.exists("NovelChunk"):
            return True
        
        # Create collection with schema
        weaviate_client.collections.create(
            name="NovelChunk",
            vectorizer_config=Configure.Vectorizer.none(),  # We'll provide our own vectors
            properties=[
                wvc.config.Property(
                    name="content",
                    data_type=wvc.config.DataType.TEXT,
                    description="Text content of the chunk"
                ),
                wvc.config.Property(
                    name="page",
                    data_type=wvc.config.DataType.INT,
                    description="Page number"
                ),
                wvc.config.Property(
                    name="start_line",
                    data_type=wvc.config.DataType.INT,
                    description="Starting line number"
                ),
                wvc.config.Property(
                    name="end_line",
                    data_type=wvc.config.DataType.INT,
                    description="Ending line number"
                ),
                wvc.config.Property(
                    name="document_id",
                    data_type=wvc.config.DataType.TEXT,
                    description="Document identifier"
                ),
                wvc.config.Property(
                    name="filename",
                    data_type=wvc.config.DataType.TEXT,
                    description="Original filename"
                ),
                wvc.config.Property(
                    name="chunk_index",
                    data_type=wvc.config.DataType.INT,
                    description="Index of chunk within document"
                )
            ]
        )
        return True
    except Exception as e:
        print(f"Error setting up Weaviate schema: {e}")
        return False

async def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except:
        return False

async def check_weaviate_connection() -> bool:
    """Check if Weaviate is accessible"""
    try:
        if not weaviate_client:
            return False
        return weaviate_client.is_ready()
    except:
        return False

async def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama API with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={
                        "model": "deepseek-r1",
                        "prompt": text
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()["embedding"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get embeddings after {max_retries} attempts: {str(e)}"
                )
            await asyncio.sleep(1)
    
    raise HTTPException(status_code=500, detail="Failed to get embeddings from Ollama")

def chunk_text(text: str, lines_per_page: int = 30, overlap: int = 5) -> List[dict]:
    """Chunk text with overlap for better context preservation"""
    lines = text.split('\n')
    chunks = []
    page = 1
    start_line = 1
    i = 0

    while i < len(lines):
        # Calculate end index with overlap
        end_idx = min(i + lines_per_page, len(lines))
        chunk_lines = lines[i:end_idx]
        
        # Add overlap from next chunk if available
        if end_idx < len(lines):
            chunk_lines.extend(lines[end_idx:end_idx + overlap])
        
        if chunk_lines:
            chunks.append({
                'text': '\n'.join(chunk_lines),
                'page': page,
                'start_line': start_line,
                'end_line': start_line + len(chunk_lines) - 1
            })
        
        i += lines_per_page
        page += 1
        start_line += lines_per_page

    return chunks

async def process_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    pdf_reader = PdfReader(io.BytesIO(file_content))
    text_content = []
    
    for page in pdf_reader.pages:
        text_content.append(page.extract_text())
    
    return "\n".join(text_content)

async def process_file_content(file: UploadFile) -> str:
    """Process uploaded file content based on file type"""
    content = await file.read()
    
    if file.filename.endswith('.pdf'):
        return await process_pdf(content)
    elif file.filename.endswith('.txt'):
        return content.decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only .txt and .pdf files are supported")

@app.get("/health")
async def health_check():
    ollama_connected = await check_ollama_connection()
    weaviate_connected = await check_weaviate_connection()
    return {
        "status": "ok" if (ollama_connected and weaviate_connected) else "error",
        "ollama_connected": ollama_connected,
        "weaviate_connected": weaviate_connected,
        "processing_status": processing_status
    }

@app.get("/status")
async def get_processing_status() -> ProcessingStatus:
    progress = (processing_status["processed_chunks"] / processing_status["total_chunks"] * 100) if processing_status["total_chunks"] > 0 else 0
    return ProcessingStatus(
        status=processing_status["status"],
        progress=progress,
        total_chunks=processing_status["total_chunks"],
        processed_chunks=processing_status["processed_chunks"],
        current_document=processing_status["current_document"]
    )

@app.get("/documents")
async def list_documents() -> List[DocumentInfo]:
    """List all uploaded documents"""
    if not weaviate_client:
        raise HTTPException(status_code=503, detail="Weaviate service is not available")
    
    try:
        collection = weaviate_client.collections.get("NovelChunk")
        
        # Query all chunks to get document information
        response = collection.query.fetch_objects(limit=10000)
        
        # Group documents manually
        document_map = {}
        for obj in response.objects:
            props = obj.properties
            doc_id = props["document_id"]
            filename = props["filename"]
            
            if doc_id not in document_map:
                document_map[doc_id] = {
                    "id": doc_id,
                    "filename": filename,
                    "chunk_count": 0
                }
            document_map[doc_id]["chunk_count"] += 1
        
        # Convert to list of DocumentInfo objects
        documents = []
        for doc_data in document_map.values():
            documents.append(DocumentInfo(
                id=doc_data["id"],
                filename=doc_data["filename"],
                chunk_count=doc_data["chunk_count"],
                upload_date="Unknown"  # You might want to add timestamp to schema
            ))
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

async def process_chunk_batch(batch, document_id, filename, start_idx):
    """Process a batch of chunks in parallel"""
    # Create tasks for getting embeddings
    embedding_tasks = []
    objects_batch = []
    
    for j, chunk in enumerate(batch):
        # Create embedding task
        task = get_embedding(chunk["text"])
        embedding_tasks.append(task)
        
        # Prepare object data
        objects_batch.append({
            "content": chunk["text"],
            "page": chunk["page"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "document_id": document_id,
            "filename": filename,
            "chunk_index": start_idx + j
        })
    
    # Wait for all embeddings in parallel
    embeddings = await asyncio.gather(*embedding_tasks)
    return embeddings, objects_batch

async def process_document(text: str, filename: str, document_id: str, lines_per_page: int = 30):
    """Background task for processing document chunks and generating embeddings"""
    try:
        # Chunk the text
        chunks = chunk_text(text, lines_per_page)
        processing_status["total_chunks"] = len(chunks)
        
        collection = weaviate_client.collections.get("NovelChunk")
        
        # Process chunks in batches for better performance
        batch_size = 5  # Reduced batch size for parallel processing
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Process batch in parallel
            embeddings_batch, objects_batch = await process_chunk_batch(
                batch, document_id, filename, i
            )
            
            # Insert batch into Weaviate
            with collection.batch.dynamic() as batch_writer:
                for obj, embedding in zip(objects_batch, embeddings_batch):
                    batch_writer.add_object(
                        properties=obj,
                        vector=embedding
                    )
            
            # Update progress after successful batch insertion
            processing_status["processed_chunks"] += len(batch)
        
        processing_status["status"] = "completed"
    except Exception as e:
        processing_status["status"] = "error"
        print(f"Error processing document: {str(e)}")

@app.post("/upload")
async def upload_novel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lines_per_page: int = 30
):
    if not await check_ollama_connection():
        raise HTTPException(status_code=503, detail="Ollama service is not available")
    
    if not await check_weaviate_connection():
        raise HTTPException(status_code=503, detail="Weaviate service is not available")

    try:
        # Read file content first to make sure it's valid
        text = await process_file_content(file)
        document_id = str(uuid.uuid4())
        
        # Reset processing status
        processing_status.update({
            "status": "processing",
            "total_chunks": 0,
            "processed_chunks": 0,
            "current_document": file.filename
        })
        
        # Schedule the background task
        background_tasks.add_task(
            process_document,
            text,
            file.filename,
            document_id,
            lines_per_page
        )
        
        return {
            "success": True,
            "message": "Document upload started. Use the /status endpoint to monitor progress.",
            "document_id": document_id,
            "filename": file.filename
        }
    
    except Exception as e:
        processing_status["status"] = "error"
        raise HTTPException(status_code=500, detail=str(e))

async def generate_streaming_response(prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream response chunks from Ollama"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-r1",
                "prompt": prompt,
                "stream": True
            },
            timeout=60.0
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error calling Ollama API")

        # Parse response as a stream of JSON lines
        buffer = ""
        current_answer = ""
        async for chunk in response.aiter_lines():
            if chunk:
                try:
                    data = json.loads(chunk)
                    if "response" in data:
                        current_answer += data["response"]
                        yield {
                            "answer": current_answer,
                            "references": [],  # We'll add references at the end
                            "done": data.get("done", False)
                        }
                except json.JSONDecodeError:
                    continue

@app.post("/query")
async def query_novel(query: QueryRequest):
    """Query the novel with streaming response"""
    if not await check_weaviate_connection():
        raise HTTPException(status_code=503, detail="Weaviate service is not available")
    
    if not await check_ollama_connection():
        raise HTTPException(status_code=503, detail="Ollama service is not available")
    
    try:
        # Generate embedding for the question
        question_embedding = await get_embedding(query.question)
        
        collection = weaviate_client.collections.get("NovelChunk")
        
        # Build and execute the query
        if query.document_id:
            response = collection.query.near_vector(
                near_vector=question_embedding,
                limit=5,
                return_metadata=["distance"],
                where=collection.query.Filter.by_property("document_id").equal(query.document_id)
            )
        else:
            response = collection.query.near_vector(
                near_vector=question_embedding,
                limit=5,
                return_metadata=["distance"]
            )
        
        print("Weaviate response JSON:")
        print(json.dumps(response.__dict__, indent=2, default=str))
        
        # Access objects from the response
        objects = response.objects if hasattr(response, 'objects') else []
        
        if not objects:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        
        # Prepare context and references
        context_chunks = []
        references = []
        
        print(f"Number of objects: {len(objects)}")
        print(f"Objects type: {type(objects)}")
        
        for i, obj in enumerate(objects):
            try:
                print(f"Processing object {i}: {type(obj)}")
                
                # Access properties directly from the GenerativeObject
                if hasattr(obj, 'properties'):
                    props = obj.properties
                    print(f"Properties found: {type(props)}")
                else:
                    print(f"No properties attribute found. Available attributes: {dir(obj)}")
                    continue
                
                content = props.get("content", "") if props else ""
                print(f"Content length: {len(content) if content else 0}")
                
                if content and isinstance(content, str):
                    context_chunks.append(content)
                elif content:
                    context_chunks.append(str(content))
                
                # Get distance from metadata
                distance = 0
                if hasattr(obj, 'metadata') and obj.metadata and hasattr(obj.metadata, 'distance'):
                    distance = obj.metadata.distance or 0
                
                similarity_score = 1 - distance if distance else 0
                
                references.append(Reference(
                    page=props.get("page", 0) if props else 0,
                    start_line=props.get("start_line", 0) if props else 0,
                    end_line=props.get("end_line", 0) if props else 0,
                    content=str(content) if content else "",
                    similarity_score=round(similarity_score, 3)
                ))
                
            except Exception as e:
                print(f"Error processing object {i}: {e}")
                print(f"Object type: {type(obj)}")
                print(f"Object dir: {dir(obj)}")
                continue
        
        print(f"Context chunks collected: {len(context_chunks)}")
        print(f"Context chunks type: {type(context_chunks)}")
        
        if not context_chunks or not isinstance(context_chunks, list):
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        
        # Ensure all chunks are strings and filter out empty ones
        valid_chunks = []
        for chunk in context_chunks:
            if chunk:
                chunk_str = str(chunk)
                if chunk_str.strip():
                    valid_chunks.append(chunk_str)
        
        print(f"Valid chunks: {len(valid_chunks)}")
        print(f"Valid chunks type: {type(valid_chunks)}")
        if valid_chunks:
            print(f"First chunk type: {type(valid_chunks[0])}")
        
        if not valid_chunks:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        
        # Join context chunks
        try:
            context = "\n\n".join(valid_chunks)
            print(f"Context created successfully, length: {len(context)}")
        except Exception as join_error:
            print(f"Join error: {join_error}")
            print(f"Valid chunks content preview: {[chunk[:50] + '...' if len(chunk) > 50 else chunk for chunk in valid_chunks[:2]]}")
            raise
        
        # Generate answer using Ollama
        prompt = f"""You are an intelligent book analysis assistant with access to both the provided book content and your general knowledge. Your primary role is to help users navigate and understand book content, but you can supplement with general knowledge when appropriate.

CONTEXT FROM BOOK:
{context}

USER QUESTION: {query.question}

INSTRUCTIONS:
1. **Primary Source Analysis**: Always prioritize information from the provided book content first.

2. **Reference Citation**: For every piece of information from the book, include specific references:
   - Page numbers where the information appears
   - Line ranges when available
   - Direct quotes with quotation marks when relevant

3. **Response Strategy**:
   - **If information IS in the book**: Provide comprehensive analysis with detailed citations
   - **If information is NOT in the book**: Clearly state "I couldn't find information about [topic] in the provided book content, but here's what I know about it from my general knowledge:" then provide relevant general information
   - **If partially in the book**: Provide book-based information first with citations, then add "Additionally, from my general knowledge:" for supplementary context

4. **Response Types Based on Question**:
   - If asked "Where can I find information about X?": Provide specific page numbers and content, or clearly state it's not in the provided text
   - If asked for similar references or patterns: Identify ALL relevant instances from the book with locations
   - If asked about character details, plot points, or themes: Provide book-based analysis first, supplement with general knowledge if needed
   - If asked for comparisons: Draw connections within the book text first, then add external context if helpful

5. **Clear Source Attribution**:
   - **From the book**: "(Page X, Lines Y-Z)" 
   - **From general knowledge**: "Based on my general knowledge:" or "From what I know about [topic]:"
   - **Mixed sources**: Clearly separate book citations from general knowledge

6. **Format Your Response**:
   ```
   **From the Book:**
   [Book-based answer with citations]
   
   **Additional Context (General Knowledge):**
   [Supplementary information if needed]
   
   **References from Book:**
   - Page X (Lines Y-Z): [description]
   ```

7. **Handling Different Scenarios**:
   - **Complete answer from book**: Focus entirely on book content with rich citations
   - **No book information**: "I couldn't find information about [topic] in the provided book content, but here's what I know: [general knowledge]"
   - **Partial book information**: Combine both sources with clear attribution

8. **Cross-References**: Mention related topics from the book and suggest where users might find additional relevant information.

EXAMPLE RESPONSES:

**Scenario 1 - Information in book:**
"Based on the book content, Harry's scar is described on Page 15 (Lines 280-285): 'The only thing Harry liked about his own appearance was a very thin scar on his forehead that was shaped like a bolt of lightning.' The origin is explained when Aunt Petunia tells him it came from 'the car crash when your parents died.'

**References from Book:**
- Page 15 (Lines 280-285): Physical description of the lightning bolt scar
- Page 15 (Lines 290-295): Aunt Petunia's explanation of its origin"

**Scenario 2 - Information not in book:**
"I couldn't find specific information about Quidditch rules in the provided book content, but here's what I know about it from my general knowledge: Quidditch is a wizarding sport played on broomsticks with four balls - one Quaffle, two Bludgers, and one Golden Snitch. Teams score by getting the Quaffle through hoops, and the game ends when someone catches the Snitch."

**Scenario 3 - Mixed information:**
"**From the Book:**
Dudley is described on Page 16 as having 'a large pink face, not much neck, small, watery blue eyes, and thick blond hair' (Lines 295-297).

**Additional Context (General Knowledge):**
Dudley Dursley is Harry's cousin in the Harry Potter series, known for being spoiled and bullying Harry throughout their childhood.

**References from Book:**
- Page 16 (Lines 295-297): Physical description of Dudley"

Now analyze the context and provide your detailed response following these guidelines."""


        async def generate_combined_response():
            """Generate response with both streaming answer and references"""
            try:
                async for chunk in generate_streaming_response(prompt):
                    if chunk.get("done", False):
                        # Add references to the final response
                        try:
                            # Convert references to dict format
                            references_list = []
                            for ref in references:
                                if hasattr(ref, 'dict'):
                                    references_list.append(ref.dict())
                                elif isinstance(ref, dict):
                                    references_list.append(ref)
                                else:
                                    # Convert to dict manually
                                    references_list.append({
                                        'page': getattr(ref, 'page', 0),
                                        'start_line': getattr(ref, 'start_line', 0),
                                        'end_line': getattr(ref, 'end_line', 0),
                                        'content': getattr(ref, 'content', ''),
                                        'similarity_score': getattr(ref, 'similarity_score', 0)
                                    })
                            
                            chunk["references"] = references_list
                            print(f"Added {len(references_list)} references to response")
                        except Exception as ref_error:
                            print(f"Error processing references: {ref_error}")
                            chunk["references"] = []
                    yield chunk
            except Exception as gen_error:
                print(f"Error in generate_combined_response: {gen_error}")
                yield {
                    "answer": f"Error generating response: {str(gen_error)}",
                    "references": [],
                    "done": True
                }

        return StreamingJSONResponse(generate_combined_response())
    
    except Exception as e:
        print(f"Exception in query_novel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document and all its chunks"""
    if not await check_weaviate_connection():
        raise HTTPException(status_code=503, detail="Weaviate service is not available")
    
    try:
        collection = weaviate_client.collections.get("NovelChunk")
        
        # Delete all chunks for this document
        collection.data.delete_many(
            collection.query.Filter.by_property("document_id").equal(document_id)
        )
        
        return {"success": True, "message": f"Document {document_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)