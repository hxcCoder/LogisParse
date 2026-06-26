// src/components/common/ProtectedRoute.tsx

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import LoadingSpinner from './LoadingSpinner';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { token, isLoading } = useAuth();
    const router = useRouter();

useEffect(() => {
    if (!isLoading && !token) {
        router.push('/login');
    }
}, [token, isLoading, router]);

if (isLoading) {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
            <LoadingSpinner size="lg" />
        </div>
    );
}

if (!token) {
    return null; // No renderiza nada mientras redirige
}

return <>{children}</>;
}