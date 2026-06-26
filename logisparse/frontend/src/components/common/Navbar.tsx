// src/components/common/Navbar.tsx

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { FaFileAlt, FaUpload, FaSignOutAlt, FaUser } from 'react-icons/fa';

export default function Navbar() {
const pathname = usePathname();
const { user, logout } = useAuth();

const isActive = (path: string) => pathname === path;

return (
    <nav className="bg-[#0F172A] text-white shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
            <span className="text-blue-400">Logis</span>
            <span>Parse</span>
        </Link>

          {/* Enlaces centrales */}
        <div className="hidden md:flex items-center gap-6">
            <Link
                href="/"
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
            >
                <span className="flex items-center justify-center">
                <FaFileAlt size={16} />
                </span>
                Dashboard
            </Link>
            <Link
                href="/upload"
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/upload') ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
            >
                <span className="flex items-center justify-center">
                <FaUpload size={16} />
                </span>
                Subir
            </Link>
            </div>

          {/* Perfil + Logout */}
        <div className="flex items-center gap-4">
            <span className="hidden sm:inline text-sm text-slate-300">
                <span className="inline-flex items-center gap-1.5">
                <FaUser size={14} />
                {user?.full_name || user?.email || 'Usuario'}
                </span>
            </span>
            <button
                onClick={logout}
                className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium bg-red-600 hover:bg-red-700 transition-colors"
            >
                <span className="flex items-center justify-center">
                <FaSignOutAlt size={16} />
                </span>
                <span className="hidden sm:inline">Cerrar sesión</span>
            </button>
            </div>
        </div>
        </div>
    </nav>
);
}