'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { API_ENDPOINTS } from '@/config/api';
import { auth } from '@/lib/auth';
import { Send, Bot, User, Mic, MicOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';

type ButtonOption = {
  label: string;
  value: string;
};

type Message = {
  sender: 'user' | 'bot';
  text?: string;
  buttons?: ButtonOption[];
};

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  
  // Search Suggestions State
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Speech Recognition
  const {
    transcript,
    isListening,
    isSupported: isSpeechSupported,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechRecognition();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const isMountedRef = useRef(false);
  const streamingMessageIndexRef = useRef<number>(-1);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ---------------- SESSION MANAGEMENT ---------------- */
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  // Volatile session ID - generates new one on every mount
  const [sessionId] = useState(() => generateUUID());
  
  // Log session ID once on mount
  useEffect(() => {
    if (sessionId) console.log('📋 Chat Session ID:', sessionId);
  }, [sessionId]);

  /* ---------------- LOAD INITIAL FAQ BUTTONS ---------------- */
  useEffect(() => {
    // Only load if messages are empty
    if (messages.length > 0 || !sessionId) return;
    
    const loadFAQ = async () => {
      try {
        console.log('🔄 Loading FAQ buttons from:', `${API_ENDPOINTS.CHAT_TREE_START}?session_id=${sessionId}`);
        
        const response = await fetch(`${API_ENDPOINTS.CHAT_TREE_START}?session_id=${sessionId}`, {
          headers: auth.getAuthHeaders(),
        });
        
        console.log('📡 FAQ Response status:', response.status, response.statusText);
        
        if (!response.ok) {
          console.error('❌ Failed to load FAQ buttons:', response.status, response.statusText);
          return;
        }

        const data = await response.json();
        console.log('📦 FAQ Data received:', data);
        
        if (data.buttons && data.buttons.length > 0) {
          console.log('✅ Setting FAQ buttons:', data.buttons.length, 'buttons');
          setMessages([{
            sender: 'bot',
            text: data.text || 'Welcome! How can I help you today?',
            buttons: data.buttons
          }]);
        } else {
          console.log('⚠️ No buttons in response');
        }
      } catch (error) {
        console.error('❌ Error loading FAQ buttons:', error);
      }
    };

    loadFAQ();
  }, [sessionId]);

  /* ---------------- WEBSOCKET CONNECTION ---------------- */
  useEffect(() => {
    if (!sessionId) return;
    
    isMountedRef.current = true;
    
    // Note: In development, React Strict Mode intentionally mounts→unmounts→remounts components
    // This causes an initial connection attempt to be closed, followed by a successful reconnection
    // This is EXPECTED behavior and does not indicate a problem
    
    // Dynamically derive WebSocket URL from API Base URL
    // e.g. http://localhost:8000 -> ws://localhost:8000
    // e.g. https://api.example.com -> wss://api.example.com
    
    let wsUrl = '';
    try {
        const apiUrl = new URL(API_ENDPOINTS.BASE_URL);
        const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        // Construct WS URL: protocol // host / path
        // Note: apiUrl.host includes port if present
        const token = auth.getToken();
        wsUrl = `${protocol}//${apiUrl.host}/chat/ws/${sessionId}?token=${token}`;
    } catch (e) {
        // Fallback if URL parsing fails
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const token = auth.getToken();
        wsUrl = `${protocol}//localhost:8000/chat/ws/${sessionId}?token=${token}`;
        console.error("Failed to parse API_URL for WebSocket, using fallback:", e);
    }
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      if (!isMountedRef.current) {
        // Silent cleanup during React Strict Mode
        ws.close();
        return;
      }
      console.log('✅ Connected to Chat WebSocket');
      setSocket(ws);
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      if (!isMountedRef.current) return;
      
      const data = event.data;
      
      // Ignore connection confirmation message
      if (data === "CONNECTED") {
        console.log('✅ Connection confirmed by server');
        return;
      }
      
      console.log('📩 Received:', data);

      if (data === "Analyzing documents..." || data === "Thinking...") {
          setLoading(true);
          setCurrentResponse('');
          streamingMessageIndexRef.current = -1;
      } else {
          setLoading(false);
          
          let parsedData = null;
          try {
             // Try to parse as JSON (e.g. for buttons)
             if (typeof data === 'string' && data.trim().startsWith('{')) {
                 parsedData = JSON.parse(data);
             }
          } catch (e) {
             // Not JSON, assume streaming text
          }

          if (parsedData && parsedData.type === 'buttons') {
              // Handle structured button response
              setMessages(msgs => {
                  return [...msgs, { 
                      sender: 'bot', 
                      text: parsedData.text,
                      buttons: parsedData.buttons 
                  }];
              });
              // We don't update streaming text for buttons, treat as complete message
          } else if (parsedData && parsedData.type === 'text') {
             // Handle simple text structured response
              const text = parsedData.text;
              
              setMessages(msgs => {
                  // If we are already streaming a message, append/replace?
                  // Actually if it sends {"type": "text"}, it's likely a complete message or a chunk.
                  // For now, let's treat it as a new full message if we aren't streaming, 
                  // or append if we are.
                  // BUT the backend sends "Thinking..." first which resets index.
                  
                  if (streamingMessageIndexRef.current === -1) {
                        streamingMessageIndexRef.current = msgs.length;
                        return [...msgs, { sender: 'bot', text: text }];
                  } else {
                       // Append or Replace? 
                       // If it is a full "text" type, it might be the whole answer.
                       // Let's assume it replaces/sets the content.
                       const updated = [...msgs];
                       updated[streamingMessageIndexRef.current] = {
                           ...updated[streamingMessageIndexRef.current],
                           text: text
                       };
                       return updated;
                  }
              });
          } else {
              // Assume streaming text chunk
              setCurrentResponse(prev => {
                  const newText = prev + data;
                  
                  // Update the message directly without causing infinite loop
                  setMessages(msgs => {
                      if (streamingMessageIndexRef.current === -1) {
                          // Create new bot message
                          streamingMessageIndexRef.current = msgs.length;
                          return [...msgs, { sender: 'bot', text: newText }];
                      } else {
                          // Update existing bot message
                          const updated = [...msgs];
                          updated[streamingMessageIndexRef.current] = {
                              ...updated[streamingMessageIndexRef.current],
                              text: newText
                          };
                          return updated;
                      }
                  });
                  
                  return newText;
              });
          }
      }
    };

    ws.onclose = (event) => {
      if (isMountedRef.current) {
        setSocket(null);
        setIsConnected(false);
      }
    };

    ws.onerror = () => {
      // Silently handle errors - they're expected during React Strict Mode double-mounting in dev
      if (isMountedRef.current) {
        setIsConnected(false);
      }
    };

    return () => {
      // Cleanup - close WebSocket when component unmounts
      isMountedRef.current = false;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [sessionId]);


  /* ---------------- SEARCH SUGGESTIONS ---------------- */
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      // Only search if input has meaningful content (at least 2 chars)
      if (input.trim().length > 1) {
        try {
          const response = await fetch(`${API_ENDPOINTS.BASE_URL}/chat/suggestions?query=${encodeURIComponent(input)}`, {
             headers: auth.getAuthHeaders()
          });
          if (response.ok) {
            const data = await response.json();
            // Only show if we have results and the input hasn't been cleared/sent
            if (data.length > 0 && input.trim()) {
              setSuggestions(data);
              setShowSuggestions(true);
            } else {
              setShowSuggestions(false);
            }
          }
        } catch (error) {
          console.error("Error fetching suggestions:", error);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(delayDebounceFn);
  }, [input]);

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
    setShowSuggestions(false);
  };

  /* ---------------- SPEECH RECOGNITION ---------------- */
  // Update input when speech transcript changes
  useEffect(() => {
    if (transcript) {
      setInput(prev => prev + transcript);
      resetTranscript();
    }
  }, [transcript, resetTranscript]);

  // Handle mic button click
  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
      setShowSuggestions(false); // Hide suggestions when using voice
    }
  };

  // Show speech error as toast/notification (optional)
  useEffect(() => {
    if (speechError) {
      console.error('Speech recognition error:', speechError);
    }
  }, [speechError]);


  const sendMessage = async (textOverride?: string) => {
    const textToSend = textOverride || input;
    
    if (!textToSend.trim() || !socket || socket.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send message: socket not ready', socket?.readyState);
      return;
    }

    setInput('');
    setSuggestions([]);
    setShowSuggestions(false);
    
    setCurrentResponse(''); // Reset stream buffer
    streamingMessageIndexRef.current = -1; // Reset streaming index
    
    // Add User Message
    setMessages(prev => [...prev, { sender: 'user', text: textToSend }]);
    
    // Send via WebSocket
    socket.send(textToSend);
  };

  /* ---------------- BUTTON HANDLING ---------------- */
  const handleButtonClick = async (value: string) => {
    console.log('🔘 Button clicked:', value);
    
    // Add user message first
    setMessages(prev => [...prev, { sender: 'user', text: value }]);
    setLoading(true);
    
    try {
      // Call tree/next endpoint
      const response = await fetch(API_ENDPOINTS.CHAT_TREE_NEXT, {
        method: 'POST',
        headers: auth.getAuthHeaders(),
        body: JSON.stringify({
          value: value,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get next tree node: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('📦 Tree response:', data);
      
      // Add bot response
      if (data.type === 'buttons' && data.buttons) {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: data.text,
          buttons: data.buttons
        }]);
      } else {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: data.text
        }]);
      }
    } catch (error) {
      console.error('❌ Error handling button click:', error);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Sorry, something went wrong.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  /* ---------------- UI ---------------- */

  return (
    <div className="flex h-full flex-col rounded-2xl bg-white shadow-xl border border-gray-100 overflow-hidden">
      {/* HEADER */}
      <div className="bg-white/80 backdrop-blur-md px-6 py-4 border-b border-gray-100 flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          <Bot size={20} />
        </div>
        <div>
          <h2 className="font-semibold text-gray-900">AI Assistant</h2>
          <p className={`text-xs flex items-center gap-1 ${isConnected ? 'text-green-500' : 'text-orange-500'}`}>
            <span className="relative flex h-2 w-2">
              {isConnected ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
              )}
            </span>
            {isConnected ? 'Online' : 'Connecting...'}
          </p>
        </div>
      </div>

      {/* MESSAGES */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-[80%] items-end gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.sender === 'user'
                    ? 'bg-primary text-white'
                    : 'bg-white border border-gray-100 text-primary shadow-sm'
                  }`}>
                  {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                {/* Bubble */}
                <div
                  className={`relative rounded-2xl px-5 py-3 text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
                      ? 'bg-primary text-white rounded-br-sm'
                      : 'bg-white text-gray-800 border border-gray-100 rounded-bl-sm'
                    }`}
                >
                  {msg.text && (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
                          em: ({node, ...props}) => <em className="italic" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                          li: ({node, ...props}) => <li className="mb-1" {...props} />,
                          code: ({node, inline, ...props}: any) => 
                            inline 
                              ? <code className="bg-gray-100 px-1 py-0.5 rounded text-xs" {...props} />
                              : <code className="block bg-gray-100 p-2 rounded my-2 text-xs" {...props} />
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  )}

                  {/* Buttons */}
                  {msg.buttons && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {msg.buttons.map((btn, i) => (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          key={i}
                          onClick={() => handleButtonClick(btn.value)}
                          className="rounded-lg bg-gray-50 border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-primary hover:text-white hover:border-primary"
                        >
                          {btn.label}
                        </motion.button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && !currentResponse && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start items-center gap-2 pl-10"
          >
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"></span>
              <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-100"></span>
              <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce delay-200"></span>
            </div>
            <span className="text-xs text-gray-400">Processing...</span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <div className="border-t border-gray-100 bg-white p-4 relative">
        <div className="relative">
          {/* Suggestions Popup */}
          <AnimatePresence>
            {showSuggestions && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute bottom-full left-0 w-full mb-4 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden z-20"
              >
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Suggestions
                </div>
                <div className="max-h-60 overflow-y-auto p-2 space-y-1">
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-primary/5 hover:text-primary rounded-xl transition-colors border border-transparent hover:border-primary/10"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className={`flex items-end gap-2 bg-gray-50 rounded-2xl p-2 border-2 transition-all ${
            isListening 
              ? 'border-red-400 ring-2 ring-red-200 bg-red-50/50' 
              : 'border-gray-200 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50'
          }`}>
            {/* Listening Indicator */}
            {isListening && (
              <div className="flex items-center gap-2 px-2">
                <div className="flex gap-1">
                  <span className="w-1 h-4 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-1 h-6 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-1 h-4 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></span>
                </div>
                <span className="text-xs font-medium text-red-600">Listening...</span>
              </div>
            )}

            <textarea
              ref={inputRef as any}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder={isListening ? "Speak now..." : "Type a message..."}
              disabled={loading && !currentResponse && false} // Allow typing while streaming
              rows={1}
              className="flex-1 bg-transparent px-2 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none resize-none max-h-32"
              style={{ minHeight: '44px' }}
            />

            {/* Mic/Stop Button */}
            {isSpeechSupported && (
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={handleMicClick}
                className={`p-2 rounded-xl transition-all ${
                  isListening
                    ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 hover:bg-red-600'
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                }`}
                title={isListening ? 'Stop listening' : 'Start voice input'}
              >
                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
              </motion.button>
            )}

            {/* Send Button */}
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || !isConnected}
              className="p-2 bg-primary text-white rounded-xl shadow-lg shadow-primary/30 hover:bg-primary/90 disabled:opacity-50 disabled:shadow-none transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
