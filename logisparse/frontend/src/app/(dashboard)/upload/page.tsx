// src/app/(dashboard)/upload/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { documentsApi } from '@/lib/api';
import UploadDropzone from '@/components/upload/UploadDropZone'; // Ojo con la Z mayúscula si tu archivo es así
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
  
  const initialSteps: Step[] = [
    { id: '1', label: 'Recibiendo documento', status: 'idle' },
    { id: '2', label: 'Extrayendo texto (OCR)', status: 'idle' },
    { id: '3', label: 'Analizando con IA', status: 'idle' },
    { id: '4', label: 'Validando datos', status: 'idle' },
  ];
  
  const [steps, setSteps] = useState<Step[]>(initialSteps);

  const updateStep = (index: number, status: Step['status']) => {
    setSteps((prev) => prev.map((s, i) => (i === index ? { ...s, status } : s)));
  };

  // Función auxiliar para pausas visuales
  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const handleUpload = async () => {
    if (!file || !token) {
      toast.error('Selecciona un archivo primero');
      return;
    }

    setIsLoading(true);
    setSteps(initialSteps);

    try {
      // 1. Recibiendo documento
      updateStep(0, 'processing');
      await sleep(600); // Pequeña pausa visual
      
      // Iniciamos la subida REAL al backend
      const uploadPromise = documentsApi.upload(file, token);
      updateStep(0, 'done');

      // 2. Extrayendo texto (OCR visual)
      updateStep(1, 'processing');
      await sleep(1000);
      updateStep(1, 'done');

      // 3. Analizando con IA (Esperamos a que el backend termine realmente aquí)
      updateStep(2, 'processing');
      const response = await uploadPromise; // Aquí se resuelve la petición real
      updateStep(2, 'done');

      // 4. Validando datos
      updateStep(3, 'processing');
      await sleep(600);
      updateStep(3, 'done');

      // Éxito real
      const documentId = response.data.id;
      toast.success('Documento procesado exitosamente 🎉');
      
      // Esperamos medio segundo para que el usuario vea todos los ticks verdes
      await sleep(500); 
      router.push(`/documents/${documentId}`);

    } catch (error: any) {
      console.error(error);
      // Encontrar el paso que estaba en 'processing' y ponerlo en 'error'
      setSteps((prev) =>
        prev.map((s) => (s.status === 'processing' ? { ...s, status: 'error' } : s))
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
        <Link href="/" className="text-slate-500 hover:text-slate-700 transition-colors">
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
        <div className="md:col-span-2">
          <UploadDropzone
            onFileSelect={setFile}
            selectedFile={file}
            isLoading={isLoading}
          />

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

        <div className="md:col-span-1">
          <PipelineVisual steps={steps} />
        </div>
      </div>
    </div>
  );
}