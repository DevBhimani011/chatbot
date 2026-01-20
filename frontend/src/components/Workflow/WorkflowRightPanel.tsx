import { Node, Edge } from 'reactflow';
import { API_ENDPOINTS } from '@/config/api';

type NodeData = {
  id: string;
  value: string;
};

type BackendEdge = {
  id: string;
  from_node_id: string;
  to_node_id: string;
};

type Workflow = {
  id: string;
  name: string;
};

type WorkflowRightPanelProps = {
  selectedNode: NodeData | undefined;
  editValue: string;
  onEditValueChange: (value: string) => void;
  onSaveNode: () => void;
  onAddNextCard: () => void;
  onDeleteWorkflow: () => void;
  selectedWorkflow: Workflow | null;
};

export function WorkflowRightPanel({
  selectedNode,
  editValue,
  onEditValueChange,
  onSaveNode,
  onAddNextCard,
  onDeleteWorkflow,
  selectedWorkflow,
}: WorkflowRightPanelProps) {
  return (
    <div className="w-80 border-l border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-y-auto">
      <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
        Properties
      </h2>

      {!selectedNode ? (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center dark:border-gray-600">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Select a node to edit
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
              Node Content
            </label>
            <textarea
              value={editValue}
              onChange={e => onEditValueChange(e.target.value)}
              rows={8}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-900"
              placeholder="Enter node content..."
            />
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onSaveNode}
              className="flex-1 rounded-lg bg-blue-500 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700"
            >
              Save
            </button>

            {selectedWorkflow && (
              <button
                type="button"
                onClick={onDeleteWorkflow}
                className="flex-1 rounded-lg bg-red-500 px-4 py-2 font-medium text-white transition-colors hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700"
              >
                Delete
              </button>
            )}
          </div>

          <button
            onClick={onAddNextCard}
            className="w-full rounded-lg bg-green-500 px-4 py-2 font-medium text-white transition-colors hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700"
          >
            ➕ Add Node
          </button>
        </div>
      )}
    </div>
  );
}
