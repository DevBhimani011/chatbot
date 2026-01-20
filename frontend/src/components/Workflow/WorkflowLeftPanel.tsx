import { useState } from 'react';
import { API_ENDPOINTS } from '@/config/api';

type Workflow = {
  id: string;
  name: string;
};

type WorkflowLeftPanelProps = {
  workflows: Workflow[];
  selectedWorkflow: Workflow | null;
  onSelectWorkflow: (workflow: Workflow) => void;
  onRefresh: () => void;
};

export function WorkflowLeftPanel({
  workflows,
  selectedWorkflow,
  onSelectWorkflow,
  onRefresh,
}: WorkflowLeftPanelProps) {
  const [name, setName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateWorkflow = async () => {
    if (!name.trim()) return;

    setIsCreating(true);
    try {
      const res = await fetch(API_ENDPOINTS.WORKFLOWS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });

      const workflow = await res.json();

      // Create first empty node
      await fetch(API_ENDPOINTS.NODES, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflow.id,
          value: '',
        }),
      });

      setName('');
      onRefresh();
    } catch (error) {
      console.error('Error creating workflow:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="w-64 border-r border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-y-auto">
      <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
        Workflows
      </h2>

      <div className="mb-4 flex flex-col gap-2">
        <input
          placeholder="Workflow name"
          value={name}
          onChange={e => setName(e.target.value)}
          disabled={isCreating}
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-900"
        />

        <button
          type="button"
          onClick={handleCreateWorkflow}
          disabled={isCreating || !name.trim()}
          className="w-full rounded-lg bg-blue-500 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-600 disabled:opacity-50 dark:bg-blue-600 dark:hover:bg-blue-700"
        >
          + Create Workflow
        </button>
      </div>

      {/* Workflows List */}
      <div className="space-y-1">
        {workflows.length === 0 ? (
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 py-4">
            No workflows yet
          </p>
        ) : (
          workflows.map(wf => (
            <button
              key={wf.id}
              onClick={() => onSelectWorkflow(wf)}
              className={`w-full rounded-lg px-3 py-2 text-left font-medium transition-colors ${
                selectedWorkflow?.id === wf.id
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600'
              }`}
            >
              {wf.name}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
