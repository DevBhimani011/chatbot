'use client';

import { useEffect, useRef, useState } from 'react';
import { API_ENDPOINTS } from '@/config/api';
import { Send, Bot, User, Paperclip, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ---------------- TREE START ---------------- */

  useEffect(() => {
    fetch(`${API_ENDPOINTS.CHAT}tree/start`)
      .then(res => res.json())
      .then(data => {
        setMessages([
          {
            sender: 'bot',
            text: data.text,
            buttons: data.buttons,
          },
        ]);
      });
  }, []);

  /* ---------------- STATIC CHAT ---------------- */

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userText = input;
    setInput('');
    setLoading(true);

    setMessages(prev => [...prev, { sender: 'user', text: userText }]);

    try {
      const res = await fetch(`${API_ENDPOINTS.CHAT}message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText }),
      });

      const data = await res.json();

      if (data.type === 'static') {
        setMessages(prev => [...prev, { sender: 'bot', text: data.text }]);
      } else if (data.type === 'faq') {
        const faqRes = await fetch(`${API_ENDPOINTS.CHAT}tree/next`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: data.value }),
        });

        const faqData = await faqRes.json();

        setMessages(prev => [
          ...prev,
          {
            sender: 'bot',
            text: faqData.text,
            buttons: faqData.buttons,
          },
        ]);
      } else {
        setMessages(prev => [...prev, { sender: 'bot', text: data.text }]);
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { sender: 'bot', text: 'Server error' },
      ]);
    }

    setLoading(false);
  };

  /* ---------------- TREE BUTTON CLICK ---------------- */

  const handleButtonClick = async (value: string) => {
    setLoading(true);

    setMessages(prev => [...prev, { sender: 'user', text: value }]);

    const res = await fetch(`${API_ENDPOINTS.CHAT}tree/next`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    });

    const data = await res.json();

    setMessages(prev => [
      ...prev,
      {
        sender: 'bot',
        text: data.text,
        buttons: data.buttons,
      },
    ]);

    setLoading(false);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    // Optimistic update
    setMessages(prev => [...prev, { sender: 'user', text: `Uploaded PDF: ${file.name}` }]);

    const res = await fetch(`${API_ENDPOINTS.CHAT}upload-pdf`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    setMessages(prev => [...prev, { sender: 'bot', text: `PDF processed successfully. Created ${data.chunks} chunks.` }]);
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
          <p className="text-xs text-grna-500 flex items-center gap-1">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Online
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
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
            >
              <div className={`flex max-w-[80%] items-end gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}>
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
                  {msg.text && <p className="whitespace-pre-wrap">{msg.text}</p>}

                  {/* Buttons (Likely only for bot) */}
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

        {loading && (
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
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <div className="border-t border-gray-100 bg-white p-4">
        <div className="flex items-end gap-2 bg-gray-50 rounded-2xl p-2 border border-gray-200 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all">
          <button
            onClick={handleUploadClick}
            className="p-2 text-gray-400 hover:text-primary transition-colors rounded-xl hover:bg-white"
            title="Upload PDF"
          >
            <Paperclip size={20} />
          </button>

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
            placeholder="Type a message..."
            disabled={loading}
            rows={1}
            className="flex-1 bg-transparent px-2 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none resize-none max-h-32"
            style={{ minHeight: '44px' }}
          />

          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="p-2 bg-primary text-white rounded-xl shadow-lg shadow-primary/30 hover:bg-primary/90 disabled:opacity-50 disabled:shadow-none transition-all"
          >
            <Send size={18} />
          </button>
        </div>

        <input
          type="file"
          accept="application/pdf"
          ref={fileInputRef}
          onChange={handleFileChange}
          hidden
        />
        <div className="mt-2 flex justify-center">
          <p className="text-[10px] text-gray-400 flex items-center gap-1">
            <FileText size={10} /> Supports PDF uploads for context
          </p>
        </div>
      </div>
    </div>
  );
}
