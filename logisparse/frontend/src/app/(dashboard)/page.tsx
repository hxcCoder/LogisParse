// src/app/(dashboard)/page.tsx

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { documentsApi } from '@/lib/api';
import { Document } from '@/types';
import DocumentCard from '@/components/documents/DocumentCard';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { FaPlus, FaFileAlt } from 'react-icons/fa';
import toast from 'react-hot-toast';

export default function DashboardPage() {
  const { user, token } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 10;

  const loadDocuments = async (currentSkip: number) => {
    if (!token) return;
    setIsLoading(true);
    try {
      const response = await documentsApi.list(token, currentSkip, limit);
      const data = response.data;
      if (currentSkip === 0) {
        setDocuments(data);
      } else {
        setDocuments((prev) => [...prev, ...data]);
      }
      setHasMore(data.length === limit);
    } catch (error) {
      toast.error('Error al cargar los documentos');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments(0);
  }, [token]);

  const loadMore = () => {
    if (!isLoading && hasMore) {
      const newSkip = skip + limit;
      setSkip(newSkip);
      loadDocuments(newSkip);
    }
  };

  if (isLoading && documents.length === 0) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#0F172A]">Dashboard</h1>
          <p className="text-slate-500 mt-1">
            Bienvenido, {user?.full_name || user?.email || 'Usuario'}
          </p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-5 rounded-lg transition-colors shadow-md flex-shrink-0"
        >
          <span className="flex items-center justify-center">
            <FaPlus size={16} />
          </span>
          Nuevo documento
        </Link>
      </div>

      {/* Lista de documentos */}
      {documents.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center border border-slate-200">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-50 p-4 rounded-full">
              <FaFileAlt size={32} />
            </div>
          </div>
          <h2 className="text-xl font-semibold text-[#0F172A]">Aún no hay documentos</h2>
          <p className="text-slate-500 mt-2 max-w-sm mx-auto">
            Sube tu primer documento para comenzar a extraer información automáticamente
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 mt-6 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors shadow-md"
          >
            <span className="flex items-center justify-center">
              <FaPlus size={16} />
            </span>
            Subir primer documento
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}

          {/* Cargar más */}
          {hasMore && (
            <div className="flex justify-center pt-4">
              <button
                onClick={loadMore}
                disabled={isLoading}
                className="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg text-sm font-medium text-slate-700 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Cargando...' : 'Cargar más documentos'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}