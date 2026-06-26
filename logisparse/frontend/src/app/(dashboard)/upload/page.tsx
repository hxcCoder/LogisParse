// src/app/(dashboard)/upload/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { documentsApi } from '@/lib/api';
import UploadDropzone from '@/components/upload/UploadDropZone';
import PipelineVisual, { Step } from '@/components/upload/PipelineVisual';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { FaArrowLeft } from 'react-icons/fa';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function UploadPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [steps, setSteps] = useState<Step[]>([
    { id: '1', label: 'Recibiendo documento', status: 'idle' },
    { id: '2', label: 'Extrayendo texto (OCR)', status: 'idle' },
    { id: '3', label: 'Analizando con IA', status: 'idle' },
    { id: '4', label: 'Validando datos', status: 'idle' },
  ]);

  const updateStep = (index: number, status: Step['status']) => {
    setSteps((prev) => prev.map((s, i) => (i === index ? { ...s, status } : s)));
  };

  const simulatePipeline = async () => {
    // Paso 1: Recibido
    updateStep(0, 'processing');
    await new Promise((resolve) => setTimeout(resolve, 600));
    updateStep(0, 'done');

    // Paso 2: OCR
    updateStep(1, 'processing');
    await new Promise((resolve) => setTimeout(resolve, 800));
    updateStep(1, 'done');

    // Paso 3: IA
    updateStep(2, 'processing');
    await new Promise((resolve) => setTimeout(resolve, 1000));
    updateStep(2, 'done');

    // Paso 4: Validación
    updateStep(3, 'processing');
    await new Promise((resolve) => setTimeout(resolve, 600));
    updateStep(3, 'done');
  };

  const handleUpload = async () => {
    if (!file || !token) {
      toast.error('Selecciona un archivo primero');
      return;
    }

    setIsLoading(true);
    // Reiniciar pipeline
    setSteps((prev) => prev.map((s) => ({ ...s, status: 'idle' })));

    try {
      // Iniciar animación del pipeline en paralelo
      const pipelinePromise = simulatePipeline();

      // Subir el archivo
      const response = await documentsApi.upload(file, token);
      const documentId = response.data.id;

      // Esperar a que termine la animación (por si acaso)
      await pipelinePromise;

      toast.success('Documento procesado exitosamente 🎉');
      router.push(`/documents/${documentId}`);
    } catch (error: any) {
      // Marcar el último paso como error
      setSteps((prev) =>
        prev.map((s, i) =>
          i === prev.length - 1 ? { ...s, status: 'error' } : s
        )
      );
      const message = error.response?.data?.detail || 'Error al subir el documento';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/"
          className="text-slate-500 hover:text-slate-700 transition-colors"
        >
          <FaArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A]">Subir documento</h1>
          <p className="text-slate-500 text-sm">
            Arrastra tu archivo o haz clic para seleccionarlo
          </p>
        </div>
      </div>

      {/* Contenido */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Dropzone */}
        <div className="md:col-span-2">
          <UploadDropzone
            onFileSelect={setFile}
            selectedFile={file}
            isLoading={isLoading}
          />

          {/* Botón de acción */}
          {file && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleUpload}
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-8 rounded-lg transition-colors shadow-md disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Procesando...
                  </>
                ) : (
                  'Subir documento'
                )}
              </button>
            </div>
          )}
        </div>

        {/* Pipeline Visual */}
        <div className="md:col-span-1">
          <PipelineVisual steps={steps} />
        </div>
      </div>
    </div>
  );
}