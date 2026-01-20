import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  NodeMouseHandler,
  Background,
  Controls,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { API_ENDPOINTS } from '@/config/api';

type Workflow = {
  id: string;
  name: string;
};

type WorkflowCanvasProps = {
  selectedWorkflow: Workflow | null;
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  onNodeClick: NodeMouseHandler;
  onConnect: (connection: Connection) => void;
  nodeTypes: any;
  backendNodes: any[];
};

export function WorkflowCanvas({
  selectedWorkflow,
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  onConnect,
  nodeTypes,
  backendNodes,
}: WorkflowCanvasProps) {
  if (!selectedWorkflow) {
    return (
      <div className="flex-1 bg-gray-100 dark:bg-gray-900 flex h-full items-center justify-center">
        <div className="rounded-xl border-2 border-dashed border-gray-300 bg-white p-12 text-center dark:border-gray-600 dark:bg-gray-800">
          <div className="text-5xl mb-4">🔄</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            No Workflow Selected
          </h3>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Select or create a workflow from the left panel
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gray-100 dark:bg-gray-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        style={{ backgroundColor: '#f3f4f6', borderRadius: 0 }}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
