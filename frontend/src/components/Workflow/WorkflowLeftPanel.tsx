import { useState } from 'react';
import { API_ENDPOINTS } from '@/config/api';
import { Plus, Layout, FolderOpen } from 'lucide-react';
import { gql, useMutation } from '@apollo/client';

const CREATE_WORKFLOW = gql`
  mutation CreateWorkflow($name: String!) {
    createWorkflow(name: $name) {
      id
      name
    }
  }
`;

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

  const [createWorkflowMutation] = useMutation(CREATE_WORKFLOW);

  const handleCreateWorkflow = async () => {
    if (!name.trim()) return;

    setIsCreating(true);
    try {
      await createWorkflowMutation({ variables: { name } });

      setName('');
      onRefresh();
    } catch (error) {
      console.error('Error creating workflow:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="w-72 border-r border-gray-200 bg-gray-50/50 p-6 flex flex-col h-full">
      <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
        <FolderOpen size={16} />
        Your Workflows
      </h2>

      <div className="mb-6 flex flex-col gap-3">
        <input
          placeholder="New workflow name..."
          value={name}
          onChange={e => setName(e.target.value)}
          disabled={isCreating}
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:opacity-50"
        />

        <button
          type="button"
          onClick={handleCreateWorkflow}
          disabled={isCreating || !name.trim()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 disabled:opacity-50 disabled:shadow-none"
        >
          <Plus size={16} />
          Create
        </button>
      </div>

      {/* Workflows List */}
      <div className="space-y-1 overflow-y-auto pr-1 custom-scrollbar">
        {workflows.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="mb-2 rounded-full bg-gray-100 p-3 text-gray-400">
              <Layout size={20} />
            </div>
            <p className="text-sm text-gray-500">No workflows yet</p>
          </div>
        ) : (
          workflows.map(wf => (
            <button
              key={wf.id}
              onClick={() => onSelectWorkflow(wf)}
              className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-all ${selectedWorkflow?.id === wf.id
                  ? 'bg-white text-primary shadow-sm ring-1 ring-gray-200'
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
