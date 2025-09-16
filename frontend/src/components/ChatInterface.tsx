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
  matchedPatients?: any[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Welcome to Healthix! 👋 I\'m your intelligent patient data assistant. You can ask me questions about your patient records, such as "Show me patients with diabetes" or "What medications has John Smith been prescribed?"',
      isUser: false,
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
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
      let response: ChatResponse;
      // Always use simple endpoint to bypass any RAG
      response = await chatApi.sendMessageWithFiles(inputValue.trim(), attachedFiles);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        isUser: false,
        timestamp: new Date(),
        sources: response.sources,
        patientIds: response.patient_ids,
        matchedPatients: (response as any).matched_patients || [],
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
      setAttachedFiles([]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (!files.length) return;
    // Validate limits
    const maxPerFile = 20 * 1024 * 1024; // 20MB
    const maxFiles = 5;
    const accepted: File[] = [];
    for (const f of files) {
      if (f.size <= maxPerFile) accepted.push(f);
    }
    const combined = [...attachedFiles, ...accepted].slice(0, maxFiles);
    setAttachedFiles(combined);
    // reset input value so same file can be reselected
    e.currentTarget.value = '';
  };

  const removeFile = (idx: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className={`card-glow animate-fade-in ${className} flex flex-col h-full`}> 
      <div className="border-b border-healthix-dark-lighter p-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-healthix-green/20 rounded-lg">
            <svg className="w-6 h-6 text-healthix-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Patient Data Chat</h2>
        </div>
        <p className="text-healthix-gray-light">Ask questions about your patient records</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-healthix-dark/30">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
          >
            <div
              className={`max-w-3xl px-4 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105 ${
                message.isUser
                  ? 'bg-gradient-to-r from-healthix-green to-healthix-green-light text-white shadow-glow'
                  : 'bg-healthix-dark-light border border-healthix-dark-lighter text-white'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
              
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

              {/* Matched patients cards */}
              {Array.isArray(message.matchedPatients) && message.matchedPatients.length > 0 && (
                <div className="mt-3 grid grid-cols-1 gap-2">
                  {message.matchedPatients.map((p: any, idx: number) => (
                    <div key={idx} className="p-3 bg-healthix-dark border border-healthix-dark-lighter rounded">
                      <div className="text-sm font-semibold text-white">{p.name}</div>
                      <div className="text-xs text-healthix-gray-light">DOB: {p.date_of_birth}</div>
                      <div className="text-xs text-healthix-gray-light">Diagnosis: {p.diagnosis || '-'}</div>
                      <div className="text-xs text-healthix-gray-light">Prescription: {p.prescription || '-'}</div>
                      <div className="text-[10px] text-healthix-gray-light/80 mt-1">ID: {p.id}</div>
                    </div>
                  ))}
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
        {/* Attached files preview */}
        {attachedFiles.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachedFiles.map((f, i) => (
              <div key={i} className="px-2 py-1 bg-healthix-dark-lighter text-xs text-white rounded flex items-center space-x-2">
                <span className="max-w-[200px] truncate">{f.name}</span>
                <button onClick={() => removeFile(i)} className="text-healthix-green hover:opacity-80">✕</button>
              </div>
            ))}
          </div>
        )}

        <div className="flex space-x-3 items-end">
          <label className="btn-secondary cursor-pointer">
            <input type="file" className="hidden" multiple onChange={handleFileChange} accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg,.csv" />
            Attach
          </label>
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
