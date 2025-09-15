import React, { useState, useRef, useEffect } from 'react';
import { chatApi } from '../services/api';
import { ChatResponse } from '../types';

interface ChatInterfaceProps {
  className?: string;
}

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: string[];
  patientIds?: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to Healthix! 👋 I\'m your intelligent patient data assistant powered by Gemini AI. I have direct access to all your patient records and can answer questions like:\n\n• "Show me all patients with diabetes"\n• "What medications has John Smith been prescribed?"\n• "How many patients do we have with hypertension?"\n• "List all patients born before 1980"\n\nI can analyze patterns, provide statistics, and help you find specific patient information instantly!',
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await chatApi.sendMessage({ message: inputValue.trim() });
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        isUser: false,
        timestamp: new Date(),
        sources: response.sources,
        patientIds: response.patient_ids,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={`card-glow animate-fade-in ${className}`}>
      <div className="border-b border-healthix-dark-lighter p-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-healthix-green/20 rounded-lg">
            <svg className="w-6 h-6 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Patient Data Chat</h2>
        </div>
        <p className="text-healthix-gray-light">Direct AI access to all patient data - No setup required!</p>
      </div>

      <div className="h-96 overflow-y-auto p-6 space-y-4 bg-healthix-dark/30">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105 ${
                message.isUser
                  ? 'bg-gradient-to-r from-healthix-green to-healthix-green-light text-white shadow-glow'
                  : 'bg-healthix-dark-light border border-healthix-dark-lighter text-white'
              }`}
            >
              <p className="text-sm leading-relaxed">{message.text}</p>
              
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-healthix-dark-lighter/50">
                  <p className="text-xs text-healthix-green font-medium">Sources:</p>
                  <ul className="text-xs text-healthix-gray-light mt-1 space-y-1">
                    {message.sources.map((source, index) => (
                      <li key={index} className="flex items-center">
                        <svg className="w-2 h-2 mr-2 text-healthix-green" fill="currentColor" viewBox="0 0 8 8">
                          <circle cx="4" cy="4" r="3" />
                        </svg>
                        {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <p className="text-xs mt-3 opacity-70 text-right">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-healthix-dark-light border border-healthix-dark-lighter px-4 py-3 rounded-xl">
              <div className="flex items-center space-x-3">
                <div className="loading-spinner h-4 w-4"></div>
                <p className="text-sm text-healthix-gray-light">AI is thinking...</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-healthix-dark-lighter p-6 bg-healthix-dark-light/50">
        <div className="flex space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about patient data..."
            className="input-modern flex-1"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="btn-primary"
          >
            {isLoading ? (
              <div className="loading-spinner h-4 w-4"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
