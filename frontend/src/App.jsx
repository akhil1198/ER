// App.js - React Chat Interface
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Initialize chat session
  useEffect(() => {
    initializeChat();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeChat = async () => {
    try {
      // Create new chat session
      const response = await fetch(`${API_BASE_URL}/api/chat/create-session`, {
        method: 'POST'
      });
      const data = await response.json();
      const newSessionId = data.session_id;
      setSessionId(newSessionId);

      // Load initial messages
      await loadMessages(newSessionId);

      // Connect WebSocket
      connectWebSocket(newSessionId);
    } catch (error) {
      console.error('Failed to initialize chat:', error);
    }
  };

  const connectWebSocket = (sessionId) => {
    wsRef.current = new WebSocket(`${WS_BASE_URL}/ws/chat/${sessionId}`);
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  };

  const loadMessages = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/${sessionId}/messages`);
      const data = await response.json();
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    try {
      await fetch(`${API_BASE_URL}/api/chat/${sessionId}/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: inputMessage }),
      });
      setInputMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file || !sessionId) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      await fetch(`${API_BASE_URL}/api/chat/${sessionId}/upload-receipt`, {
        method: 'POST',
        body: formData,
      });
    } catch (error) {
      console.error('Failed to upload file:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragEvents = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0] && files[0].type.startsWith('image/')) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatFieldName = (fieldName) => {
    return fieldName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatFieldValue = (value) => {
    if (value === null || value === undefined) return 'Not specified';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'number') return value.toLocaleString();
    return value;
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user' || message.type === 'image';
    
    return (
      <div key={message.id} className={`message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-content">
          {message.type === 'image' && message.image_url && (
            <div className="image-message">
              <img src={message.image_url} alt="Receipt" className="receipt-image" />
              <p>{message.content}</p>
            </div>
          )}
          
          {message.type === 'expense_data' && message.expense_data && (
            <div className="expense-data-message">
              <p className="expense-intro">{message.content}</p>
              <div className="expense-data-card">
                <h4>💰 Extracted Expense Information</h4>
                <div className="expense-fields">
                  {Object.entries(message.expense_data).map(([key, value]) => (
                    <div key={key} className="expense-field">
                      <span className="field-label">{formatFieldName(key)}:</span>
                      <span className={`field-value ${value ? 'has-value' : 'no-value'}`}>
                        {formatFieldValue(value)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="expense-actions">
                  <button className="action-btn secondary">Make Changes</button>
                  <button className="action-btn primary">Create Expense Report</button>
                </div>
              </div>
            </div>
          )}
          
          {(message.type === 'user' || message.type === 'assistant') && message.type !== 'image' && (
            <p>{message.content}</p>
          )}
          
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  if (!sessionId) {
    return (
      <div className="App loading-app">
        <div className="loading-spinner"></div>
        <p>Initializing chat...</p>
      </div>
    );
  }

  return (
    <div 
      className={`App chat-app ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDragEvents}
      onDragLeave={handleDragEvents}
      onDragOver={handleDragEvents}
      onDrop={handleDrop}
    >
      {/* Header */}
      <header className="chat-header">
        <div className="header-content">
          <h1>💬 Expense Chat Assistant</h1>
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="chat-container">
        <div className="messages-container">
          {messages.map(renderMessage)}
          {isUploading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>Processing your receipt...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Drop Zone Overlay */}
        {dragActive && (
          <div className="drop-overlay">
            <div className="drop-content">
              <div className="drop-icon">📎</div>
              <h3>Drop your receipt here</h3>
              <p>Release to upload and extract expense data</p>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        <div className="input-row">
          <button 
            className="attach-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            📎
          </button>
          
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message... or drag & drop a receipt image"
            className="message-input"
            rows="1"
            disabled={isUploading}
          />
          
          <button 
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isUploading}
            className="send-btn"
          >
            📤
          </button>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        <div className="input-hint">
          💡 Upload a receipt image or type corrections like "Change the vendor to Starbucks" or "The amount should be $25.50"
        </div>
      </div>
    </div>
  );
}

export default App;