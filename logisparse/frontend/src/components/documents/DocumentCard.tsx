// src/components/documents/DocumentCard.tsx

'use client';

import Link from 'next/link';
import { Document } from '@/types';
import StatusBadge from '@/components/common/StatusBadge';
import { FaEye, FaFile, FaCalendar } from 'react-icons/fa';

interface DocumentCardProps {
  document: Document;
}

export default function DocumentCard({ document }: DocumentCardProps) {
  const confidence = document.extracted_data?.confidence_score;

  // Formatear fecha manualmente sin date-fns (evita dependencia adicional)
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between">
        {/* Icono + Nombre */}
        <div className="flex items-start gap-4 min-w-0">
          <div className="bg-blue-50 p-3 rounded-lg flex-shrink-0">
            <FaFile size={20} />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-[#0F172A] text-lg truncate max-w-[200px] sm:max-w-xs">
              {document.filename}
            </h3>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
              <StatusBadge status={document.status} />
              {confidence !== undefined && confidence !== null && (
                <span
                  className={`text-sm font-medium ${
                    confidence >= 80
                      ? 'text-green-600'
                      : confidence >= 50
                      ? 'text-yellow-600'
                      : 'text-red-600'
                  }`}
                >
                  Confianza: {Math.round(confidence)}%
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Fecha + Botón */}
        <div className="flex flex-col items-end gap-3 flex-shrink-0 ml-4">
          <span className="text-sm text-slate-500 flex items-center gap-1.5 whitespace-nowrap">
            <FaCalendar size={14} />
            {formatDate(document.created_at)}
          </span>
          <Link
            href={`/documents/${document.id}`}
            className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            <FaEye size={16} />
            Ver detalle
          </Link>
        </div>
      </div>
    </div>
  );
}