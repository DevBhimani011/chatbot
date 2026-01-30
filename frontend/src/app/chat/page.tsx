import { ChatBox } from './components';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col bg-slate-50">
      {/* Header */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 -ml-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all">
                <ArrowLeft size={20} />
              </Link>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
                Chat Interface
              </h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden p-4 sm:p-6 lg:p-8 flex justify-center">
        <div className="w-full max-w-4xl h-full shadow-2xl rounded-2xl shadow-indigo-100/50">
          <ChatBox />
        </div>
      </main>
    </div>
  );
}
