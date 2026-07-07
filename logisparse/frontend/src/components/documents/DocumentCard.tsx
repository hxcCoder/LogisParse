'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Document } from '@/types';
import StatusBadge from '@/components/common/StatusBadge';
import { FaEye, FaFile, FaCalendar, FaEdit, FaSave } from 'react-icons/fa';

interface DocumentCardProps {
  document: Document;
}

export default function DocumentCard({ document }: DocumentCardProps) {
  const confidence = document.extracted_data?.confidence_score;
  const extracted = document.extracted_data;

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    chofer: extracted?.chofer || '',
    patente_camion: extracted?.patente_camion || '',
    origen: extracted?.origen || '',
    destino: extracted?.destino || '',
  });

  const [showFiscal, setShowFiscal] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    // Aquí puedes llamar a tu API para persistir los cambios
    // await documentsApi.update(document.id, formData, token);
    setIsEditing(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow p-6">
      {/* Cabecera */}
      <div className="flex items-start justify-between border-b border-slate-100 pb-4 mb-4">
        <div className="flex items-start gap-4 min-w-0">
          <div className="bg-blue-50 text-blue-600 p-3 rounded-lg flex-shrink-0">
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

        <div className="flex flex-col items-end gap-3 flex-shrink-0 ml-4">
          <span className="text-sm text-slate-500 flex items-center gap-1.5 whitespace-nowrap">
            <FaCalendar size={14} />
            {formatDate(document.created_at)}
          </span>
          <div className="flex items-center gap-4">
            <button
              onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
              className={`flex items-center gap-1.5 text-sm font-medium transition-colors ${
                isEditing
                  ? 'text-green-600 hover:text-green-700'
                  : 'text-orange-500 hover:text-orange-600'
              }`}
            >
              {isEditing ? (
                <>
                  <FaSave size={16} /> Guardar
                </>
              ) : (
                <>
                  <FaEdit size={16} /> Editar
                </>
              )}
            </button>
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

      {/* Datos de transporte */}
      <div>
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Datos de Transporte
        </h4>

        {isEditing ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Chofer</label>
              <input
                name="chofer"
                value={formData.chofer}
                onChange={handleChange}
                className="w-full text-sm p-2 border border-slate-300 rounded focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Patente</label>
              <input
                name="patente_camion"
                value={formData.patente_camion}
                onChange={handleChange}
                className="w-full text-sm p-2 border border-slate-300 rounded focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Origen</label>
              <input
                name="origen"
                value={formData.origen}
                onChange={handleChange}
                className="w-full text-sm p-2 border border-slate-300 rounded focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Destino</label>
              <input
                name="destino"
                value={formData.destino}
                onChange={handleChange}
                className="w-full text-sm p-2 border border-slate-300 rounded focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-3 gap-x-4 bg-slate-50/50 p-4 rounded-lg">
            {['chofer', 'patente_camion', 'origen', 'destino'].map((field) => (
              <div key={field}>
                <p className="text-xs font-semibold text-slate-500">
                  {field === 'patente_camion' ? 'Patente' : field.charAt(0).toUpperCase() + field.slice(1)}
                </p>
                <p className="text-sm font-medium text-slate-800">
                  {(extracted as any)?.[field] || '—'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Datos fiscales colapsables */}
      <div className="mt-4">
        <button
          onClick={() => setShowFiscal(!showFiscal)}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
        >
          {showFiscal ? '▼ Ocultar datos fiscales' : '▶ Ver datos fiscales'}
        </button>
        {showFiscal && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-2 gap-x-4 mt-2 p-3 bg-slate-50/50 rounded-lg border border-slate-200">
            <div>
              <p className="text-xs font-semibold text-slate-500">RUT Emisor</p>
              <p className="text-sm font-medium text-slate-800">
                {extracted?.rut_emisor || '—'}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">RUT Receptor</p>
              <p className="text-sm font-medium text-slate-800">
                {extracted?.rut_receptor || '—'}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">Folio SII</p>
              <p className="text-sm font-medium text-slate-800">
                {extracted?.folio_sii || '—'}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">Monto Total</p>
              <p className="text-sm font-medium text-slate-800">
                {extracted?.monto_total ? `$${extracted.monto_total}` : '—'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}