import React from 'react';
import { FileText, Trash2, Clock, Hash, Layers, Zap } from 'lucide-react';
import type { Document } from '../types';

interface DocumentSidebarProps {
  documents: Document[];
  selectedDocumentId?: string;
  onSelectDocument: (documentId?: string) => void;
  onDeleteAllDocuments: () => void;
  loading: boolean;
  className?: string;
}

const DocumentSidebar: React.FC<DocumentSidebarProps> = ({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onDeleteAllDocuments,
  loading,
  className = '',
}) => {
  return (
    <div className={`glass rounded-2xl border border-verdant-500/20 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-verdant-500/20 bg-gradient-to-r from-verdant-500/10 to-verdant-600/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-lg flex items-center justify-center">
              <Layers className="h-4 w-4 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-verdant-100">Document Library</h3>
          </div>
          {documents.length > 0 && (
            <button
              onClick={onDeleteAllDocuments}
              className="group p-2 text-verdant-400/60 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-300"
              title="Delete all documents"
            >
              <Trash2 className="h-4 w-4 group-hover:scale-110 transition-transform duration-300" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center space-x-3 p-4 rounded-xl glass-light">
                  <div className="w-10 h-10 bg-verdant-500/20 rounded-lg shimmer"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-verdant-500/20 rounded-lg w-3/4 mb-2 shimmer"></div>
                    <div className="h-3 bg-verdant-500/10 rounded-lg w-1/2 shimmer"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gradient-to-br from-verdant-500/20 to-verdant-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4 float">
              <FileText className="h-8 w-8 text-verdant-400" />
            </div>
            <p className="text-verdant-300/80 text-sm leading-relaxed">
              No documents uploaded yet.<br />
              Upload your first document to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* All Documents Option */}
            <button
              onClick={() => onSelectDocument(undefined)}
              className={`group w-full text-left p-4 rounded-xl transition-all duration-300 ${
                !selectedDocumentId
                  ? 'bg-gradient-to-r from-verdant-500/20 to-verdant-600/20 border border-verdant-500/30 glow-green'
                  : 'glass-light hover:bg-verdant-500/10 border border-verdant-500/10'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${
                  !selectedDocumentId 
                    ? 'bg-gradient-to-br from-verdant-500 to-verdant-600 glow-green' 
                    : 'bg-verdant-500/20 group-hover:bg-verdant-500/30'
                }`}>
                  <Zap className={`h-5 w-5 ${
                    !selectedDocumentId ? 'text-white' : 'text-verdant-400'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`font-semibold truncate transition-colors duration-300 ${
                    !selectedDocumentId ? 'text-verdant-100' : 'text-verdant-200 group-hover:text-verdant-100'
                  }`}>
                    All Documents
                  </p>
                  <p className="text-sm text-verdant-300/70 mt-1">
                    Search across your entire library
                  </p>
                </div>
              </div>
            </button>

            {/* Individual Documents */}
            {documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => onSelectDocument(doc.id)}
                className={`group w-full text-left p-4 rounded-xl transition-all duration-300 ${
                  selectedDocumentId === doc.id
                    ? 'bg-gradient-to-r from-verdant-500/20 to-verdant-600/20 border border-verdant-500/30 glow-green'
                    : 'glass-light hover:bg-verdant-500/10 border border-verdant-500/10'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${
                    selectedDocumentId === doc.id 
                      ? 'bg-gradient-to-br from-verdant-500 to-verdant-600 glow-green' 
                      : 'bg-verdant-500/20 group-hover:bg-verdant-500/30'
                  }`}>
                    <FileText className={`h-5 w-5 ${
                      selectedDocumentId === doc.id ? 'text-white' : 'text-verdant-400'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium truncate transition-colors duration-300 ${
                      selectedDocumentId === doc.id ? 'text-verdant-100' : 'text-verdant-200 group-hover:text-verdant-100'
                    }`} title={doc.filename}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center space-x-4 mt-2">
                      <div className="flex items-center space-x-1 text-xs text-verdant-300/70">
                        <Hash className="h-3 w-3" />
                        <span>{doc.chunk_count} chunks</span>
                      </div>
                      <div className="flex items-center space-x-1 text-xs text-verdant-300/70">
                        <Clock className="h-3 w-3" />
                        <span>{doc.upload_date !== 'Unknown' ? doc.upload_date : 'Recent'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentSidebar;