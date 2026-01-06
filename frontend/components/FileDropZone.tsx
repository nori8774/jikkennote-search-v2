'use client';

import { useState, useRef, DragEvent, ChangeEvent } from 'react';

interface FileDropZoneProps {
  onFilesSelected: (files: FileList) => void;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
}

export default function FileDropZone({
  onFilesSelected,
  accept = '.md',
  multiple = true,
  disabled = false,
  loading = false,
  className = '',
}: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dragCounter = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const validateFiles = (files: FileList): boolean => {
    const acceptedExtensions = accept.split(',').map(ext => ext.trim().toLowerCase());

    for (const file of Array.from(files)) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedExtensions.includes(ext)) {
        setError(`${file.name} は無効なファイル形式です。${accept}のみアップロード可能です。`);
        return false;
      }
    }
    setError(null);
    return true;
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    if (disabled || loading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      if (validateFiles(files)) {
        onFilesSelected(files);
      }
    }
  };

  const handleClick = () => {
    if (!disabled && !loading) {
      inputRef.current?.click();
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      if (validateFiles(files)) {
        onFilesSelected(files);
      }
    }
    // リセット（同じファイルを再選択できるように）
    e.target.value = '';
  };

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'}
        ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}
        ${error ? 'border-red-500' : ''}
        ${className}
      `}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleChange}
        disabled={disabled || loading}
        className="hidden"
      />

      {loading ? (
        <div className="flex flex-col items-center gap-2">
          <svg className="animate-spin h-10 w-10 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-gray-600">アップロード中...</span>
        </div>
      ) : isDragging ? (
        <div className="flex flex-col items-center gap-2">
          <span className="text-4xl">📥</span>
          <span className="text-blue-600 font-medium">ここにドロップ</span>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <span className="text-4xl">📁</span>
          <span className="text-gray-700 font-medium">ファイルをドラッグ&ドロップ</span>
          <span className="text-sm text-gray-500">またはクリックして選択</span>
          <span className="text-xs text-gray-400 mt-2">
            {multiple ? '複数ファイル対応 | ' : ''}Markdown ({accept}) のみ
          </span>
        </div>
      )}

      {error && (
        <div className="mt-4 text-red-600 text-sm bg-red-50 px-3 py-2 rounded">
          {error}
        </div>
      )}
    </div>
  );
}
