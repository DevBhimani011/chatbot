import { Plus, Save, Settings, Trash2 } from 'lucide-react';

type FAQWorkflowRightPanelProps = {
  selectedWorkflow: any;
  selectedNode: any;
  selectedEdgeId: string | null;
  editValue: string;
  onEditValueChange: (value: string) => void;
  onSaveNode: () => void;
  onAddNode: () => void;
  onDeleteNode: () => void;
  onDeleteEdge: () => void;
  onDeleteWorkflow: () => void;
};

export function FAQWorkflowRightPanel({
  selectedWorkflow,
  selectedNode,
  selectedEdgeId,
  editValue,
  onEditValueChange,
  onSaveNode,
  onAddNode,
  onDeleteNode,
  onDeleteEdge,
  onDeleteWorkflow,
}: FAQWorkflowRightPanelProps) {
  return (
    <div className="w-80 border-l border-gray-200 bg-white p-6 shadow-xl shadow-gray-200/50 flex flex-col h-full overflow-y-auto">
      <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
        <Settings size={16} />
        Properties
      </h2>

      {!selectedWorkflow ? (
        <div className="flex flex-col items-center justify-center py-12 text-center rounded-xl bg-gray-50 border border-dashed border-gray-200">
          <p className="text-sm text-gray-400">Select a workflow first</p>
        </div>
      ) : !selectedNode ? (
        <div className="flex flex-col items-center justify-center py-12 text-center rounded-xl bg-gray-50 border border-dashed border-gray-200">
          <p className="text-sm text-gray-400">Select a node to edit</p>
        </div>
      ) : (
        <div className="space-y-4 animate-fadeIn">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">FAQ Content</label>
            <textarea
              value={editValue}
              onChange={(e) => onEditValueChange(e.target.value)}
              rows={8}
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              placeholder="Enter content..."
            />
          </div>

          <button
            type="button"
            onClick={onSaveNode}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/20 transition-all hover:bg-blue-700 hover:shadow-blue-500/30"
          >
            <Save size={16} />
            Save Changes
          </button>
        </div>
      )}

      <div className="mt-auto pt-6 border-t border-gray-100 space-y-3">
        <button
          onClick={onAddNode}
          disabled={!selectedWorkflow}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-green-500/20 transition-all hover:bg-green-700 disabled:opacity-50 disabled:shadow-none"
        >
          <Plus size={16} />
          Add FAQ Node
        </button>

        {selectedNode && (
          <button
            onClick={onDeleteNode}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-medium text-red-600 transition-all hover:bg-red-100 border border-transparent hover:border-red-200"
          >
            <Trash2 size={16} />
            Delete Node
          </button>
        )}

        {selectedEdgeId && (
          <button
            onClick={onDeleteEdge}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-medium text-red-600 transition-all hover:bg-red-100 border border-transparent hover:border-red-200"
          >
            <Trash2 size={16} />
            Delete Connection
          </button>
        )}

        {selectedWorkflow && (
          <button
            onClick={onDeleteWorkflow}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-500 transition-all hover:bg-gray-100 hover:text-red-700"
          >
            <Trash2 size={16} />
            Delete Workflow
          </button>
        )}
      </div>
    </div>
  );
}
