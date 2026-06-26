// src/app/(dashboard)/layout.tsx

'use client';

import ProtectedRoute from '@/components/common/ProtectedRoute';
import Navbar from '@/components/common/Navbar';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
return (
    <ProtectedRoute>
        <Navbar />
        <main className="min-h-screen bg-[#F8FAFC] py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">{children}</div>
        </main>
    </ProtectedRoute>
);
}