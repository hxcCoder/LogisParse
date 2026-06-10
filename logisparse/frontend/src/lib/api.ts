export type DocumentStatus = "PENDING" | "PROCESSING" | "EXTRACTED" | "FAILED";

export type ExtractedLogisticsData = {
  origen: string | null;
  destino: string | null;
  patente_camion: string | null;
  chofer: string | null;
  fecha_despacho: string | null;
  numero_guia: string | null;
  observaciones: string | null;
};

export type DocumentResponse = {
  id: string;
  filename: string;
  content_type: string | null;
  status: DocumentStatus;
  extracted_data: ExtractedLogisticsData | null;
  error_logs: string | null;
  created_at: string;
  updated_at: string;
};

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function login(email: string, password: string): Promise<string> {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    throw new Error("No se pudo iniciar sesion");
  }

  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

export async function uploadDocument(file: File, token: string): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData
  });

  if (!response.ok) {
    throw new Error("No se pudo procesar el documento");
  }

  return (await response.json()) as DocumentResponse;
}

export async function listDocuments(token: string): Promise<DocumentResponse[]> {
  const response = await fetch(`${API_URL}/api/v1/documents`, {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!response.ok) {
    throw new Error("No se pudo cargar la bandeja documental");
  }

  return (await response.json()) as DocumentResponse[];
}
