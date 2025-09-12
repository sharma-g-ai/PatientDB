import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface DocumentUploadProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onFileUpload, isUploading }) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled: isUploading
  });

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary-500 hover:bg-primary-50'}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <svg
              className="h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          
          {isUploading ? (
            <div>
              <p className="text-gray-600">Processing document...</p>
              <div className="mt-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-gray-600">
                {isDragActive
                  ? 'Drop the document here...'
                  : 'Drag & drop a patient document, or click to select'}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Supports: Images (JPG, PNG), Text files, PDFs
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
