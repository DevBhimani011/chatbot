type NodeData = {
  id: string;
  value: string;
};

type Workflow = {
  id: string;
  name: string;
};

type WorkflowRightPanelProps = {
  selectedNode: NodeData | undefined;
  selectedEdgeId: string | null;
  editValue: string;
  onEditValueChange: (value: string) => void;
  onSaveNode: () => void;
  onAddNextCard: () => void;
  onDeleteNode: () => void;
  onDeleteEdge: () => void;
  onDeleteWorkflow: () => void;
  selectedWorkflow: Workflow | null;
};

export function WorkflowRightPanel({
  selectedNode,
  selectedEdgeId,
  editValue,
  onEditValueChange,
  onSaveNode,
  onAddNextCard,
  onDeleteNode,
  onDeleteEdge,
  onDeleteWorkflow,
  selectedWorkflow,
}: WorkflowRightPanelProps) {
  return (
    <div className="w-80 border-l border-gray-200 bg-white p-6 dark:bg-gray-800">
      <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">
        Properties
      </h2>

      {!selectedNode && !selectedEdgeId && (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Select a node or edge
        </p>
      )}

      {selectedNode && (
        <>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Node Content
          </label>
          <textarea
            value={editValue}
            onChange={e => onEditValueChange(e.target.value)}
            rows={6}
            className="w-full rounded-lg border px-3 py-2 dark:bg-gray-700 dark:text-white"
          />

          <button
            onClick={onSaveNode}
            className="mt-3 w-full rounded-lg bg-blue-500 py-2 text-white"
          >
            💾 Save Node
          </button>

          <button
            onClick={onDeleteNode}
            className="mt-2 w-full rounded-lg bg-red-500 py-2 text-white"
          >
            🗑 Delete Node
          </button>
        </>
      )}

      {selectedEdgeId && (
        <button
          onClick={onDeleteEdge}
          className="mt-4 w-full rounded-lg bg-red-600 py-2 text-white"
        >
          🗑 Delete Edge
        </button>
      )}

      <button
        onClick={onAddNextCard}
        disabled={!selectedWorkflow}
        className="mt-6 w-full rounded-lg bg-green-500 py-2 text-white disabled:opacity-50"
      >
        ➕ Add Node
      </button>

      {selectedWorkflow && (
        <button
          onClick={onDeleteWorkflow}
          className="mt-4 w-full rounded-lg bg-red-700 py-2 text-white"
        >
          🗑 Delete Workflow
        </button>
      )}
    </div>
  );
}
