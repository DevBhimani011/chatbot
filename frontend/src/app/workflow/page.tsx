'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  NodeMouseHandler,
} from 'reactflow';

import {
  WorkflowNode,
  WorkflowLeftPanel,
  WorkflowCanvas,
  WorkflowRightPanel,
  WorkflowHeader,
} from '@/components/Workflow';

import { API_ENDPOINTS } from '@/config/api';

type Workflow = { id: string; name: string };
type NodeData = { id: string; value: string };

const nodeTypes = { default: WorkflowNode };

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);

  const [backendNodes, setBackendNodes] = useState<NodeData[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const selectedNode = backendNodes.find(n => n.id === selectedNodeId);

  /* ---------------- LOAD ---------------- */

  const fetchWorkflows = async () => {
    const res = await fetch(API_ENDPOINTS.WORKFLOWS);
    setWorkflows(await res.json());
  };

  const loadWorkflow = async (wf: Workflow) => {
    setSelectedWorkflow(wf);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);

    const nodesRes = await fetch(API_ENDPOINTS.WORKFLOW_NODES(wf.id));
    const nodesData: NodeData[] = await nodesRes.json();

    const edgesRes = await fetch(API_ENDPOINTS.EDGES_BY_WORKFLOW(wf.id));
    const edgesData = await edgesRes.json();

    setBackendNodes(nodesData);

    setNodes(
      nodesData.map((n, i) => ({
        id: n.id,
        data: { label: n.value || '(empty)' },
        position: { x: 200, y: i * 150 },
        type: 'default',
      }))
    );

    setEdges(
      edgesData.map((e: any) => ({
        id: e.id,
        source: e.from_node_id,
        target: e.to_node_id,
      }))
    );
  };

  /* ---------------- NODE ---------------- */

  const saveNode = async () => {
  if (!selectedNodeId) return;
    console.log('Saving node:', selectedNodeId, editValue);
    console.log('API_URL:', API_ENDPOINTS.NODES); // Check what URL is actually being used
  console.log('Saving node:', selectedNodeId, editValue);
  try {
    const response = await fetch(`${API_ENDPOINTS.NODES}/${selectedNodeId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: editValue }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    setBackendNodes(n =>
      n.map(x => (x.id === selectedNodeId ? { ...x, value: editValue } : x))
    );

    setNodes(n =>
      n.map(x =>
        x.id === selectedNodeId
          ? { ...x, data: { label: editValue || '(empty)' } }
          : x
      )
    );
  } catch (error) {
    console.error('Failed to save node:', error);
  }
};

  const addNextCard = async () => {
  if (!selectedWorkflow) return;

  const res = await fetch(API_ENDPOINTS.NODES, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_id: selectedWorkflow.id,
      value: '',
    }),
  });

  const node = await res.json();

  // backend state
  setBackendNodes(prev => [...prev, node]);

  // react-flow state
  setNodes(prev => [
    ...prev,
    {
      id: node.id,
      data: { label: '(empty)' },
      position: { x: 200, y: prev.length * 150 },
      type: 'default',
    },
  ]);

  // just select the new node
  setSelectedNodeId(node.id);
  setEditValue('');
};


  const deleteNode = async () => {
    if (!selectedNodeId) return;

    await fetch(`${API_ENDPOINTS.NODES}/${selectedNodeId}`, { method: 'DELETE' });

    setNodes(n => n.filter(x => x.id !== selectedNodeId));
    setEdges(e => e.filter(x => x.source !== selectedNodeId && x.target !== selectedNodeId));
    setBackendNodes(n => n.filter(x => x.id !== selectedNodeId));
    setSelectedNodeId(null);
  };

  /* ---------------- EDGE ---------------- */

  const deleteEdge = async () => {
    if (!selectedEdgeId) return;
    await fetch(`${API_ENDPOINTS.EDGES}/${selectedEdgeId}`, { method: 'DELETE' });
    setEdges(e => e.filter(x => x.id !== selectedEdgeId));
    setSelectedEdgeId(null);
  };

  const onConnect = async (connection: Connection) => {
    if (!selectedWorkflow) return;

    const res = await fetch(API_ENDPOINTS.EDGES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow_id: selectedWorkflow.id,
        from_node_id: connection.source,
        to_node_id: connection.target,
      }),
    });

    const edge = await res.json();
    setEdges(e => addEdge({ ...connection, id: edge.id }, e));
  };

  /* ---------------- WORKFLOW ---------------- */

  const deleteWorkflow = async () => {
    if (!selectedWorkflow) return;

    await fetch(API_ENDPOINTS.WORKFLOW_BY_ID(selectedWorkflow.id), {
      method: 'DELETE',
    });

    setSelectedWorkflow(null);
    setNodes([]);
    setEdges([]);
    setBackendNodes([]);
    fetchWorkflows();
  };

  /* ---------------- EVENTS ---------------- */

  const onNodeClick: NodeMouseHandler = (_, node) => {
    setSelectedNodeId(node.id);
    setSelectedEdgeId(null);
    setEditValue(node.data.label);
  };

  const onEdgeClick = (_: any, edge: Edge) => {
    setSelectedEdgeId(edge.id);
    setSelectedNodeId(null);
  };

  const onNodeDragStop = useCallback(
  async (_: any, node: Node) => {
    await fetch(`${API_ENDPOINTS.TREE_NODES}/${node.id}/position`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        position_x: node.position.x,
        position_y: node.position.y,
      }),
    });
  },
  []
);


  useEffect(() => {
    fetchWorkflows();
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <WorkflowHeader />

      <div className="flex flex-1">
        <WorkflowLeftPanel
          workflows={workflows}
          selectedWorkflow={selectedWorkflow}
          onSelectWorkflow={loadWorkflow}
          onRefresh={fetchWorkflows}
        />

        <WorkflowCanvas
          selectedWorkflow={selectedWorkflow}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
        />

        <WorkflowRightPanel
          selectedNode={selectedNode}
          selectedEdgeId={selectedEdgeId}
          editValue={editValue}
          onEditValueChange={setEditValue}
          onSaveNode={saveNode}
          onAddNextCard={addNextCard}
          onDeleteNode={deleteNode}
          onDeleteEdge={deleteEdge}
          onDeleteWorkflow={deleteWorkflow}
          selectedWorkflow={selectedWorkflow}
        />
      </div>
    </div>
  );
}
