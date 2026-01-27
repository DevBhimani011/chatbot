import Link from 'next/link';

export function WorkflowHeader() {
  return (
    <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-20">
      <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
              Workflow Builder
            </h1>

          </div>
          <div className="flex gap-2">
            <Link
              href="/"
              className="rounded-lg px-4 py-2 text-sm text-gray-600 font-medium transition-colors hover:bg-gray-50 hover:text-gray-900"
            >
              Home
            </Link>
            <Link
              href="/chat"
              className="rounded-lg bg-white border border-gray-200 px-4 py-2 text-sm text-gray-700 font-medium hover:bg-gray-50 hover:text-primary transition-all shadow-sm"
            >
              Chat
            </Link>
            <Link
              href="/faq-workflows"
              className="rounded-lg bg-primary px-4 py-2 text-sm text-white font-medium hover:bg-primary/90 shadow-md shadow-primary/20 transition-all"
            >
              FAQ Builder
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
