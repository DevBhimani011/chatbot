import ReactFlow, {
  Node,
  Edge,
  Connection,
  NodeMouseHandler,
  Background,
  Controls,
  MiniMap,
  NodeDragHandler,
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
  onNodeDragStop?: NodeDragHandler;
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
  onNodeDragStop,
  nodeTypes,
}: WorkflowCanvasProps) {
  if (!selectedWorkflow) {
    return (
      <div className="flex-1 bg-gray-50 flex h-full items-center justify-center">
        <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-white p-12 text-center shadow-sm">
          <h3 className="text-xl font-semibold text-gray-900">
            No Workflow Selected
          </h3>
          <p className="mt-2 text-gray-500">
            Select a workflow from the sidebar to start editing
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={() => '#e2e8f0'}
          maskColor="rgba(241, 245, 249, 0.7)"
        />
      </ReactFlow>
    </div>
  );
}
