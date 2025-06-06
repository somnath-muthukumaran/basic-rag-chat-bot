from typing import List, Dict, Any, Optional
import weaviate
import weaviate.classes as wvc
from weaviate.exceptions import WeaviateConnectionError
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from models.api_models import DocumentInfo

# Load environment variables from .env file
load_dotenv()

class WeaviateClient:
    def __init__(self):
        try:
            # Get Weaviate cloud credentials from environment variables
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            if not weaviate_url or not weaviate_api_key:
                raise ValueError("WEAVIATE_URL and WEAVIATE_API_KEY environment variables must be set")

            # Connect to Weaviate Cloud
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=wvc.init.Auth.api_key(weaviate_api_key),
                skip_init_checks=True
            )
            print(f"self.client {self.client.is_ready()}")
            self._ensure_schema()
        except Exception as e:
            print(f"Failed to initialize Weaviate client: {e}")
            raise

    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate"""
        try:
            # Check if collection exists
            if not self.client.collections.exists("NovelChunk"):
                # Create collection if it doesn't exist
                self.client.collections.create(
                    name="NovelChunk",
                    description="A collection to store novel text chunks and their embeddings",
                    vectorizer_config=wvc.config.Configure.Vectorizer.none(),  # we provide our own vectors
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to ensure schema: {str(e)}")

    async def add_document(
        self,
        text: str,
        embedding: List[float],
        document_id: str,
        filename: str,
        page: int,
        start_line: int,
        end_line: int,
        chunk_index: int
    ):
        """Add a text chunk to the novel collection with its embedding"""
        try:
            document = {
                "content": text,
                "document_id": document_id,
                "filename": filename,
                "page": page,
                "start_line": start_line,
                "end_line": end_line,
                "chunk_index": chunk_index
            }
            collection = self.client.collections.get("NovelChunk")
            collection.data.insert(properties=document, vector=embedding)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

    async def add_documents_batch(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Batch insert multiple document chunks with their embeddings."""
        try:
            collection = self.client.collections.get("NovelChunk")
            # Prepare batch data: each item is a dict with 'properties' and 'vector'
            batch_data = [
                {"properties": doc, "vector": emb}
                for doc, emb in zip(documents, embeddings)
            ]
            # Use insert_many for batch insert (Weaviate v4)
            collection.data.insert_many(batch_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to batch add documents: {str(e)}")

    async def search_similar(self, query_embedding: List[float], document_id: Optional[str] = None, limit: int = 5) -> Any:
        """Search for similar documents using the query embedding, optionally filtered by document_id."""
        try:
            collection = self.client.collections.get("NovelChunk")
            if document_id:
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=limit,
                    return_metadata=["distance"],
                    where=collection.query.Filter.by_property("document_id").equal(document_id)
                )
            else:
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=limit,
                    return_metadata=["distance"]
                )
            return response.objects if hasattr(response, 'objects') else []
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")

    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the store"""
        try:
            collection = weaviate_client.client.collections.get("NovelChunk")
            response = collection.query.fetch_objects(limit=10)
    
            # Group by document_id
            document_map = {}
            for obj in response.objects:
                props = obj.properties
                doc_id = props.get("document_id", "")
                filename = props.get("filename", "")
                
                if doc_id not in document_map:
                    document_map[doc_id] = {
                        "id": doc_id,
                        "filename": filename,
                        "chunk_count": 0
                    }
                document_map[doc_id]["chunk_count"] += 1
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
            raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

    async def delete_all_documents(self):
        """Delete all documents from the store"""
        try:
            if self.client.collections.exists("NovelChunk"):
                collection = self.client.collections.get("NovelChunk")
                # Delete all objects in the collection
                collection.data.delete_many()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete documents: {str(e)}")

    async def delete_document(self, document_id: str):
        """Delete a specific document and all its chunks"""
        try:
            if self.client.collections.exists("NovelChunk"):
                collection = self.client.collections.get("NovelChunk")
                # Delete all chunks for this document
                collection.data.delete_many(
                    collection.query.Filter.by_property("document_id").equal(document_id)
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

    async def check_weaviate_connection(self) -> bool:
        """Check if Weaviate is accessible"""
        try:
            if not self.client:
                return False
            return self.client.is_ready()
        except:
            return False

    def close(self):
        """Close the Weaviate connection"""
        if self.client:
            self.client.close()

# Create a singleton instance
weaviate_client = WeaviateClient()