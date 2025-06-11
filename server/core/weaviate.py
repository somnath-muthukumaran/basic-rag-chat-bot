from typing import List, Optional
from langchain_core.documents import Document

class WeaviateRetriever:
    """Custom retriever that integrates with our existing Weaviate client."""
    
    def __init__(self, weaviate_client, k: int = 5):
        self.weaviate_client = weaviate_client
        self.k = k
    
    async def get_relevant_documents(self, query: str, document_id: Optional[str] = None) -> List[Document]:
        """Retrieve relevant documents from Weaviate using the existing client."""
        from core.llm import get_embedding
        
        # Get query embedding
        query_embedding = await get_embedding(query)
        
        # Use the existing search_similar method from db/weaviate_client
        objects = await self.weaviate_client.search_similar(
            query_embedding, 
            document_id=document_id, 
            limit=self.k
        )
        
        # Convert Weaviate objects to LangChain Documents
        documents = []
        for obj in objects:
            if hasattr(obj, 'properties'):
                props = obj.properties
                content = props.get("content", "")
                
                # Calculate similarity score from distance
                distance = 0
                if hasattr(obj, 'metadata') and obj.metadata and hasattr(obj.metadata, 'distance'):
                    distance = obj.metadata.distance or 0
                similarity_score = 1 - distance if distance is not None else 0
                
                # Create LangChain Document with metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        'page': props.get("page", 0),
                        'start_line': props.get("start_line", 0),
                        'end_line': props.get("end_line", 0),
                        'document_id': props.get("document_id", ""),
                        'filename': props.get("filename", ""),
                        'chunk_index': props.get("chunk_index", 0),
                        'similarity_score': round(similarity_score, 3)
                    }
                )
                documents.append(doc)
        
        return documents
