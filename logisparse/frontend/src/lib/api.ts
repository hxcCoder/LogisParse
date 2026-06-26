// src/lib/api.ts

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { AuthTokens, CorrectionPayload, Document, LoginCredentials, RegisterPayload } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Request Interceptor: Inyecta el token ---
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response Interceptor: Maneja 401 global ---
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Disparar evento global para que AuthContext haga logout
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('unauthorized'));
      }
    }
    return Promise.reject(error);
  }
);

// --- Métodos de API (encapsulados) ---

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<{ id: string; email: string; full_name: string; is_active: boolean; created_at: string }>(
      '/api/v1/auth/register',
      payload
    ),

  login: (credentials: LoginCredentials) =>
    apiClient.post<AuthTokens>('/api/v1/auth/login', credentials),
};

export const documentsApi = {
  upload: (file: File, token: string) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<Document>('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    });
  },

  list: (token: string, skip: number = 0, limit: number = 50) =>
    apiClient.get<Document[]>(`/api/v1/documents?skip=${skip}&limit=${limit}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  get: (id: string, token: string) =>
    apiClient.get<Document>(`/api/v1/documents/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  submitCorrection: (id: string, payload: CorrectionPayload, token: string) =>
    apiClient.post<{ id: string; document_id: string; field_name: string; corrected_value: string; created_at: string }>(
      `/api/v1/documents/${id}/corrections`,
      payload,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    ),
};