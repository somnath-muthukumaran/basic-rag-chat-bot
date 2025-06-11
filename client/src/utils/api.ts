import { HealthStatus, ProcessingStatus, QueryResponse, Document as AppDocument } from "../types";

const API_BASE = 'http://localhost:8000'; // Update this to your actual API base URL

export class ApiService {
  static async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) {
        throw new Error('Failed to check health');
      }
      return response.json();
    } catch (error) {
      // Return a mock health status when backend is not available
      return {
        status: 'offline',
        message: 'Backend server is not available',
        timestamp: new Date().toISOString()
      };
    }
  }

  static async uploadDocument(file: File, chunkSize = 512, chunkOverlap = 50): Promise<{
    message: string;
    document_id: string;
    filename: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = new URL(`${API_BASE}/upload`);
    url.searchParams.set('chunk_size', chunkSize.toString());
    url.searchParams.set('chunk_overlap', chunkOverlap.toString());

    const response = await fetch(url.toString(), {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload document');
    }
    return response.json();
  }

  static async getDocuments(): Promise<AppDocument[]> {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      return response.json();
    } catch (error) {
      // Return empty array when backend is not available
      return [];
    }
  }

  static async deleteAllDocuments(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/documents`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete documents');
    }
    return response.json();
  }

  static async getProcessingStatus(): Promise<ProcessingStatus> {
    try {
      const response = await fetch(`${API_BASE}/status`);
      if (!response.ok) {
        throw new Error('Failed to get processing status');
      }
      return response.json();
    } catch (error) {
      // Return a mock processing status when backend is not available
      return {
        is_processing: false,
        current_document: null,
        queue_size: 0,
        message: 'Backend server is not available',
        status: 'error',
        progress: 0,
        total_chunks: 0,
        processed_chunks: 0
      };
    }
  }

  static async *queryStream(question: string, documentId?: string): AsyncGenerator<QueryResponse> {
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        document_id: documentId,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to query');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Failed to get response reader');
    }

    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              yield data;
            } catch (e) {
              console.error('Failed to parse JSON:', line);
            }
          }
        }
      }

      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          yield data;
        } catch (e) {
          console.error('Failed to parse final JSON:', buffer);
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}