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
  adapter_used?: string | null;
  confidence_score?: number | null;
  [key: string]: any; 
};

// Añadimos el tipo DocumentResponse que usabas en tu page.tsx
export type DocumentResponse = {
  id: string;
  filename: string;
  content_type: string;
  status: DocumentStatus;
  extracted_data: ExtractedLogisticsData | null;
  error_logs: any | null;
  created_at: string;
  updated_at: string;
};

const API_URL = "http://localhost:8000/api/v1";

// Función para obtener el token del localStorage
const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return {
    Authorization: `Bearer ${token}`,
  };
};

// Función para subir el documento
export const uploadDocument = async (file: File): Promise<DocumentResponse> => {
  const formData = new FormData();
  formData.append("file", file); // El backend de FastAPI espera un campo llamado "file"

  const res = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    headers: { ...getAuthHeaders() }, // No enviamos "Content-Type", el navegador lo genera automáticamente con el FormData
    body: formData,
  });

  if (!res.ok) throw new Error("Error al subir el documento");
  return res.json();
};