import React, { useCallback, useState } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, UploadCloud as CloudUpload } from 'lucide-react';
import { ApiService } from '../utils/api';

interface FileUploadProps {
  onUploadComplete: () => void;
  className?: string;
}

interface UploadState {
  file: File | null;
  uploading: boolean;
  success: boolean;
  error: string | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete, className = '' }) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    success: false,
    error: null,
  });
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    const file = files[0];
    
    if (file && (file.type === 'application/pdf' || file.type === 'text/plain')) {
      setUploadState(prev => ({ ...prev, file, error: null }));
    } else {
      setUploadState(prev => ({ 
        ...prev, 
        error: 'Please upload a PDF or TXT file only.' 
      }));
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadState(prev => ({ ...prev, file, error: null }));
    }
  }, []);

  const handleUpload = async () => {
    if (!uploadState.file) return;

    setUploadState(prev => ({ ...prev, uploading: true, error: null }));

    try {
      await ApiService.uploadDocument(uploadState.file);
      setUploadState(prev => ({ 
        ...prev, 
        uploading: false, 
        success: true 
      }));
      onUploadComplete();
      
      // Reset after success
      setTimeout(() => {
        setUploadState({
          file: null,
          uploading: false,
          success: false,
          error: null,
        });
      }, 2000);
    } catch (error) {
      setUploadState(prev => ({ 
        ...prev, 
        uploading: false, 
        error: error instanceof Error ? error.message : 'Upload failed' 
      }));
    }
  };

  const handleRemove = () => {
    setUploadState({
      file: null,
      uploading: false,
      success: false,
      error: null,
    });
  };

  return (
    <div className={`glass rounded-2xl border border-verdant-500/20 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-8 h-8 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-lg flex items-center justify-center">
          <CloudUpload className="h-4 w-4 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-verdant-100">Upload Document</h3>
      </div>
      
      {!uploadState.file ? (
        <div
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 ${
            dragActive
              ? 'border-verdant-400 bg-verdant-500/10 glow-green'
              : 'border-verdant-500/30 hover:border-verdant-400/50 hover:bg-verdant-500/5'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-all duration-300 ${
            dragActive ? 'bg-verdant-500/20 scale-110' : 'bg-verdant-500/10'
          }`}>
            <Upload className={`h-8 w-8 transition-all duration-300 ${
              dragActive ? 'text-verdant-300 rotate-12' : 'text-verdant-400'
            }`} />
          </div>
          <p className="text-lg font-medium text-verdant-100 mb-2">
            Drop your document here
          </p>
          <p className="text-sm text-verdant-300/80 mb-6">
            Supports PDF and TXT files up to 10MB
          </p>
          <label className="inline-flex items-center px-6 py-3 btn-primary rounded-xl font-medium cursor-pointer transition-all duration-300 hover:scale-105">
            <span>Choose File</span>
            <input
              type="file"
              className="hidden"
              accept=".pdf,.txt"
              onChange={handleFileSelect}
            />
          </label>
        </div>
      ) : (
        <div className="space-y-4">
          {/* File Preview */}
          <div className="flex items-center justify-between p-4 glass-light rounded-xl border border-verdant-500/20">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-xl flex items-center justify-center glow-green">
                <File className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="font-medium text-verdant-100">{uploadState.file.name}</p>
                <p className="text-sm text-verdant-300/70">
                  {(uploadState.file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!uploadState.uploading && !uploadState.success && (
              <button
                onClick={handleRemove}
                className="p-2 hover:bg-red-500/10 text-verdant-400/60 hover:text-red-400 rounded-lg transition-all duration-300"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Status Messages */}
          {uploadState.success ? (
            <div className="flex items-center space-x-3 p-4 bg-verdant-500/10 border border-verdant-500/30 rounded-xl">
              <CheckCircle className="h-5 w-5 text-verdant-400" />
              <span className="font-medium text-verdant-100">Upload successful!</span>
            </div>
          ) : uploadState.error ? (
            <div className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <span className="text-sm text-red-300">{uploadState.error}</span>
            </div>
          ) : (
            <button
              onClick={handleUpload}
              disabled={uploadState.uploading}
              className="w-full px-6 py-3 btn-primary rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
            >
              {uploadState.uploading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Processing...</span>
                </div>
              ) : (
                'Upload Document'
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;