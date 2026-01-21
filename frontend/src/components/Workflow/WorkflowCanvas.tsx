import ReactFlow, {
  Node,
  Edge,
  Connection,
  NodeMouseHandler,
  Background,
  Controls,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';

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
  onEdgeClick: (event: any, edge: Edge) => void;
  onConnect: (connection: Connection) => void;
  nodeTypes: any;
};

export function WorkflowCanvas({
  selectedWorkflow,
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  onEdgeClick,
  onConnect,
  nodeTypes,
}: WorkflowCanvasProps) {
  if (!selectedWorkflow) {
    return (
      <div className="flex-1 bg-gray-100 dark:bg-gray-900 flex h-full items-center justify-center">
        <div className="rounded-xl border-2 border-dashed border-gray-300 bg-white p-12 text-center dark:border-gray-600 dark:bg-gray-800">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            No Workflow Selected
          </h3>
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
        onEdgeClick={onEdgeClick}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
