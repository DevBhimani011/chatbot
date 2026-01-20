export function WorkflowHeader() {
  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Workflow Builder
          </h1>
          <div className="flex gap-3">
            <a
              href="/"
              className="rounded-lg px-4 py-2 text-gray-700 font-medium transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              Home
            </a>
            <a
              href="/chat"
              className="rounded-lg bg-blue-500 px-4 py-2 text-white font-medium transition-all hover:bg-blue-600"
            >
              Chat
            </a>
            <a
  href="/faq-workflows"
  className="rounded-lg bg-green-500 px-4 py-2 text-white font-medium hover:bg-green-600"
>
  FAQ Builder
</a>

          </div>
        </div>
      </div>
    </nav>
  );
}
