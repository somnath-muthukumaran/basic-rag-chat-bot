# NovelChatBot API Documentation

This document provides an overview of the available API endpoints for the NovelChatBot server.

## Base URL

All API endpoints are relative to the server's base URL.

## Authentication

Currently, there is no authentication implemented for these endpoints.

## Endpoints

### Health Checks

#### `GET /health`

*   **Description:** Checks the health of the server and its dependencies (Ollama and Weaviate).
*   **Response Body (`application/json`):**
    ```json
    {
        "status": "healthy" | "degraded",
        "ollama_status": true | false,
        "weaviate_status": true | false
    }
    ```
    *   `status`: "healthy" if all dependencies are responsive, "degraded" otherwise.
    *   `ollama_status`: `true` if Ollama is accessible, `false` otherwise.
    *   `weaviate_status`: `true` if Weaviate is accessible, `false` otherwise.

### Document Management

#### `POST /upload`

*   **Description:** Uploads and processes a document (PDF or TXT). The document is chunked, embeddings are generated, and then stored in the Weaviate vector database. This is an asynchronous operation.
*   **Request:** `multipart/form-data`
    *   `file`: The document file to upload.
    *   `chunk_size` (optional, query parameter): The desired size of text chunks (default: 512 characters).
    *   `chunk_overlap` (optional, query parameter): The overlap between consecutive chunks (default: 50 characters).
*   **Response Body (`application/json`):**
    ```json
    {
        "message": "Document upload started. Use the /status endpoint to monitor progress.",
        "document_id": "string (UUID)",
        "filename": "string"
    }
    ```
*   **Background Processing:** This endpoint initiates a background task for processing. Use the `/status` endpoint to track progress.

#### `GET /documents`

*   **Description:** Lists all documents currently stored in the vector database, grouped by their original upload.
*   **Response Body (`application/json`):**
    ```json
    [
        {
            "id": "string (document_id)",
            "filename": "string",
            "chunk_count": "integer",
            "upload_date": "string (Currently 'Unknown', consider adding timestamp to schema)"
        }
    ]
    ```

#### `DELETE /documents`

*   **Description:** Deletes all documents and their associated chunks from the vector database.
*   **Response Body (`application/json`):**
    ```json
    {
        "message": "Successfully deleted all documents"
    }
    ```

#### `GET /status`

*   **Description:** Retrieves the current status of any ongoing document processing.
*   **Response Body (`application/json`):**
    ```json
    {
        "status": "idle" | "processing" | "completed" | "error",
        "progress": "float (0-100)",
        "total_chunks": "integer",
        "processed_chunks": "integer",
        "current_document": "string (filename, or null)"
    }
    ```

### Querying

#### `POST /query`

*   **Description:** Submits a question to the chatbot. The system retrieves relevant context from the uploaded documents (optionally filtered by a specific `document_id`) and generates a response using an LLM. The response is streamed.
*   **Request Body (`application/json`):**
    ```json
    {
        "question": "string",
        "document_id": "string (optional, UUID to scope search to a specific document)"
    }
    ```
*   **Response Body (`application/json`, streamed, newline-delimited JSON objects):**
    Each chunk in the stream is a JSON object:
    ```json
    {
        "answer": "string (cumulative answer)",
        "references": [
            {
                "page": "integer",
                "start_line": "integer",
                "end_line": "integer",
                "content": "string (text content of the reference chunk)",
                "similarity_score": "float"
            }
        ],
        "done": "boolean (true for the last chunk)"
    }
    ```
    *   `answer`: The generated answer. For intermediate chunks, this is the answer built up so far.
    *   `references`: A list of source chunks from the document(s) that were used as context. This list is typically sent with the final chunk (`done: true`).
    *   `done`: `true` if this is the final chunk of the response, `false` otherwise.

## Error Handling

Errors are generally returned with appropriate HTTP status codes (e.g., 400, 404, 500) and a JSON body:

```json
{
    "detail": "Error message describing the issue"
}
```
