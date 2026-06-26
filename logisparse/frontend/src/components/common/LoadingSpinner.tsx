// src/components/common/LoadingSpinner.tsx

'use client';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const sizeClasses = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
};

export default function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
    return (
        <div
            className={`inline-block animate-spin rounded-full border-solid border-blue-600 border-t-transparent ${sizeClasses[size]} ${className}`}
            role="status"
            aria-label="Cargando..."
    />
);
}