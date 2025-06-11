import React, { useState, useEffect } from 'react';
import { Brain, Upload, Zap, Activity } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import DocumentSidebar from './components/DocumentSidebar';
import FileUpload from './components/FileUpload';
import StatusIndicator from './components/StatusIndicator';
import { ApiService } from './utils/api';
import type { Document, HealthStatus, ProcessingStatus } from './types';

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [processing, setProcessing] = useState<ProcessingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  // Fetch health status
  const fetchHealth = async () => {
    try {
      const healthData = await ApiService.checkHealth();
      setHealth(healthData);
    } catch (error) {
      console.error('Failed to fetch health:', error);
      setHealth({
        status: 'offline',
        message: 'Backend server is not available',
        timestamp: new Date().toISOString()
      });
    }
  };

  // Fetch documents
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const docs = await ApiService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch processing status
  const fetchProcessingStatus = async () => {
    try {
      const status = await ApiService.getProcessingStatus();
      setProcessing(status);
    } catch (error) {
      console.error('Failed to fetch processing status:', error);
      setProcessing({
        is_processing: false,
        current_document: null,
        queue_size: 0,
        message: 'Backend server is not available'
      });
    }
  };

  // Handle document deletion
  const handleDeleteAllDocuments = async () => {
    if (!confirm('Are you sure you want to delete all documents? This action cannot be undone.')) {
      return;
    }

    try {
      await ApiService.deleteAllDocuments();
      setDocuments([]);
      setSelectedDocumentId(undefined);
    } catch (error) {
      console.error('Failed to delete documents:', error);
      alert('Failed to delete documents. Please try again.');
    }
  };

  // Handle upload completion
  const handleUploadComplete = () => {
    fetchDocuments();
    setShowUpload(false);
  };

  // Initial data fetch
  useEffect(() => {
    fetchHealth();
    fetchDocuments();
    fetchProcessingStatus();

    // Set up polling for health and processing status
    const healthInterval = setInterval(fetchHealth, 30000); // Every 30 seconds
    const processingInterval = setInterval(fetchProcessingStatus, 2000); // Every 2 seconds

    return () => {
      clearInterval(healthInterval);
      clearInterval(processingInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-verdant-500/10 rounded-full blur-3xl animate-pulse-green"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-verdant-400/10 rounded-full blur-3xl animate-pulse-green" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-verdant-600/5 rounded-full blur-3xl animate-float"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 glass border-b border-verdant-500/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-xl flex items-center justify-center glow-green">
                  <Brain className="h-7 w-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-verdant-400 rounded-full animate-pulse-green"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">VerdantMind</h1>
                <p className="text-sm text-verdant-300/80">AI Document Intelligence</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="group flex items-center space-x-2 px-6 py-3 btn-primary rounded-xl font-medium transition-all duration-300 hover:scale-105"
              >
                <Upload className="h-5 w-5 group-hover:rotate-12 transition-transform duration-300" />
                <span>Upload Document</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Status Bar */}
      <div className="relative z-10 glass-light border-b border-verdant-500/10">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <StatusIndicator health={health} processing={processing} />
        </div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-220px)]">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Upload Section */}
            {showUpload && (
              <div className="transform transition-all duration-500 ease-out">
                <FileUpload
                  onUploadComplete={handleUploadComplete}
                  className="lg:sticky lg:top-0"
                />
              </div>
            )}
            
            {/* Document List */}
            <div className="transform transition-all duration-500 ease-out">
              <DocumentSidebar
                documents={documents}
                selectedDocumentId={selectedDocumentId}
                onSelectDocument={setSelectedDocumentId}
                onDeleteAllDocuments={handleDeleteAllDocuments}
                loading={loading}
                className={`${showUpload ? '' : 'lg:sticky lg:top-0'}`}
              />
            </div>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="transform transition-all duration-500 ease-out">
              <ChatInterface
                selectedDocumentId={selectedDocumentId}
                className="h-full"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;