# NovelChatBot: Complete Architecture & Flow Documentation

## System Overview

NovelChatBot is a comprehensive RAG (Retrieval-Augmented Generation) application that allows users to upload novels (PDF/TXT) and chat with them using natural language queries. The system combines modern AI technologies including vector embeddings, semantic search, and LLM-powered responses.

## Architecture Components

### Frontend (Vue.js Client)
- **Framework**: Vue 3 with TypeScript
- **Styling**: Tailwind CSS
- **Location**: `/bot client/`
- **Key Components**:
  - `NovelUpload.vue` - File upload interface
  - `ChatInterface.vue` - Chat interface
  - `ProcessingStatus.vue` - Real-time processing status
  - `useNovelChatbot.ts` - Main composable for API interactions

### Backend (FastAPI Server)
- **Framework**: FastAPI with Python
- **Location**: `/server/`
- **Key Modules**:
  - `routes/` - API endpoints
  - `core/` - Core business logic (LLM, Weaviate)
  - `db/` - Database client (Weaviate)
  - `utils/` - Utilities (text processing, streaming)
  - `models/` - Data models
  - `prompts/` - LLM prompt templates

### External Services
- **Ollama** - Local LLM for embeddings and chat generation
- **Weaviate Cloud** - Vector database for semantic search
- **NLTK** - Natural language processing toolkit

## Technology Stack

### Core Dependencies
```
fastapi                 # Web framework
uvicorn                 # ASGI server
langchain              # LLM framework
langchain-text-splitters # Advanced text chunking
weaviate-client        # Vector database client
httpx                  # HTTP client for Ollama
pypdf                  # PDF processing
python-dotenv          # Environment configuration
nltk                   # Text processing
```

### Unused Dependencies
- `sentence-transformers` - Listed but not used (can be removed)

## Complete System Flow

### 1. Document Upload Flow

#### Frontend (Vue.js)
1. **User Interface**: User selects PDF/TXT file via `NovelUpload.vue`
2. **File Validation**: Client validates file type and size
3. **Upload Initiation**: FormData sent to `/upload` endpoint
4. **Status Monitoring**: Starts polling `/status` endpoint every 2 seconds

#### Backend Processing
1. **File Reception**: FastAPI receives multipart/form-data
2. **File Processing**:
   - **PDF**: Uses `pypdf` to extract text content
   - **TXT**: Direct text reading
3. **Text Preprocessing**: 
   - Normalize whitespace and line endings
   - Fix formatting issues (paragraph breaks)
4. **Advanced Chunking** (LangChain):
   - Uses `RecursiveCharacterTextSplitter`
   - Chunk size: 1000 characters (2x larger than before)
   - Overlap: 200 characters (4x larger than before)
   - Smart separators: paragraphs → sentences → clauses → words
5. **Batch Processing**:
   - Processes 5 chunks at a time
   - Generates embeddings via Ollama (`nomic-embed-text:v1.5`)
   - Stores in Weaviate using improved batch insertion
6. **Status Updates**: Real-time progress tracking

### 2. Query Processing Flow

#### Query Reception
1. **User Input**: User types question in chat interface
2. **Request Formation**: Client sends POST to `/query` endpoint
3. **Query Embedding**: Generate embedding for user question

#### Retrieval & Compression
1. **Vector Search**: 
   - Search Weaviate for similar chunks (k=10 initially)
   - Calculate similarity scores
2. **Document Retrieval**: Convert Weaviate objects to LangChain Documents
3. **Contextual Compression**:
   - Apply `OllamaCompressor` for relevance filtering
   - Extract most relevant sentences (>10% keyword overlap)
   - Truncate long documents while preserving key information

#### Response Generation
1. **Prompt Assembly**: Use RAG template with compressed context
2. **LLM Generation**: Stream response from Ollama (`qwen3:4b`)
3. **Real-time Streaming**: Send incremental responses to client
4. **Reference Assembly**: Attach source references on completion

## Detailed Component Architecture

### Frontend Architecture (`/bot client/`)

```
src/
├── App.vue                 # Main application component
├── components/
│   ├── NovelUpload.vue     # File upload with drag-drop
│   ├── ChatInterface.vue   # Chat UI with message history
│   ├── ChatMessage.vue     # Individual message component
│   └── ProcessingStatus.vue # Real-time processing indicator
└── composables/
    └── useNovelChatbot.ts  # Main business logic & API client
```

**Key Features**:
- Real-time file upload progress
- Streaming chat responses with proper JSON parsing
- Automatic status polling for background processing
- Reference display with source attribution
- Responsive design with Tailwind CSS

### Backend Architecture (`/server/`)

```
server/
├── main.py                 # FastAPI application entry
├── routes/
│   ├── documents.py        # Upload, list, delete documents
│   ├── query.py           # Chat queries with streaming
│   └── health.py          # System health checks
├── core/
│   ├── llm.py             # Ollama integration & compression
│   └── weaviate.py        # Weaviate retriever wrapper
├── db/
│   └── weaviate_client.py # Vector database client
├── utils/
│   ├── text_processing.py # LangChain chunking
│   └── streaming.py       # Response streaming utilities
├── models/
│   └── api_models.py      # Pydantic data models
└── prompts/
    └── templates.py       # LLM prompt templates
```

## Advanced Features Implementation

