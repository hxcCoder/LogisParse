// src/components/upload/PipelineVisual.tsx

'use client';

import { FaCheckCircle, FaSpinner, FaCircle } from 'react-icons/fa';

export interface Step {
  id: string;
  label: string;
  status: 'idle' | 'processing' | 'done' | 'error';
}

interface PipelineVisualProps {
  steps: Step[];
}

export default function PipelineVisual({ steps }: PipelineVisualProps) {
  const getIcon = (status: Step['status']) => {
    switch (status) {
      case 'done':
        return (
          <span className="text-green-500">
            <FaCheckCircle size={20} />
          </span>
        );
      case 'processing':
        return (
          <span className="text-blue-500 animate-spin">
            <FaSpinner size={20} />
          </span>
        );
      case 'error':
        return (
          <span className="text-red-500">
            <FaCircle size={20} />
          </span>
        );
      default:
        return (
          <span className="text-slate-300">
            <FaCircle size={20} />
          </span>
        );
    }
  };

  const getLineColor = (status: Step['status']) => {
    return status === 'idle' ? 'bg-slate-200' : 
           status === 'done' ? 'bg-green-500' :
           status === 'error' ? 'bg-red-500' :
           'bg-blue-500';
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6">
        Pipeline de procesamiento
      </h3>
      <div className="space-y-0">
        {steps.map((step, index) => (
          <div key={step.id} className="relative">
            {/* Línea conectora */}
            {index < steps.length - 1 && (
              <div
                className={`absolute left-[9px] top-[30px] w-0.5 h-[30px] transition-colors duration-500 ${getLineColor(step.status)}`}
              />
            )}

            <div className="flex items-start gap-4 py-2">
              <div className="flex-shrink-0 w-5 h-5 mt-0.5 flex items-center justify-center">
                {getIcon(step.status)}
              </div>
              <div className="flex-1">
                <p
                  className={`font-medium text-sm ${
                    step.status === 'idle' ? 'text-slate-400' :
                    step.status === 'done' ? 'text-green-700' :
                    step.status === 'error' ? 'text-red-600' :
                    'text-blue-700'
                  }`}
                >
                  {step.label}
                </p>
                {step.status === 'processing' && (
                  <p className="text-xs text-slate-400 mt-0.5">Procesando...</p>
                )}
                {step.status === 'done' && (
                  <p className="text-xs text-green-500 mt-0.5">Completado</p>
                )}
                {step.status === 'error' && (
                  <p className="text-xs text-red-500 mt-0.5">Error</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}