from fastapi import APIRouter, HTTPException
from models.api_models import QueryRequest, StreamingResponse
from core.llm import generate_streaming_response, get_embedding
from db.weaviate_client import weaviate_client
from prompts.templates import generate_rag_prompt
from utils.streaming import StreamingJSONResponse
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

def extract_context_and_references(objects):
    context_chunks = []
    references = []
    for i, obj in enumerate(objects):
        try:
            if not hasattr(obj, 'properties'):
                continue

            props = obj.properties
            content = props.get("content", "")
            if content:
                context_chunks.append(str(content))

            distance = 0
            if hasattr(obj, 'metadata') and obj.metadata and hasattr(obj.metadata, 'distance'):
                distance = obj.metadata.distance or 0

            similarity_score = 1 - distance if distance is not None else 0

            references.append(Reference(
                page=props.get("page", 0),
                start_line=props.get("start_line", 0),
                end_line=props.get("end_line", 0),
                content=str(content) if content else "",
                similarity_score=round(similarity_score, 3)
            ))
        except Exception:
            continue
    return context_chunks, references

@router.post("/query")
async def query_novel(query: QueryRequest):
    """Query the novel with streaming response"""
    try:
        # Generate embedding for the question
        question_embedding = await get_embedding(query.question)
        # Use the reusable search_similar method
        objects = await weaviate_client.search_similar(question_embedding, document_id=getattr(query, 'document_id', None))
        if not objects:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        # Use the helper function for context and references
        context_chunks, references = extract_context_and_references(objects)
        valid_chunks = [str(chunk).strip() for chunk in context_chunks if chunk and str(chunk).strip()]
        if not valid_chunks:
            async def empty_response():
                yield {
                    "answer": "No relevant information found in the uploaded documents.",
                    "references": [],
                    "done": True
                }
            return StreamingJSONResponse(empty_response())
        # Generate answer using Ollama
        prompt = generate_rag_prompt(valid_chunks, query.question)
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