### 1. LangChain Text Chunking
```python
# Intelligent text splitting with multiple separators
separators = [
    "\n\n",    # Paragraph breaks (highest priority)
    "\n",      # Line breaks
    ". ",      # Sentence endings
    "? ",      # Question endings
    "! ",      # Exclamation endings
    "; ",      # Semicolon breaks
    ", ",      # Comma breaks
    " ",       # Word breaks
    ""         # Character-level fallback
]

# Larger chunks with better overlap
RecursiveCharacterTextSplitter(
    chunk_size=1000,     # 2x larger than before
    chunk_overlap=200,   # 4x more overlap
    separators=separators
)
```

### 2. Contextual Compression
```python
# Query-aware document compression
def compress_documents(documents, query):
    query_words = set(query.lower().split())
    compressed_docs = []
    
    for doc in documents:
        # Calculate relevance score
        doc_words = set(doc.page_content.lower().split())
        relevance_score = len(query_words.intersection(doc_words)) / len(query_words)
        
        # Keep documents with >10% keyword overlap
        if relevance_score > 0.1:
            # Extract most relevant sentences
            # Truncate while preserving important parts
            compressed_docs.append(processed_doc)
    
    return compressed_docs
```

### 3. Streaming Response Handling
```typescript
// Client-side streaming with proper buffer management
const reader = response.body.getReader();
let buffer = "";

while (!done) {
    const { value, done: streamDone } = await reader.read();
    buffer += decoder.decode(value, { stream: true });
    
    let lines = buffer.split("\n");
    buffer = lines.pop() || ""; // Keep incomplete line
    
    for (const line of lines) {
        const data = JSON.parse(line);
        // Update UI with incremental response
        updateMessage(data.answer);
        if (data.done) setReferences(data.references);
    }
}
```

### 4. Batch Vector Storage
```python
# Improved Weaviate batch insertion
with collection.batch.dynamic() as batch:
    for doc_properties, vector_embedding in zip(documents, embeddings):
        batch.add_object(
            properties=doc_properties,  # Clean properties only
            vector=vector_embedding
        )
# Automatic execution on context exit
```

## Environment Configuration

### Required Environment Variables
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text:v1.5
OLLAMA_CHAT_MODEL=qwen3:4b

# Weaviate Configuration  
WEAVIATE_URL=your_weaviate_cloud_url
WEAVIATE_API_KEY=your_weaviate_api_key
```

### Services Setup
1. **Ollama**: Local LLM service running on port 11434
2. **Weaviate Cloud**: Managed vector database service
3. **NLTK Data**: Punkt tokenizer for sentence segmentation

## Performance Optimizations

### 1. Chunking Improvements
- **Larger Chunks**: 1000 chars vs 512 (better context)
- **More Overlap**: 200 chars vs 50 (better continuity)
- **Smart Separators**: Respect natural text boundaries

### 2. Batch Processing
- Process 5 chunks simultaneously
- Skip very small chunks (<50 chars)
- Parallel embedding generation with `asyncio.gather()`

### 3. Contextual Compression
- Pre-filter documents by relevance score
- Extract only relevant sentences
- Limit context size while preserving quality

### 4. Streaming Responses
- Real-time response delivery
- Proper JSON chunking and parsing
- Background reference processing

## API Endpoints Summary

| Endpoint | Method | Purpose | Key Features |
|----------|--------|---------|--------------|
| `/upload` | POST | Document upload | Background processing, status tracking |
| `/query` | POST | Chat queries | Streaming responses, contextual compression |
| `/status` | GET | Processing status | Real-time progress monitoring |
| `/documents` | GET | List documents | Document management |
| `/documents` | DELETE | Clear all docs | Bulk deletion |
| `/health` | GET | System health | Service dependency checks |

## Error Handling & Resilience

### 1. Upload Resilience
- File validation on client and server
- Graceful handling of PDF extraction errors
- Background processing with status tracking

### 2. Query Resilience  
- Embedding generation retry logic (3 attempts)
- Graceful fallback when no relevant documents found
- Stream error handling with proper cleanup

### 3. Service Dependencies
- Health checks for Ollama and Weaviate
- Detailed error messages for debugging
- Timeout handling for long operations

## Future Enhancement Opportunities

### 1. Advanced Compression
- Implement actual LLM-based document compression
- Use Ollama to extract only relevant excerpts
- Query-specific context optimization

### 2. Multi-Modal Support
- Image extraction from PDFs
- Table and structure preservation
- Metadata extraction and indexing

### 3. Scalability Improvements
- Redis for status tracking
- Celery for background processing
- Database connection pooling

### 4. User Experience
- Document management interface
- Chat history persistence
- Advanced search and filtering

## Dependency Cleanup

### Unused Dependencies
- `sentence-transformers`: Listed in requirements but not used
- Recommendation: Remove from `requirements.txt`

### Core Dependencies Used
- `langchain`: Text splitting and document processing
- `langchain-text-splitters`: Advanced chunking algorithms
- `langchain-core`: Document abstraction layer
- `weaviate-client`: Vector database operations
- `fastapi`: Web framework and API routing
- `httpx`: HTTP client for Ollama integration
- `pypdf`: PDF text extraction
- `nltk`: Natural language processing

This architecture provides a robust, scalable foundation for document-based conversational AI with advanced RAG capabilities.
