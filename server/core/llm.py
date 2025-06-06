import httpx
from fastapi import HTTPException
from typing import List, Dict, Any, AsyncGenerator
import json

async def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
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
                        "model": "nomic-embed-text:v1.5",
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

async def generate_streaming_response(prompt: str, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream response chunks from Ollama /api/chat endpoint and yield answer as it builds up."""
    if tools is None:
        tools = []
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen3:4b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "tools": tools
            },
            timeout=60.0
        )
        print(f"response {response}")
        print(f"response status: {response.status_code}")
        print(f"response headers: {response.headers}")
        if response.status_code != 200:
            print(f"Ollama error body: {await response.aread()}")
            raise HTTPException(status_code=500, detail="Error calling Ollama API")

        current_answer = ""
        try:
            async for chunk in response.aiter_lines():
                print(f"Received chunk: {chunk}")
                if chunk:
                    try:
                        data = json.loads(chunk)
                        content_piece = data.get("message", {}).get("content", "")
                        if content_piece:
                            current_answer += content_piece
                        yield {
                            "answer": current_answer,
                            "references": [],  # We'll add references at the end
                            "done": data.get("done", False)
                        }
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e} for chunk: {chunk}")
                        continue
        except Exception as stream_error:
            print(f"Error while streaming from Ollama: {stream_error}")
            raise HTTPException(status_code=500, detail=f"Streaming error: {stream_error}")
