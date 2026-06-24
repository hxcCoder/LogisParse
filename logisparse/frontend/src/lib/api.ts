// logisparse/frontend/src/lib/api.ts

export type DocumentStatus = "PENDING" | "PROCESSING" | "EXTRACTED" | "FAILED" | "NEEDS_REVIEW";

export type ExtractedLogisticsData = {
  origen: string | null;
  destino: string | null;
  patente_camion: string | null;
  chofer: string | null;
  fecha_despacho: string | null;
  numero_guia: string | null;
  observaciones: string | null;
  
  // Nuevos campos dinámicos
  adapter_used?: string | null;
  confidence_score?: number | null;
  // Permite cualquier otro campo extra que venga del backend (Ej. peso_carga)
  [key: string]: any; 
};