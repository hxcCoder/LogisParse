// src/app/(dashboard)/documents/[id]/page.tsx

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { documentsApi } from '@/lib/api';
import { Document, CorrectionPayload, ExtractedLogisticsData } from '@/types';
import StatusBadge from '@/components/common/StatusBadge';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import CorrectionForm from '@/components/corrections/CorrectionForm';
import { FaArrowLeft, FaCheckCircle, FaExclamationTriangle, FaInfoCircle } from 'react-icons/fa';
import toast from 'react-hot-toast';

// Lista fija de todos los campos que queremos mostrar (incluso vacíos)
const ALL_FIELDS: (keyof ExtractedLogisticsData)[] = [
  'origen',
  'destino',
  'patente_camion',
  'chofer',
  'fecha_despacho',
  'numero_guia',
  'observaciones',
];

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadDocument = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const response = await documentsApi.get(documentId, token);
      setDocument(response.data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        toast.error('Documento no encontrado');
        router.push('/');
      } else if (error.response?.status === 403) {
        toast.error('No tienes permiso para ver este documento');
        router.push('/');
      } else {
        toast.error('Error al cargar el documento');
      }
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocument();
  }, [documentId, token]);

  const handleCorrectionSuccess = async () => {
    setIsRefreshing(true);
    await loadDocument();
    setIsRefreshing(false);
  };

  const handleSubmitCorrection = async (
    docId: string,
    fieldName: string,
    originalValue: string | null,
    correctedValue: string,
    adapterUsed: string | null
  ) => {
    const payload: CorrectionPayload = {
      field_name: fieldName,
      original_value: originalValue,
      corrected_value: correctedValue,
      adapter_used: adapterUsed,
    };
    await documentsApi.submitCorrection(docId, payload, token!);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Documento no encontrado</p>
        <Link href="/" className="text-blue-600 hover:underline mt-2 inline-block">
          Volver al dashboard
        </Link>
      </div>
    );
  }

  const data = document.extracted_data;
  const isNeedsReview = document.status === 'NEEDS_REVIEW';
  const isExtracted = document.status === 'EXTRACTED';
  const isFailed = document.status === 'FAILED';

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/"
          className="text-slate-500 hover:text-slate-700 transition-colors"
        >
          <span>
            <FaArrowLeft size={20} />
          </span>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-[#0F172A] truncate">
            {document.filename}
          </h1>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <StatusBadge status={document.status} />
            {data?.confidence_score !== undefined && data?.confidence_score !== null && (
              <span
                className={`text-sm font-medium ${
                  data.confidence_score >= 80
                    ? 'text-green-600'
                    : data.confidence_score >= 50
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}
              >
                Confianza: {Math.round(data.confidence_score)}%
              </span>
            )}
            {data?.adapter_used && (
              <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded-full">
                {data.adapter_used}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Datos extraídos */}
        <div className="md:col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-[#0F172A] mb-4">
              📋 Datos extraídos
            </h2>

            {isFailed ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                <p className="font-medium">Error en el procesamiento</p>
                <p className="text-sm mt-1">{document.error_logs || 'Error desconocido'}</p>
              </div>
            ) : data ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {ALL_FIELDS.map((key) => {
                  const value = data[key];
                  const displayValue =
                    value !== null && value !== undefined && value !== ''
                      ? String(value)
                      : '—';
                  return (
                    <div key={key} className="border-b border-slate-100 pb-2">
                      <p className="text-xs text-slate-400 uppercase tracking-wider">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className="text-sm font-medium text-[#0F172A] mt-0.5">
                        {displayValue}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No se extrajeron datos</p>
            )}
          </div>
        </div>

        {/* Sidebar: Estado del pipeline + acciones */}
        <div className="md:col-span-1 space-y-4">
          {/* Estado del documento */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Estado
            </h3>
            <div className="flex items-center gap-2">
              {isExtracted && (
                <>
                  <span className="text-green-500">
                    <FaCheckCircle size={20} />
                  </span>
                  <span className="text-green-700 font-medium">Documento validado</span>
                </>
              )}
              {isNeedsReview && (
                <>
                  <span className="text-orange-500">
                    <FaExclamationTriangle size={20} />
                  </span>
                  <span className="text-orange-700 font-medium">Requiere revisión</span>
                </>
              )}
              {isFailed && (
                <>
                  <span className="text-red-500">
                    <FaInfoCircle size={20} />
                  </span>
                  <span className="text-red-700 font-medium">Error en el proceso</span>
                </>
              )}
            </div>
            {isNeedsReview && (
              <p className="text-xs text-slate-500 mt-2">
                El sistema no está seguro de estos datos. Revisa y corrige los campos necesarios.
              </p>
            )}
          </div>

          {/* Acciones rápidas */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Acciones
            </h3>
            <button
              onClick={() => loadDocument()}
              disabled={isRefreshing}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors disabled:opacity-50"
            >
              {isRefreshing ? 'Actualizando...' : '🔄 Actualizar'}
            </button>
          </div>
        </div>
      </div>

      {/* Formulario de corrección (solo si NEEDS_REVIEW) */}
      {isNeedsReview && data && (
        <div className="mt-6">
          <CorrectionForm
            documentId={document.id}
            extractedData={data}
            onCorrectionSuccess={handleCorrectionSuccess}
            onSubmit={handleSubmitCorrection}
          />
        </div>
      )}
    </div>
  );
}