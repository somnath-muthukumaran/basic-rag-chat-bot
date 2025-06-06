from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import query, documents, health
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Novel RAG Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, tags=["Query"])
app.include_router(documents.router, tags=["Documents"])
app.include_router(health.router, tags=["Health"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Chatbot API is running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Server will be started using run.py