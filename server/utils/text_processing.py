import re
from typing import List, Dict, Any, Optional
import nltk
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class LangChainChunker:
    def __init__(
        self,
        chunk_size: int = 1000,  # Larger chunks for better context
        chunk_overlap: int = 200,  # More overlap for continuity
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Default separators optimized for novels/documents
        if separators is None:
            separators = [
                "\n\n",      # Paragraph breaks
                "\n",        # Line breaks
                ". ",        # Sentence endings
                "? ",        # Question endings
                "! ",        # Exclamation endings
                "; ",        # Semicolon breaks
                ", ",        # Comma breaks
                " ",         # Word breaks
                ""           # Character-level fallback
            ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )

    def create_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create chunks using LangChain's RecursiveCharacterTextSplitter."""
        if metadata is None:
            metadata = {}
        
        # Create a LangChain Document
        doc = Document(page_content=text, metadata=metadata)
        
        # Split the document
        chunks = self.text_splitter.split_documents([doc])
        
        # Convert to our expected format
        result_chunks = []
        for i, chunk in enumerate(chunks):
            # Calculate approximate page and line numbers
            page = (i // 5) + 1  # Assume ~5 chunks per page
            start_line = i * 10 + 1  # Approximate line calculation
            end_line = start_line + chunk.page_content.count('\n') + 10
            
            result_chunks.append({
                'text': chunk.page_content,
                'page': page,
                'start_line': start_line,
                'end_line': end_line,
                'chunk_index': i,
                'metadata': chunk.metadata
            })
        
        return result_chunks

def preprocess_text(text: str) -> str:
    """Clean and normalize text before chunking."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Fix common formatting issues
    text = re.sub(r'([.!?])\s*\n\s*', r'\1\n\n', text)  # Add proper paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)  # Normalize multiple line breaks
    
    return text.strip()

def chunk_document(
    text: str,
    chunk_size: int = 1000,  # Increased default size
    chunk_overlap: int = 200  # Increased overlap
) -> List[Dict[str, Any]]:
    """Process and chunk a document using LangChain's advanced text splitting."""
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Create chunker instance
    chunker = LangChainChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Generate chunks
    chunks = chunker.create_chunks(processed_text)
    
    return chunks
