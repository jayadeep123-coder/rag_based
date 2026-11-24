import axios from 'axios';
import { supabase } from '../lib/supabase';
import type {
  DocumentItem,
  DocumentDetail,
  DocumentListResponse,
  ChatResponse,
  HealthResponse,
  UserProfile,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Interceptor to inject Supabase JWT access token on every outgoing request
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Interceptor to handle 401 response by signing out and redirecting to /login
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const apiClient = {
  // Health
  checkHealth: async (): Promise<HealthResponse> => {
    const res = await api.get<HealthResponse>('/health');
    return res.data;
  },

  // Auth / Current User profile verification
  getCurrentUser: async (): Promise<UserProfile> => {
    const res = await api.get<UserProfile>('/api/auth/me');
    return res.data;
  },

  // Documents
  listDocuments: async (): Promise<DocumentItem[]> => {
    const res = await api.get<DocumentListResponse>('/api/documents');
    return res.data.documents;
  },

  getDocument: async (documentId: string): Promise<DocumentDetail> => {
    const res = await api.get<DocumentDetail>(`/api/documents/${documentId}`);
    return res.data;
  },

  uploadDocument: async (file: File): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await api.post<DocumentItem>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  deleteDocument: async (documentId: string): Promise<{ success: boolean }> => {
    const res = await api.delete<{ success: boolean }>(`/api/documents/${documentId}`);
    return res.data;
  },

  retryDocument: async (documentId: string): Promise<DocumentItem> => {
    const res = await api.post<DocumentItem>(`/api/documents/${documentId}/retry`);
    return res.data;
  },

  // Chat
  askQuestion: async (documentId: string, question: string): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>('/api/chat', {
      document_id: documentId,
      question,
    });
    return res.data;
  },
};

