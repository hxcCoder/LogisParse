// src/components/common/StatusBadge.tsx

'use client';

import { DocumentStatus } from '@/types';
import { FaClock, FaSpinner, FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from 'react-icons/fa';

interface StatusBadgeProps {
    status: DocumentStatus;
    className?: string;
}

const statusConfig = {
PENDING: {
    label: 'Pendiente',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: FaClock,
},
PROCESSING: {
    label: 'Procesando',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: FaSpinner,
},
EXTRACTED: {
    label: 'Extraído',
    color: 'bg-green-100 text-green-800 border-green-300',
    icon: FaCheckCircle,
},
FAILED: {
    label: 'Falló',
    color: 'bg-red-100 text-red-800 border-red-300',
    icon: FaTimesCircle,
},
NEEDS_REVIEW: {
    label: 'Revisión',
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: FaExclamationTriangle,
},
};

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
const config = statusConfig[status];
const Icon = config?.icon || FaClock;

return (
    <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${config?.color} ${className}`}
    >
        <span className="flex items-center justify-center">
        <Icon size={14} />
        </span>
        {config?.label || status}
    </span>
);
}