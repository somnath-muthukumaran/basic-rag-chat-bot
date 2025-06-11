export interface Document {
  id: string;
  filename: string;
  chunk_count: number;
  upload_date: string;
}

export interface ProcessingStatus {
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  total_chunks: number;
  processed_chunks: number;
  current_document: string | null;
  is_processing?: boolean;
  queue_size?: number;
  message?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'offline';
  ollama_status?: boolean;
  weaviate_status?: boolean;
  message?: string;
  timestamp?: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  references?: Reference[];
  isStreaming?: boolean;
}

export interface Reference {
  page: number;
  start_line: number;
  end_line: number;
  content: string;
  similarity_score: number;
}

export interface QueryResponse {
  answer: string;
  references: Reference[];
  done: boolean;
}