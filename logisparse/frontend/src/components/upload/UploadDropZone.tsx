// src/components/upload/UploadDropzone.tsx

'use client';

import { useRef, useState, DragEvent } from 'react';
import { FaCloudUploadAlt, FaFile } from 'react-icons/fa';
import toast from 'react-hot-toast';

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  isLoading: boolean;
}

export default function UploadDropzone({
  onFileSelect,
  selectedFile,
  isLoading,
}: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (isLoading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (validTypes.includes(file.type)) {
        onFileSelect(file);
      } else {
        toast.error('Formato no soportado. Usa PDF, PNG o JPG.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (validTypes.includes(file.type)) {
        onFileSelect(file);
      } else {
        toast.error('Formato no soportado. Usa PDF, PNG o JPG.');
      }
    }
  };

  const handleClick = () => {
    if (!isLoading && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-white hover:bg-slate-50'}
        ${isLoading ? 'opacity-60 pointer-events-none' : ''}
      `}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={handleFileChange}
        disabled={isLoading}
      />

      <div className="flex flex-col items-center justify-center text-center gap-3">
        {selectedFile ? (
          <>
            <div className="bg-blue-100 p-4 rounded-full">
              <span className="text-blue-600">
                <FaFile size={32} />
              </span>
            </div>
            <div className="max-w-full">
              <p className="font-semibold text-[#0F172A] truncate">
                {selectedFile.name}
              </p>
              <p className="text-sm text-slate-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              {!isLoading && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onFileSelect(null as any);
                  }}
                  className="mt-2 text-sm text-red-500 hover:text-red-600 font-medium"
                >
                  Cambiar archivo
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            <span className="text-blue-500">
              <FaCloudUploadAlt size={48} />
            </span>
            <div>
              <p className="text-lg font-semibold text-[#0F172A]">
                Arrastra tu documento aquí
              </p>
              <p className="text-sm text-slate-500 mt-1">
                o haz clic para seleccionarlo (PDF, PNG, JPG)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}