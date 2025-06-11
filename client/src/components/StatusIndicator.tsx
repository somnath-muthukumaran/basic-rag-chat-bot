import React from 'react';
import { Circle, Wifi, WifiOff, Activity, Zap, AlertTriangle } from 'lucide-react';
import type { HealthStatus, ProcessingStatus } from '../types';

interface StatusIndicatorProps {
  health?: HealthStatus | null;
  processing?: ProcessingStatus | null;
  className?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  health, 
  processing, 
  className = '' 
}) => {
  const getHealthStatus = () => {
    if (!health) {
      return (
        <div className="flex items-center space-x-2 text-verdant-400/60">
          <Circle className="h-4 w-4 animate-pulse" />
          <span className="text-sm font-medium">Checking status...</span>
        </div>
      );
    }

    if (health.status === 'offline') {
      return (
        <div className="flex items-center space-x-2 text-red-400">
          <WifiOff className="h-4 w-4" />
          <span className="text-sm font-medium">Backend Offline</span>
        </div>
      );
    }

    if (health.status === 'healthy') {
      return (
        <div className="flex items-center space-x-2 text-verdant-400">
          <div className="w-4 h-4 bg-verdant-500 rounded-full animate-pulse-green"></div>
          <span className="text-sm font-medium">System Online</span>
        </div>
      );
    }

    return (
      <div className="flex items-center space-x-2 text-yellow-400">
        <AlertTriangle className="h-4 w-4" />
        <span className="text-sm font-medium">System Degraded</span>
      </div>
    );
  };

  const getProcessingStatus = () => {
    if (!processing) return null;
    
    if (processing.status === 'processing') {
      return (
        <div className="flex items-center space-x-2 text-verdant-400">
          <Activity className="h-4 w-4 animate-pulse" />
          <span className="text-sm font-medium">
            Processing {processing.current_document} ({Math.round(processing.progress)}%)
          </span>
        </div>
      );
    }

    if (processing.status === 'error') {
      return (
        <div className="flex items-center space-x-2 text-red-400">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm font-medium">Processing Error</span>
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="flex items-center space-x-6">
        {/* Health Status */}
        {getHealthStatus()}

        {/* Processing Status */}
        {getProcessingStatus()}
      </div>

      {/* Service Status Details */}
      {health && health.status !== 'offline' && (
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <Circle 
                className={`h-2 w-2 fill-current ${
                  health.ollama_status ? 'text-verdant-500' : 'text-red-500'
                }`} 
              />
              <span className="text-verdant-300/70">Ollama</span>
            </div>
            <div className="flex items-center space-x-1">
              <Circle 
                className={`h-2 w-2 fill-current ${
                  health.weaviate_status ? 'text-verdant-500' : 'text-red-500'
                }`} 
              />
              <span className="text-verdant-300/70">Weaviate</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;