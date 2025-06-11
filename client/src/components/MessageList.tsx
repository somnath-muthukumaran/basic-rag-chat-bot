import React from 'react';
import { User, Bot, FileText, Hash, Sparkles } from 'lucide-react';
import type { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  className?: string;
}

const MessageList: React.FC<MessageListProps> = ({ messages, className = '' }) => {
  return (
    <div className={`space-y-6 ${className}`}>
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex space-x-4 ${
            message.type === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.type === 'assistant' && (
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-xl flex items-center justify-center glow-green">
                <Bot className="h-5 w-5 text-white" />
              </div>
            </div>
          )}
          
          <div
            className={`max-w-3xl ${
              message.type === 'user' ? 'order-1' : 'order-2'
            }`}
          >
            <div
              className={`px-6 py-4 rounded-2xl transition-all duration-300 ${
                message.type === 'user'
                  ? 'message-user text-white'
                  : 'message-assistant text-verdant-100'
              } ${message.isStreaming ? 'animate-pulse' : ''}`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">
                {message.content}
              </p>
            </div>
            
            {/* References */}
            {message.references && message.references.length > 0 && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-4 w-4 text-verdant-400" />
                  <p className="text-sm font-medium text-verdant-300">Sources:</p>
                </div>
                {message.references.map((ref, index) => (
                  <div
                    key={index}
                    className="glass-light border border-verdant-500/20 rounded-xl p-4 text-sm transition-all duration-300 hover:border-verdant-500/30"
                  >
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-verdant-500/20 to-verdant-600/20 rounded-lg flex items-center justify-center">
                        <FileText className="h-4 w-4 text-verdant-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 text-xs text-verdant-300/80">
                          <span className="font-medium">Page {ref.page}</span>
                          <span className="text-verdant-500">•</span>
                          <span>Lines {ref.start_line}-{ref.end_line}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Hash className="h-3 w-3 text-verdant-400/60" />
                        <span className="text-xs text-verdant-400 font-medium">
                          {Math.round(ref.similarity_score * 100)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-verdant-200/90 italic leading-relaxed line-clamp-3 pl-11">
                      "{ref.content}"
                    </p>
                  </div>
                ))}
              </div>
            )}
            
            <p className="text-xs text-verdant-400/60 mt-3 flex items-center space-x-2">
              <span>{message.timestamp.toLocaleTimeString()}</span>
            </p>
          </div>
          
          {message.type === 'user' && (
            <div className="flex-shrink-0 order-2">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl flex items-center justify-center border border-verdant-500/20">
                <User className="h-5 w-5 text-verdant-200" />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default MessageList;