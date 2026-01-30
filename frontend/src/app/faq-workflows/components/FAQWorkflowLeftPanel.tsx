import { Plus, Layout } from 'lucide-react';

type FAQWorkflow = {
  id: string;
  name: string;
};

type FAQWorkflowLeftPanelProps = {
  workflows: FAQWorkflow[];
  selectedWorkflow: FAQWorkflow | null;
  workflowName: string;
  isCreating: boolean;
  onWorkflowNameChange: (name: string) => void;
  onCreateWorkflow: () => void;
  onSelectWorkflow: (workflow: FAQWorkflow) => void;
};

export function FAQWorkflowLeftPanel({
  workflows,
  selectedWorkflow,
  workflowName,
  isCreating,
  onWorkflowNameChange,
  onCreateWorkflow,
  onSelectWorkflow,
}: FAQWorkflowLeftPanelProps) {
  return (
    <div className="w-72 border-r border-gray-200 bg-gray-50/50 p-6 shadow-sm flex flex-col h-full">
      <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
        <Layout size={16} />
        FAQ Workflows
      </h2>

      <div className="mb-4 flex flex-col gap-3">
        <input
          placeholder="New workflow name..."
          value={workflowName}
          onChange={(e) => onWorkflowNameChange(e.target.value)}
          disabled={isCreating}
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-green-500 focus:ring-2 focus:ring-green-100 disabled:opacity-50"
        />
        <button
          type="button"
          onClick={onCreateWorkflow}
          disabled={isCreating || !workflowName.trim()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-green-500/20 transition-all hover:bg-green-700 disabled:opacity-50 disabled:shadow-none"
        >
          <Plus size={16} />
          Create
        </button>
      </div>

      <div className="space-y-1 overflow-y-auto pr-1">
        {workflows.length === 0 ? (
          <div className="py-4 text-center">
            <p className="text-sm text-gray-400">No workflows yet</p>
          </div>
        ) : (
          workflows.map((wf) => (
            <button
              key={wf.id}
              onClick={() => onSelectWorkflow(wf)}
              className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-all ${
                selectedWorkflow?.id === wf.id
                  ? 'bg-white text-green-600 shadow-sm ring-1 ring-gray-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
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
