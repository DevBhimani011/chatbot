'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeMouseHandler,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import type { Edge as RFEdge } from 'reactflow';
import 'reactflow/dist/style.css';

import { API_ENDPOINTS } from '@/config/api';
import { WorkflowHeader, WorkflowNode } from '@/components/Workflow';

type FAQWorkflow = {
  id: string;
  name: string;
};

type FaqNodeData = {
  label: string;
  isSelected?: boolean;
};

type TreeNode = {
  id: string;
  value: string;
};

type TreeEdge = {
  id: string;
  from_node_id: string;
  to_node_id: string;
};

// Define nodeTypes outside component to prevent warnings
const nodeTypes = { default: WorkflowNode };

export default function FAQWorkflowBuilder({ initialWorkflowId }: { initialWorkflowId?: string }) {
  const router = useRouter();

  const [workflows, setWorkflows] = useState<FAQWorkflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<FAQWorkflow | null>(null);
  const [name, setName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const [backendNodes, setBackendNodes] = useState<TreeNode[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  const selectedNode = useMemo(
    () => backendNodes.find(n => n.id === selectedNodeId),
    [backendNodes, selectedNodeId]
  );

  const fetchWorkflows = useCallback(async () => {
    const res = await fetch(API_ENDPOINTS.TREE_WORKFLOWS);
    const data = await res.json();
    if (Array.isArray(data)) setWorkflows(data);
  }, []);

  const loadGraph = useCallback(
    async (workflowId: string) => {
      const [nodesRes, edgesRes] = await Promise.all([
        fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${workflowId}/nodes`),
        fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${workflowId}/edges`),
      ]);

      const nodesData: TreeNode[] = (await nodesRes.json()) ?? [];
      const edgesData: TreeEdge[] = (await edgesRes.json()) ?? [];

      setBackendNodes(Array.isArray(nodesData) ? nodesData : []);

      const rfNodes = (Array.isArray(nodesData) ? nodesData : []).map((n, index) => {
        const isSelected = selectedNodeId === n.id;
        return {
          id: n.id,
          data: { label: n.value ?? '', isSelected },
          position: { x: 250, y: index * 150 },
          type: 'default',
          selected: isSelected,
        };
      });

      const rfEdges = (Array.isArray(edgesData) ? edgesData : []).map(e => ({
        id: e.id,
        source: e.from_node_id,
        target: e.to_node_id,
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
    },
    [selectedNodeId, setEdges, setNodes]
  );

  const selectWorkflow = useCallback(
    (wf: FAQWorkflow) => {
      setSelectedWorkflow(wf);
      setSelectedNodeId(null);
      setEditValue('');
      router.push(`/faq-workflows/${wf.id}`);
      loadGraph(wf.id);
    },
    [loadGraph, router]
  );

  const createWorkflow = useCallback(async () => {
    if (!name.trim()) return;
    setIsCreating(true);
    try {
      const res = await fetch(API_ENDPOINTS.TREE_WORKFLOWS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const wf = await res.json();
      if (!wf?.id) return;

      // create first empty FAQ node (mirrors normal workflow behavior)
      await fetch(API_ENDPOINTS.TREE_NODES, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tree_workflow_id: wf.id, value: '' }),
      });

      setName('');
      await fetchWorkflows();
      selectWorkflow(wf);
    } finally {
      setIsCreating(false);
    }
  }, [fetchWorkflows, name, selectWorkflow]);

  const addFaqNode = useCallback(async () => {
    if (!selectedWorkflow) return;

    const res = await fetch(API_ENDPOINTS.TREE_NODES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tree_workflow_id: selectedWorkflow.id, value: '' }),
    });
    if (!res.ok) return;

    const node = await res.json();
    if (!node?.id || typeof node.id !== 'string') return;

    setBackendNodes(prev => [...prev, { id: node.id, value: node.value ?? '' }]);
    setNodes(prev => [
      ...prev,
      {
        id: node.id,
        data: { label: node.value ?? '' },
        position: { x: 250, y: prev.length * 150 },
        type: 'default',
      },
    ]);
    setSelectedNodeId(node.id);
    setEditValue(node.value ?? '');
  }, [selectedWorkflow, setNodes]);

  const saveFaqNode = useCallback(async () => {
    if (!selectedNodeId) return;
    const res = await fetch(`${API_ENDPOINTS.TREE_NODES}/${selectedNodeId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: editValue }),
    });
    if (!res.ok) return;

    setBackendNodes(prev =>
      prev.map(n => (n.id === selectedNodeId ? { ...n, value: editValue } : n))
    );
    setNodes(prev =>
      prev.map(n => (n.id === selectedNodeId ? { ...n, data: { ...n.data, label: editValue } } : n))
    );
  }, [editValue, selectedNodeId, setNodes]);

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => {
    setSelectedNodeId(node.id);
    setEditValue(typeof (node.data as FaqNodeData | undefined)?.label === 'string' ? (node.data as FaqNodeData).label : '');
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!selectedWorkflow || !connection.source || !connection.target) return;

      const res = await fetch(API_ENDPOINTS.TREE_EDGES, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tree_workflow_id: selectedWorkflow.id,
          from_node_id: connection.source,
          to_node_id: connection.target,
        }),
      });
      if (!res.ok) return;

      const created = await res.json();
      const edgeId = created?.id || `${connection.source}-${connection.target}`;
      setEdges(prev => addEdge({ ...connection, id: edgeId }, prev));
    },
    [selectedWorkflow, setEdges]
  );

  const onEdgeClick = useCallback(
  (_: React.MouseEvent, edge: RFEdge) => {
    setSelectedEdgeId(edge.id);
    setSelectedNodeId(null);
  },
  []
);

const deleteFaqNode = async () => {
  if (!selectedNodeId) return;

  await fetch(`${API_ENDPOINTS.TREE_NODES}/${selectedNodeId}`, {
    method: 'DELETE',
  });

  setNodes(prev => prev.filter(n => n.id !== selectedNodeId));
  setEdges(prev => prev.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId));
  setBackendNodes(prev => prev.filter(n => n.id !== selectedNodeId));

  setSelectedNodeId(null);
  setEditValue('');
};

const deleteFaqEdge = async () => {
  if (!selectedEdgeId) return;

  await fetch(`${API_ENDPOINTS.TREE_EDGES}/${selectedEdgeId}`, {
    method: 'DELETE',
  });

  setEdges(prev => prev.filter(e => e.id !== selectedEdgeId));
  setSelectedEdgeId(null);
};

const deleteFaqWorkflow = async () => {
  if (!selectedWorkflow) return;

  await fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${selectedWorkflow.id}`, {
    method: 'DELETE',
  });

  setSelectedWorkflow(null);
  setNodes([]);
  setEdges([]);
  fetchWorkflows();
};



  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  // If user lands on /faq-workflows/[id], preselect and load.
  useEffect(() => {
    if (!initialWorkflowId) return;
    if (selectedWorkflow?.id === initialWorkflowId) return;

    const wf = workflows.find(w => w.id === initialWorkflowId);
    if (wf) {
      setSelectedWorkflow(wf);
      loadGraph(wf.id);
    } else if (workflows.length > 0) {
      // If the list loaded but doesn't contain it yet, still attempt to load graph.
      setSelectedWorkflow({ id: initialWorkflowId, name: 'FAQ Workflow' });
      loadGraph(initialWorkflowId);
    }
  }, [initialWorkflowId, loadGraph, selectedWorkflow?.id, workflows]);

  // Keep visual selection styles in sync.
  useEffect(() => {
    setNodes(prev =>
      prev.map(n => ({
        ...n,
        selected: n.id === selectedNodeId,
        data: {
          ...n.data,
          isSelected: n.id === selectedNodeId,
        },
      }))
    );
  }, [selectedNodeId, setNodes]);

  return (
    <div className="flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <WorkflowHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANEL */}
        <div className="w-64 border-r border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-y-auto">
          <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">FAQ Workflows</h2>

          <div className="mb-4 flex flex-col gap-2">
            <input
              placeholder="FAQ workflow name"
              value={name}
              onChange={e => setName(e.target.value)}
              disabled={isCreating}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-900"
            />
            <button
              type="button"
              onClick={createWorkflow}
              disabled={isCreating || !name.trim()}
              className="w-full rounded-lg bg-green-500 px-4 py-2 font-medium text-white transition-colors hover:bg-green-600 disabled:opacity-50 dark:bg-green-600 dark:hover:bg-green-700"
            >
              + Create FAQ Workflow
            </button>
          </div>

          <div className="space-y-1">
            {workflows.length === 0 ? (
              <p className="text-center text-sm text-gray-500 dark:text-gray-400 py-4">
                No FAQ workflows yet
              </p>
            ) : (
              workflows.map(wf => (
                <button
                  key={wf.id}
                  onClick={() => selectWorkflow(wf)}
                  className={`w-full rounded-lg px-3 py-2 text-left font-medium transition-colors ${
                    selectedWorkflow?.id === wf.id
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600'
                  }`}
                >
                  {wf.name}
                </button>
              ))
            )}
          </div>
        </div>

        {/* CANVAS */}
        <div className="flex-1 bg-gray-100 dark:bg-gray-900">
          {!selectedWorkflow ? (
            <div className="flex h-full items-center justify-center">
              <div className="rounded-xl border-2 border-dashed border-gray-300 bg-white p-12 text-center dark:border-gray-600 dark:bg-gray-800">
                <div className="text-5xl mb-4">📘</div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  No FAQ Workflow Selected
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Select or create a FAQ workflow from the left panel
                </p>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              onPaneClick={onPaneClick}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
              style={{ backgroundColor: '#f3f4f6', borderRadius: 0 }}
            >
              <Background color="#aaa" gap={16} />
              <Controls />
              <MiniMap />
            </ReactFlow>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="w-80 border-l border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-y-auto">
          <h2 className="mb-4 text-lg font-bold text-gray-900 dark:text-white">Properties</h2>

          {!selectedWorkflow ? (
            <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center dark:border-gray-600">
              <p className="text-sm text-gray-500 dark:text-gray-400">Select a workflow to edit nodes</p>
            </div>
          ) : !selectedNode ? (
            <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center dark:border-gray-600">
              <p className="text-sm text-gray-500 dark:text-gray-400">Select a node to edit</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                  FAQ Content
                </label>
                <textarea
                  value={editValue}
                  onChange={e => setEditValue(e.target.value)}
                  rows={8}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-900"
                  placeholder="Enter FAQ node content..."
                />
              </div>

              <button
                type="button"
                onClick={saveFaqNode}
                className="w-full rounded-lg bg-blue-500 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          )}

          <button
            onClick={addFaqNode}
            disabled={!selectedWorkflow}
            className="mt-4 w-full rounded-lg bg-green-500 px-4 py-2 font-medium text-white transition-colors hover:bg-green-600 disabled:opacity-50 dark:bg-green-600 dark:hover:bg-green-700"
          >
            ➕ Add FAQ Node
          </button>

          {selectedNode && (
  <button
    onClick={deleteFaqNode}
    className="w-full rounded-lg bg-red-500 px-4 py-2 text-white hover:bg-red-600"
  >
    🗑 Delete Node
  </button>
)}

{selectedEdgeId && (
  <button
    onClick={deleteFaqEdge}
    className="mt-2 w-full rounded-lg bg-red-400 px-4 py-2 text-white hover:bg-red-500"
  >
    🗑 Delete Edge
  </button>
)}

{selectedWorkflow && (
  <button
    onClick={deleteFaqWorkflow}
    className="mt-6 w-full rounded-lg bg-red-700 px-4 py-2 text-white hover:bg-red-800"
  >
    ❌ Delete Workflow
  </button>
)}

        </div>
      </div>
    </div>
  );
}

