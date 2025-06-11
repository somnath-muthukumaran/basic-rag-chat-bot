import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, Sparkles } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = "Ask a question about your documents...",
  className = '',
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <form onSubmit={handleSubmit} className={`${className}`}>
      <div className="relative glass-light rounded-2xl border border-verdant-500/20 focus-within:border-verdant-500/40 focus-within:glow-green transition-all duration-300">
        <div className="flex items-start space-x-3 p-4">
          <div className="w-8 h-8 bg-gradient-to-br from-verdant-500/20 to-verdant-600/20 rounded-lg flex items-center justify-center mt-1">
            <Sparkles className="h-4 w-4 text-verdant-400" />
          </div>
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 bg-transparent border-0 resize-none focus:ring-0 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed max-h-32 text-verdant-100 placeholder-verdant-300/50"
            rows={1}
          />
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className="w-10 h-10 bg-gradient-to-br from-verdant-500 to-verdant-600 text-white rounded-xl hover:from-verdant-600 hover:to-verdant-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105 disabled:hover:scale-100 glow-green flex items-center justify-center mt-1"
          >
            {disabled ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default MessageInput;