export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm dark:border-gray-700 dark:bg-gray-800/80">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Chatbot Workflow
            </h1>
            <div className="flex gap-3">
              <a
                href="/chat"
                className="rounded-lg bg-blue-500 px-4 py-2 text-white font-medium transition-all hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700"
              >
                Chat
              </a>
              <a
                href="/workflow"
                className="rounded-lg bg-indigo-500 px-4 py-2 text-white font-medium transition-all hover:bg-indigo-600 dark:bg-indigo-600 dark:hover:bg-indigo-700"
              >
                Workflow
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-white p-8 shadow-xl dark:bg-gray-800 sm:p-12">
          <div className="mb-8 text-center">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white sm:text-5xl">
              Welcome to Your Chatbot Workflow
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Build and manage intelligent conversational workflows with ease
            </p>
          </div>

          <div className="grid gap-8 py-8 sm:grid-cols-2">
            <div className="rounded-xl border border-gray-200 bg-gradient-to-br from-blue-50 to-blue-100 p-6 dark:border-gray-700 dark:from-gray-700 dark:to-gray-600">
              <div className="mb-3 text-3xl">💬</div>
              <h3 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                Chat Interface
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                Interact with your static chatbot in a clean, modern chat interface
              </p>
              <a
                href="/chat"
                className="mt-4 inline-block rounded-lg bg-blue-500 px-4 py-2 text-white font-medium transition-all hover:bg-blue-600"
              >
                Start Chatting →
              </a>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gradient-to-br from-indigo-50 to-indigo-100 p-6 dark:border-gray-700 dark:from-gray-700 dark:to-gray-600">
              <div className="mb-3 text-3xl">⚙️</div>
              <h3 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
                Workflow Builder
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                Design and manage complex workflows with an intuitive node-based editor
              </p>
              <a
                href="/workflow"
                className="mt-4 inline-block rounded-lg bg-indigo-500 px-4 py-2 text-white font-medium transition-all hover:bg-indigo-600"
              >
                Build Workflows →
              </a>
            </div>
          </div>

          <div className="mt-12 border-t border-gray-200 pt-8 dark:border-gray-700">
            <h3 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
              Features
            </h3>
            <ul className="grid gap-3 sm:grid-cols-2">
              <li className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500 text-sm font-bold text-white">
                  ✓
                </span>
                Real-time chat interactions
              </li>
              <li className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500 text-sm font-bold text-white">
                  ✓
                </span>
                Visual workflow design
              </li>
              <li className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500 text-sm font-bold text-white">
                  ✓
                </span>
                Easy-to-use interface
              </li>
              <li className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500 text-sm font-bold text-white">
                  ✓
                </span>
                Persistent data storage
              </li>
            </ul>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white/50 py-8 dark:border-gray-700 dark:bg-gray-800/50">
        <div className="mx-auto max-w-7xl px-4 text-center text-gray-600 dark:text-gray-400">
          <p>© 2026 Chatbot Workflow. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
