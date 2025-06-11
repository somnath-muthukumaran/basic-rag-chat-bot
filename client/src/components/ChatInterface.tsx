import React, { useState, useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { ApiService } from '../utils/api';
import { processThinkingText } from '../utils/textFilters';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import type { Message, QueryResponse } from '../types';

interface ChatInterfaceProps {
  selectedDocumentId?: string;
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  selectedDocumentId,
  className = '',
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages(prev => [...prev, assistantMessage]);

      let fullAnswer = '';
      let references: any[] = [];
      let hasStartedStreaming = false;

      for await (const chunk of ApiService.queryStream(content, selectedDocumentId)) {
        if (!hasStartedStreaming) {
          hasStartedStreaming = true;
        }
        
        // Process thinking tags and get appropriate display content
        const processed = processThinkingText(chunk.answer);
        fullAnswer = processed.displayText;
        
        if (chunk.references) {
          references = chunk.references;
        }

        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content: fullAnswer,
                references: chunk.done ? references : undefined,
                isStreaming: !chunk.done || processed.isThinking,
              }
            : msg
        ));

        if (chunk.done && !processed.isThinking) {
          break;
        }
        
        // Add a small delay to make streaming more visible
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an issue while processing your question. Please ensure the backend server is running and try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [
        ...prev.slice(0, -1), // Remove the streaming message
        errorMessage,
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col h-full glass rounded-2xl border border-verdant-500/20 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-verdant-500/20 bg-gradient-to-r from-verdant-500/10 to-verdant-600/10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-verdant-500 to-verdant-600 rounded-xl flex items-center justify-center glow-green">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-verdant-100">
              Intelligent Document Chat
            </h2>
            {selectedDocumentId ? (
              <p className="text-sm text-verdant-300/80 mt-1">
                Focused on selected document
              </p>
            ) : (
              <p className="text-sm text-verdant-300/80 mt-1">
                Searching across all documents
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center py-16">
            <div className="max-w-md mx-auto">
              <div className="w-20 h-20 bg-gradient-to-br from-verdant-500/20 to-verdant-600/20 rounded-2xl flex items-center justify-center mx-auto mb-6 float">
                <Sparkles className="h-10 w-10 text-verdant-400" />
              </div>
              <h3 className="text-2xl font-semibold text-verdant-100 mb-3 gradient-text">
                Start Your Conversation
              </h3>
              <p className="text-verdant-300/80 leading-relaxed">
                Upload documents and ask questions to unlock intelligent insights. 
                I'll analyze your content and provide detailed, contextual answers.
              </p>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 border-t border-verdant-500/20 bg-gradient-to-r from-verdant-500/5 to-verdant-600/5">
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder={
            selectedDocumentId
              ? "Ask about the selected document..."
              : "Ask a question about your documents..."
          }
        />
      </div>
    </div>
  );
};

export default ChatInterface;