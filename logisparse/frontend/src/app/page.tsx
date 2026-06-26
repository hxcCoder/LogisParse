// src/app/page.tsx

'use client';

import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { FaPlus } from 'react-icons/fa';

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#0F172A]">Dashboard</h1>
          <p className="text-slate-500 mt-1">
            Bienvenido, {user?.full_name || user?.email || 'Usuario'}
          </p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-5 rounded-lg transition-colors shadow-md"
        >
          <span className="flex items-center justify-center">
            <FaPlus size={16} />
          </span>
          Nuevo documento
        </Link>
      </div>

      {/* Placeholder: lista de documentos */}
      <div className="bg-white rounded-xl shadow-sm p-8 text-center text-slate-500 border border-slate-200">
        <p className="text-lg">Aún no hay documentos</p>
        <p className="text-sm mt-1">Sube tu primer documento para comenzar</p>
      </div>
    </div>
  );
}