import httpx
from fastapi import HTTPException
from typing import List, Dict, Any, AsyncGenerator
import json
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:v1.5")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:4b")


async def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
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
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={
                        "model": OLLAMA_EMBED_MODEL,
                        "prompt": text
                    },
                    timeout=30.0
                )
                response.raise_for_status() # Raise an exception for bad status codes
                return response.json()["embedding"]
        except httpx.HTTPStatusError as e:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Failed to get embeddings after {max_retries} attempts. Ollama error: {e.response.text}"
                )
            await asyncio.sleep(1)
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
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "tools": tools
                },
                timeout=60.0
            )
            if response.status_code != 200:
                error_body = await response.aread()
                print(f"Ollama error body: {error_body.decode()}")
                raise HTTPException(status_code=response.status_code, detail=f"Error calling Ollama API: {error_body.decode()}")

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
        except httpx.RequestError as e:
            print(f"Request error calling Ollama: {e}")
            raise HTTPException(status_code=503, detail=f"Could not connect to Ollama: {e}")
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            print(f"Ollama API returned an error: {e.response.status_code} - {error_body}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Ollama API error: {error_body}")
        except Exception as e:
            print(f"Unexpected error in generate_streaming_response: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
