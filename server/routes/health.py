from fastapi import APIRouter
from models.api_models import HealthResponse
from core.llm import check_ollama_connection
from db.weaviate_client import weaviate_client

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the server and its dependencies"""
    ollama_status = await check_ollama_connection()

    try:
        await weaviate_client.check_weaviate_connection()
        weaviate_status = True
    except:
        weaviate_status = False

        print(f"ollama_status: {ollama_status} weaviate: {weaviate_status}")

    return HealthResponse(
        status="healthy" if (ollama_status and weaviate_status) else "degraded",
        ollama_status=ollama_status,
        weaviate_status=weaviate_status
    )
