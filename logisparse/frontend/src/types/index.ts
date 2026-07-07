// src/types/index.ts

export interface User {
    id: string;
    email: string;
    full_name: string | null;
    is_active: boolean;
    created_at: string;
}

export type DocumentStatus =
    | "PENDING"
    | "PROCESSING"
    | "EXTRACTED"
    | "FAILED"
    | "NEEDS_REVIEW";

export interface ExtractedLogisticsData {
  // --- Campos SII (nuevos) ---
    rut_emisor?: string | null;
    rut_receptor?: string | null;
    folio_sii?: string | null;
    fecha_emision?: string | null;
    monto_total?: string | null;
  
    // --- Campos logísticos ---
    origen?: string | null;
    destino?: string | null;
    patente_camion?: string | null;
    chofer?: string | null;
    fecha_despacho?: string | null;
    numero_guia?: string | null;
    observaciones?: string | null;
  
    // --- Metadatos ---
    adapter_used?: string | null;
    confidence_score?: number | null;

  // Permitir campos extra (ya estaba)
    [key: string]: any;
}

export interface Document {
    id: string;
    filename: string;
    content_type: string | null;
    status: DocumentStatus;
    extracted_data: ExtractedLogisticsData | null;
    error_logs: string | null;
    created_at: string;
    updated_at: string;
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

export interface TokenResponse {
    access_token: string;
   token_type: string;
}

export interface CorrectionPayload {
    field_name: string;
    original_value: string | null;
    corrected_value: string;
    adapter_used: string | null;
}