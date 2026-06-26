// src/components/corrections/CorrectionForm.tsx

'use client';

import { useState } from 'react';
import { ExtractedLogisticsData } from '@/types';
import { FaSave, FaSpinner } from 'react-icons/fa';
import toast from 'react-hot-toast';

interface CorrectionFormProps {
  documentId: string;
  extractedData: ExtractedLogisticsData;
  onCorrectionSuccess: () => void;
  onSubmit: (
    documentId: string,
    fieldName: string,
    originalValue: string | null,
    correctedValue: string,
    adapterUsed: string | null
  ) => Promise<void>;
}

// Todos los campos que queremos mostrar (ordenados)
const ALL_FIELDS: (keyof ExtractedLogisticsData)[] = [
  'origen',
  'destino',
  'patente_camion',
  'chofer',
  'fecha_despacho',
  'numero_guia',
  'observaciones',
];

export default function CorrectionForm({
  documentId,
  extractedData,
  onCorrectionSuccess,
  onSubmit,
}: CorrectionFormProps) {
  // Estado para almacenar los valores corregidos (inicializados con los actuales)
  const [corrections, setCorrections] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const field of ALL_FIELDS) {
      const value = extractedData[field];
      initial[field] = typeof value === 'string' ? value : '';
    }
    return initial;
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (fieldName: string, value: string) => {
    setCorrections((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Recoger solo los campos que cambiaron o que antes estaban vacíos y ahora tienen valor
    const correctionsToSend: { field: string; original: string | null; corrected: string }[] = [];

    for (const field of ALL_FIELDS) {
      const original = extractedData[field] as string | null;
      const corrected = corrections[field]?.trim() || '';
      // Enviar si:
      // - El usuario escribió algo y antes estaba vacío (original null o vacío)
      // - O el usuario cambió el valor
      if (corrected && (original === null || original === undefined || original.trim() === '' || corrected !== original)) {
        correctionsToSend.push({
          field,
          original: original || null,
          corrected,
        });
      }
    }

    if (correctionsToSend.length === 0) {
      toast.error('No has realizado ninguna corrección');
      return;
    }

    setIsSubmitting(true);
    try {
      for (const { field, original, corrected } of correctionsToSend) {
        await onSubmit(
          documentId,
          field,
          original,
          corrected,
          extractedData.adapter_used || null
        );
      }
      toast.success(`✅ ${correctionsToSend.length} corrección(es) enviada(s)`);
      // Resetear el estado de correcciones a los nuevos valores (para que no se reenvíen)
      const newCorrections: Record<string, string> = {};
      for (const field of ALL_FIELDS) {
        newCorrections[field] = corrections[field] || '';
      }
      setCorrections(newCorrections);
      onCorrectionSuccess();
    } catch (error) {
      toast.error('Error al enviar las correcciones');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-[#0F172A] mb-4">
        ✏️ Corregir campos
      </h3>
      <p className="text-sm text-slate-500 mb-4">
        Completa o corrige los campos que el sistema no pudo extraer correctamente.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {ALL_FIELDS.map((field) => {
          const label = field.replace(/_/g, ' ');
          const value = corrections[field] || '';
          const original = extractedData[field] as string | null;

          return (
            <div key={field} className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-start">
              <label className="text-sm font-medium text-slate-700 capitalize pt-2">
                {label}
              </label>
              <div>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleChange(field, e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder={original && original.trim() ? `Original: ${original}` : 'No disponible, ingresa un valor'}
                  disabled={isSubmitting}
                />
                {original && original.trim() && (
                  <p className="text-xs text-slate-400 mt-1">
                    Original: <span className="font-mono">{original}</span>
                  </p>
                )}
              </div>
            </div>
          );
        })}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors shadow-md disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin">
                <FaSpinner size={18} />
              </span>
              Enviando correcciones...
            </>
          ) : (
            <>
              <span>
                <FaSave size={18} />
              </span>
              Enviar correcciones
            </>
          )}
        </button>
      </form>
    </div>
  );
}