import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertCircle, TrendingUp, Zap, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  data?: any;
  suggestions?: string[];
}

interface ChatResponse {
  response: string;
  data?: any;
  suggestions?: string[];
}

const API_BASE = 'http://10.10.4.15:8000';

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! Where are you writing in from today, AMER or EMEA?',
      isUser: false,
      timestamp: new Date(),
      suggestions: [
        'AMER',
        'EMEA'
      ]
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

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: content.trim(),
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post<ChatResponse>(`${API_BASE}/chat`, {
        message: content.trim(),
        timestamp: new Date().toISOString()
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        isUser: false,
        timestamp: new Date(),
        data: response.data.data,
        suggestions: response.data.suggestions
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please make sure the backend server is running.',
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const getStatusIcon = (severity: string) => {
    switch (severity) {
      case 'high':
      case 'CRITICAL':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'medium':
      case 'WARNING':
        return <TrendingUp className="w-4 h-4 text-yellow-500" />;
      default:
        return <Zap className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-orange-500 border-b border-orange-600 px-6 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
            <span className="text-2xl">🌮</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">Taco 'Bout Errors 🌮</h1>
            <p className="text-sm text-orange-100">Real-time monitoring analysis and correlation</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-3 ${message.isUser ? 'justify-end' : 'justify-start'}`}>
            {!message.isUser && (
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            
            <div className={`max-w-3xl ${message.isUser ? 'order-1' : ''}`}>
              <div className={`rounded-lg px-4 py-3 ${
                message.isUser 
                  ? 'bg-blue-600 text-white ml-auto' 
                  : 'bg-white border border-gray-200 shadow-sm'
              }`}>
                <div className={`text-sm ${message.isUser ? 'text-white' : 'text-gray-900'}`}>
                  <ReactMarkdown 
                    className="prose prose-sm max-w-none"
                    components={{
                      h2: ({children}) => <h2 className="text-lg font-semibold mb-2 mt-3 first:mt-0">{children}</h2>,
                      h3: ({children}) => <h3 className="text-md font-medium mb-1 mt-2">{children}</h3>,
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                      code: ({children}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{children}</code>,
                      a: ({href, children}) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">{children}</a>
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
                
                <div className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                  <Clock className="w-3 h-3 inline mr-1" />
                  {formatDistanceToNow(message.timestamp, { addSuffix: true })}
                </div>
              </div>
              
              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full border transition-colors"
                      disabled={isLoading}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              {/* Data visualization */}
              {message.data && (
                <div className="mt-3 bg-gray-50 rounded-lg p-3 border">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                    {message.data.deployments && message.data.deployments.length > 0 && (
                      <div className="bg-white rounded p-2">
                        <div className="font-medium text-gray-700 mb-1">Deployments</div>
                        <div className="text-2xl font-bold text-blue-600">{message.data.deployments.length}</div>
                      </div>
                    )}
                    
                    {message.data.alerts && message.data.alerts.length > 0 && (
                      <div className="bg-white rounded p-2">
                        <div className="font-medium text-gray-700 mb-1">Active Alerts</div>
                        <div className="text-2xl font-bold text-red-600">{message.data.alerts.length}</div>
                      </div>
                    )}
                    
                    {message.data.anomalies && message.data.anomalies.length > 0 && (
                      <div className="bg-white rounded p-2">
                        <div className="font-medium text-gray-700 mb-1">Anomalies</div>
                        <div className="text-2xl font-bold text-yellow-600">{message.data.anomalies.length}</div>
                      </div>
                    )}
                    
                    {message.data.errors && message.data.errors.length > 0 && (
                      <div className="bg-white rounded p-2">
                        <div className="font-medium text-gray-700 mb-1">Error Types</div>
                        <div className="text-2xl font-bold text-orange-600">{message.data.errors.length}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            {message.isUser && (
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                Analyzing monitoring data...
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about recent changes, errors, or system health..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;