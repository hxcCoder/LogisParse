"use client";

import { useState, useRef } from "react";
import { uploadDocument, type DocumentResponse } from "@/lib/api";

const pipeline = [
  { label: "Texto", detail: "PDF u OCR local", tone: "bg-sea" },
  { label: "Regex", detail: "Extraccion deterministica", tone: "bg-kelp" },
  { label: "Normalizar", detail: "Campos y formato", tone: "bg-amber" },
  { label: "IA parcial", detail: "Solo fragmentos dudosos", tone: "bg-salmon" },
  { label: "Revision", detail: "Humano valida", tone: "bg-ink" }
];

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  
  // Empezamos con tu documento demo por defecto, pero lo actualizaremos con el real
  const [document, setDocument] = useState<DocumentResponse | null>({
    id: "demo-001",
    filename: "guia-despacho-salmon.pdf",
    content_type: "application/pdf",
    status: "EXTRACTED",
    extracted_data: {
      origen: "Puerto Montt",
      destino: "Santiago",
      patente_camion: "ABCD12",
      chofer: "Juan Perez",
      fecha_despacho: "2026-01-01",
      numero_guia: "123456",
      observaciones: "Requiere revision humana final"
    },
    error_logs: null,
    created_at: "2026-01-01T09:00:00Z",
    updated_at: "2026-01-01T09:00:10Z"
  });

  // Función que se ejecuta cuando el usuario selecciona un archivo
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      // Llamamos a la API real
      const realDoc = await uploadDocument(file);
      setDocument(realDoc); // Actualizamos la pantalla con los datos reales de la IA
    } catch (error) {
      console.error(error);
      alert("Hubo un error subiendo el documento. Revisa la consola.");
    } finally {
      setIsUploading(false);
      // Limpiamos el input para poder subir el mismo archivo de nuevo si es necesario
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const fields = [
    ["Origen", document?.extracted_data?.origen],
    ["Destino", document?.extracted_data?.destino],
    ["Patente", document?.extracted_data?.patente_camion],
    ["Chofer", document?.extracted_data?.chofer],
    ["Fecha", document?.extracted_data?.fecha_despacho],
    ["Guia", document?.extracted_data?.numero_guia]
  ];

  return (
    <main className="min-h-screen bg-[#f5f7fa] text-ink">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sea">
              Concurso INACAP
            </p>
            <h1 className="text-2xl font-semibold">LogisParse</h1>
          </div>
          <div className="rounded border border-line px-3 py-2 text-sm text-slate-600">
            API: localhost:8000
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-md border border-line bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Bandeja de verificacion</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Interfaz pensada para administrativos: subir documento, ver campos
              detectados y marcar revision final sin exponer complejidad tecnica.
            </p>
            
            {/* Input oculto para manejar el archivo */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept=".pdf,.png,.jpg,.jpeg" 
            />
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className={`mt-5 w-full rounded px-4 py-3 text-sm font-semibold text-white ${isUploading ? 'bg-gray-400 cursor-wait' : 'bg-ink hover:bg-slate-800'}`}
            >
              {isUploading ? "Procesando con IA..." : "Subir PDF o imagen"}
            </button>
          </div>

          <div className="rounded-md border border-line bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Estado</h2>
            <div className="mt-4 space-y-3">
              {pipeline.map((step) => (
                <div key={step.label} className="flex items-center gap-3">
                  <span className={`h-3 w-3 rounded-sm ${step.tone}`} />
                  <div>
                    <p className="text-sm font-semibold">{step.label}</p>
                    <p className="text-xs text-slate-500">{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="space-y-6">
          <div className="rounded-md border border-line bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line px-5 py-4">
              <div>
                <h2 className="text-lg font-semibold">{document?.filename || "Sin documento"}</h2>
                <p className="text-sm text-slate-500">Documento extraido y listo para revision</p>
              </div>
              <span className={`rounded border px-3 py-1 text-xs font-semibold ${document?.status === 'NEEDS_REVIEW' ? 'border-amber text-amber' : 'border-kelp text-kelp'}`}>
                {document?.status || "PENDING"}
              </span>
            </div>

            <div className="grid gap-px bg-line md:grid-cols-3">
              {fields.map(([label, value], idx) => (
                <div key={idx} className="bg-white p-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                    {label}
                  </p>
                  <p className="mt-2 text-base font-semibold">{value ? String(value) : "Pendiente"}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-md border border-line bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Uso de IA</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                El backend envia solo fragmentos asociados a campos faltantes o
                inconsistentes. Regex y normalizacion local conservan prioridad.
              </p>
            </div>

            <div className="rounded-md border border-line bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Trazabilidad</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Cada documento conserva estado, errores y JSON extraido para que
                una persona pueda auditar la decision antes de cerrar el proceso.
              </p>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}