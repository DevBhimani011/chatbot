'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChatBox } from './components';
import { AppNavbar } from '@/components/AppNavbar';

export default function ChatPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <AppNavbar />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden p-4 sm:p-6 lg:p-8 flex justify-center">
        <div className="w-full max-w-4xl h-full shadow-2xl rounded-2xl shadow-indigo-100/50">
          <ChatBox />
        </div>
      </main>
    </div>
  );
}
