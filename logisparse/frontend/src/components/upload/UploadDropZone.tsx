"use client";

import React, { useCallback, useRef, useState } from 'react';

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  isLoading?: boolean;
}

export default function UploadDropzone({ onFileSelect, selectedFile, isLoading = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const openFilePicker = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    onFileSelect(file);
  }, [onFileSelect]);

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div
        onClick={openFilePicker}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleFiles(e.dataTransfer.files); }}
        className={`w-full border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${isDragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-white'}`}
        aria-label="Upload PDF"
      >
        {isLoading ? (
          <div className="text-sm text-slate-500">Cargando...</div>
        ) : selectedFile ? (
          <div className="text-sm text-slate-700">Archivo seleccionado: {selectedFile.name}</div>
        ) : (
          <div>
            <div className="font-medium text-slate-700">Arrastra y suelta tu PDF aquí</div>
            <div className="text-sm text-slate-500 mt-1">o haz clic para seleccionar un archivo</div>
          </div>
        )}
      </div>
    </div>
  );
}