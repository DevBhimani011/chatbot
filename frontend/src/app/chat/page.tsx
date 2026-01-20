import ChatBox from '../components/ChatBox';

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm shadow-sm dark:border-gray-700 dark:bg-gray-800/80">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Chat
            </h1>
            <div className="flex gap-3">
              <a
                href="/"
                className="rounded-lg px-4 py-2 text-gray-700 font-medium transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Home
              </a>
              <a
                href="/workflow"
                className="rounded-lg bg-indigo-500 px-4 py-2 text-white font-medium transition-all hover:bg-indigo-600"
              >
                Workflow
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content - Fixed Height */}
      <main className="flex-1 overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto h-full max-w-4xl rounded-xl shadow-lg">
          <ChatBox />
        </div>
      </main>
    </div>
  );
}
