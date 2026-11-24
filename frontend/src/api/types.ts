export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed';

export interface DocumentItem {
  id: string;
  user_id: string;
  filename: string;
  storage_path: string;
  page_count: number | null;
  status: DocumentStatus;
  error?: string | null;
  created_at: string;
}

export interface DocumentDetail extends DocumentItem {
  chunk_count: number;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
}

export interface Citation {
  ref: number;
  chunk_id: string;
  page_start: number;
  page_end: number;
  snippet: string;
  full_text?: string;
  similarity: number;
  char_start?: number;
  char_end?: number;
  context_before?: string;
  context_after?: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  found: boolean;
}

export interface HealthResponse {
  status: string;
  environment: string;
}

export interface UserProfile {
  id: string;
  email?: string;
}

