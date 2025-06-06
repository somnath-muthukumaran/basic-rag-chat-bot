import re
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class TextChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        length_function: callable = len,
        separator: str = " "
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.separator = separator

    def _split_text(self, text: str) -> List[str]:
        """Split text into sentences."""
        # First split by common section markers
        sections = re.split(r'\n\s*#{1,6}\s+|\n\s*\d+\.\s+|\n\s*[-*]\s+', text)
        
        # Then split each section into sentences
        sentences = []
        for section in sections:
            if section.strip():
                sentences.extend(sent_tokenize(section))
        return sentences

    def _merge_sentences(self, sentences: List[str], current_chunk: List[str]) -> bool:
        """Check if sentences can be merged into the current chunk."""
        current_length = self.length_function(self.separator.join(current_chunk))
        return current_length < self.chunk_size

    def create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create semantically coherent chunks from text."""
        sentences = self._split_text(text)
        chunks = []
        current_chunk = []
        chunk_start_line = 1
        
        for i, sentence in enumerate(sentences):
            current_chunk.append(sentence)
            
            # Check if current chunk exceeds size limit
            if not self._merge_sentences(sentences[i+1:i+2], current_chunk) if i < len(sentences)-1 else True:
                # Create chunk with metadata
                chunk_text = self.separator.join(current_chunk)
                chunk_end_line = chunk_start_line + chunk_text.count('\n')
                
                chunks.append({
                    'text': chunk_text,
                    'page': (len(chunks) // 5) + 1,  # Assume ~5 chunks per page
                    'start_line': chunk_start_line,
                    'end_line': chunk_end_line
                })
                
                # Handle overlap for next chunk
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk[-1:]
                current_chunk = overlap_sentences
                chunk_start_line = max(1, chunk_end_line - len(''.join(overlap_sentences).split('\n')))

        # Add remaining sentences as last chunk if any
        if current_chunk:
            chunk_text = self.separator.join(current_chunk)
            chunk_end_line = chunk_start_line + chunk_text.count('\n')
            chunks.append({
                'text': chunk_text,
                'page': (len(chunks) // 5) + 1,
                'start_line': chunk_start_line,
                'end_line': chunk_end_line
            })

        return chunks

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
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """Process and chunk a document with smart text splitting."""
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Create chunker instance
    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separator=" "
    )
    
    # Generate chunks
    chunks = chunker.create_chunks(processed_text)
    
    return chunks
