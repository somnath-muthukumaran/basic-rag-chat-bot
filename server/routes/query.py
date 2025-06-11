from fastapi import APIRouter, HTTPException
from typing import List
from models.api_models import QueryRequest, StreamingResponse
from core.llm import generate_streaming_response, get_embedding, compress_documents_with_llm
from core.weaviate import WeaviateRetriever
from db.weaviate_client import weaviate_client
from prompts.templates import generate_rag_prompt
from utils.streaming import StreamingJSONResponse
from langchain_core.documents import Document
import json

router = APIRouter()

class Reference:
    def __init__(self, page, start_line, end_line, content, similarity_score):
        self.page = page
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
        self.similarity_score = similarity_score
        
    def dict(self):
        return {
            'page': self.page,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'content': self.content,
            'similarity_score': self.similarity_score
        }

def extract_context_and_references(documents: List[Document]):
    """Extract context and references from LangChain documents."""
    context_chunks = []
    references = []
    
    for doc in documents:
        content = doc.page_content
        metadata = doc.metadata
        
        if content:
            context_chunks.append(str(content))
            
            references.append(Reference(
                page=metadata.get("page", 0),
                start_line=metadata.get("start_line", 0),
                end_line=metadata.get("end_line", 0),
                content=str(content),
                similarity_score=metadata.get("similarity_score", 0)
            ))
    
    return context_chunks, references

@router.post("/query")
async def query_novel(query: QueryRequest):
    """Query the novel with streaming response using contextual compression"""
    try:
        # Initialize the Weaviate retriever
        retriever = WeaviateRetriever(weaviate_client, k=10)  # Get more documents initially
        
        # Get relevant documents
        documents = await retriever.get_relevant_documents(
            query.question, 
            document_id=getattr(query, 'document_id', None)
        )
        
        if not documents:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        
        # Apply contextual compression to get the most relevant parts
        compressed_documents = await compress_documents_with_llm(documents, query.question)
        
        if not compressed_documents:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        
        # Extract context and references from compressed documents
        context_chunks, references = extract_context_and_references(compressed_documents)
        
        # Generate answer using Ollama
        prompt = generate_rag_prompt(query.question, context_chunks)
        
        async def generate_combined_response():
            try:
                async for chunk in generate_streaming_response(prompt):
                    if chunk.get("done", False):
                        try:
                            references_list = []
                            for ref in references:
                                if hasattr(ref, 'dict'):
                                    references_list.append(ref.dict())
                                elif isinstance(ref, dict):
                                    references_list.append(ref)
                                else:
                                    references_list.append({
                                        'page': getattr(ref, 'page', 0),
                                        'start_line': getattr(ref, 'start_line', 0),
                                        'end_line': getattr(ref, 'end_line', 0),
                                        'content': getattr(ref, 'content', ''),
                                        'similarity_score': getattr(ref, 'similarity_score', 0)
                                    })
                            
                            yield {
                                "answer": chunk.get("answer", ""),
                                "references": references_list,
                                "done": True
                            }
                        except Exception as ref_error:
                            print(f"Error processing references: {ref_error}")
                            yield {
                                "answer": chunk.get("answer", ""),
                                "references": [],
                                "done": True
                            }
                    else:
                        yield {
                            "answer": chunk.get("answer", ""),
                            "references": [],
                            "done": False
                        }
            except Exception as gen_error:
                print(f"Error in generate_combined_response: {gen_error}")
                yield {
                    "answer": f"Sorry, I encountered an error while generating the response: {str(gen_error)}",
                    "references": [],
                    "done": True
                }
        
        return StreamingJSONResponse(generate_combined_response())
        
    except Exception as e:
        print(f"Error in query_novel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
