// src/types/index.ts

export type DocumentStatus =
    | 'PENDING'
    | 'PROCESSING'
    | 'EXTRACTED'
    | 'FAILED'
    | 'NEEDS_REVIEW';

export interface ExtractedLogisticsData {
    origen?: string | null;
    destino?: string | null;
    patente_camion?: string | null;
    chofer?: string | null;
    fecha_despacho?: string | null;
    numero_guia?: string | null;
    observaciones?: string | null;
    adapter_used?: string | null;
    confidence_score?: number | null;
}

export interface Document {
    id: string;
    filename: string;
    content_type?: string | null;
    status: DocumentStatus;
    extracted_data?: ExtractedLogisticsData | null;
    error_logs?: string | null;
    created_at: string; // ISO Date string
    updated_at: string; // ISO Date string
}

export interface User {
    id: string;
    email: string;
    full_name?: string | null;
    is_active: boolean;
    created_at: string;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterPayload {
    email: string;
    password: string;
    full_name?: string;
}

export interface AuthTokens {
    access_token: string;
    token_type: 'bearer';
}

export interface CorrectionPayload {
    field_name: string;
    original_value?: string | null;
    corrected_value: string;
    adapter_used?: string | null;
}

export interface CorrectionResponse {
    id: string;
    document_id: string;
    field_name: string;
    original_value?: string | null;
    corrected_value?: string | null;
    adapter_used?: string | null;
    created_at: string;
}

export interface ApiError {
    detail: string;
}