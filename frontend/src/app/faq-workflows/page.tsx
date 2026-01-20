'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

type FAQWorkflow = {
  id: string;
  name: string;
};

export default function FAQWorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<FAQWorkflow[]>([]);
  const [name, setName] = useState('');

  const fetchWorkflows = async () => {
    const res = await fetch('http://127.0.0.1:8000/tree-workflows');
    const data = await res.json();
    setWorkflows(data);
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const createWorkflow = async () => {
    if (!name.trim()) return;

    const res = await fetch('http://127.0.0.1:8000/tree-workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });

    const wf = await res.json();
    setName('');
    fetchWorkflows();

    // 👉 redirect to editor (we’ll build next)
    router.push(`/faq-workflows/${wf.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-white">
        📘 FAQ Workflows
      </h1>

      {/* Create */}
      <div className="mb-6 flex gap-3">
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="FAQ Workflow name"
          className="rounded-lg border px-4 py-2 dark:bg-gray-800 dark:text-white"
        />
        <button
          onClick={createWorkflow}
          className="rounded-lg bg-blue-600 px-5 py-2 text-white hover:bg-blue-700"
        >
          + Create
        </button>
      </div>

      {/* List */}
      <div className="space-y-2">
        {workflows.map(wf => (
          <button
            key={wf.id}
            onClick={() => router.push(`/faq-workflows/${wf.id}`)}
            className="block w-full rounded-lg bg-white p-4 text-left shadow hover:bg-gray-50 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-700"
          >
            {wf.name}
          </button>
        ))}
      </div>
    </div>
  );
}
