'use client';

import { useEffect, useRef, useState } from 'react';

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ---------------- TREE START ---------------- */

  useEffect(() => {
    fetch('http://127.0.0.1:8000/chat/tree/start')
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
    const res = await fetch('http://127.0.0.1:8000/chat/static', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText }),
    });

    const data = await res.json();

    // ✅ STATIC ANSWER
    if (data.type === 'static') {
      setMessages(prev => [...prev, { sender: 'bot', text: data.text }]);
    }

    // 🔁 FALLBACK → FAQ TREE
    else if (data.type === 'faq') {
      const faqRes = await fetch('http://127.0.0.1:8000/chat/tree/next', {
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
    }

    else {
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

    const res = await fetch('http://127.0.0.1:8000/chat/tree/next', {
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

  /* ---------------- UI ---------------- */

  return (
    <div className="flex h-full flex-col rounded-xl bg-[#0f172a] shadow-xl">
      {/* HEADER */}
      <div className="border-b border-gray-700 px-4 py-3 text-center text-white">
        <h2 className="text-lg font-semibold">🤖</h2>
      </div>

      {/* MESSAGES */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs rounded-2xl px-4 py-2 text-sm ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              {msg.text && <p>{msg.text}</p>}

              {msg.buttons && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.buttons.map((btn, i) => (
                    <button
                      key={i}
                      onClick={() => handleButtonClick(btn.value)}
                      className="rounded-full bg-blue-500 px-4 py-1 text-xs text-white transition hover:bg-blue-600"
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-gray-800 px-4 py-2 text-xs text-gray-400">
              Bot is typing...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message..."
            disabled={loading}
            className="flex-1 rounded-full bg-gray-800 px-4 py-2 text-sm text-white outline-none placeholder-gray-500 focus:ring-2 focus:ring-blue-600"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:bg-gray-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
