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
  NodeDragHandler,
  NodeMouseHandler,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import type { Edge as RFEdge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Plus, Trash2, Save, Layout, FileText, Settings } from 'lucide-react';

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
  position_x?: number;
  position_y?: number;
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
          position: {
            x: n.position_x ?? 250,
            y: n.position_y ?? index * 150
          },
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
        selected: true,
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
    <div className="flex h-screen flex-col bg-gray-50">
      <WorkflowHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANEL */}
        <div className="w-72 border-r border-gray-200 bg-gray-50/50 p-6 shadow-sm flex flex-col h-full">
          <h2 className="mb-6 text-sm font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
            <Layout size={16} />
            FAQ Workflows
          </h2>

          <div className="mb-4 flex flex-col gap-3">
            <input
              placeholder="New workflow name..."
              value={name}
              onChange={e => setName(e.target.value)}
              disabled={isCreating}
              className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-green-500 focus:ring-2 focus:ring-green-100 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={createWorkflow}
              disabled={isCreating || !name.trim()}
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
              workflows.map(wf => (
                <button
                  key={wf.id}
                  onClick={() => selectWorkflow(wf)}
                  className={`w-full rounded-lg px-4 py-2.5 text-left text-sm font-medium transition-all ${selectedWorkflow?.id === wf.id
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

        {/* CANVAS */}
        <div className="flex-1 bg-gray-50">
          {!selectedWorkflow ? (
            <div className="flex h-full items-center justify-center">
              <div className="rounded-xl border-2 border-dashed border-gray-200 bg-white p-12 text-center shadow-sm">
                <div className="mx-auto h-12 w-12 rounded-full bg-gray-50 flex items-center justify-center text-gray-400 mb-4">
                  <FileText size={24} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">
                  No FAQ Workflow Selected
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Select or create a workflow from the left sidebar
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
              onNodeDragStop={onNodeDragStop}
              nodeTypes={nodeTypes}
              fitView
              className="bg-gray-50"
            >
              <Background color="#cbd5e1" gap={16} />
              <Controls />
              <MiniMap nodeColor={() => '#e2e8f0'} maskColor="rgba(241, 245, 249, 0.7)" />
            </ReactFlow>
          )}
        </div>

        {/* RIGHT PANEL - Properties */}
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  FAQ Content
                </label>
                <textarea
                  value={editValue}
                  onChange={e => setEditValue(e.target.value)}
                  rows={8}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition-all placeholder:text-gray-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
                  placeholder="Enter content..."
                />
              </div>

              <button
                type="button"
                onClick={saveFaqNode}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/20 transition-all hover:bg-blue-700 hover:shadow-blue-500/30"
              >
                <Save size={16} />
                Save Changes
              </button>
            </div>
          )}

          <div className="mt-auto pt-6 border-t border-gray-100 space-y-3">
            <button
              onClick={addFaqNode}
              disabled={!selectedWorkflow}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-green-500/20 transition-all hover:bg-green-700 disabled:opacity-50 disabled:shadow-none"
            >
              <Plus size={16} />
              Add FAQ Node
            </button>

            {selectedNode && (
              <button
                onClick={deleteFaqNode}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-medium text-red-600 transition-all hover:bg-red-100 border border-transparent hover:border-red-200"
              >
                <Trash2 size={16} />
                Delete Node
              </button>
            )}

            {selectedEdgeId && (
              <button
                onClick={deleteFaqEdge}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-50 px-4 py-2.5 text-sm font-medium text-red-600 transition-all hover:bg-red-100 border border-transparent hover:border-red-200"
              >
                <Trash2 size={16} />
                Delete Connection
              </button>
            )}

            {selectedWorkflow && (
              <button
                onClick={deleteFaqWorkflow}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gray-50 px-4 py-2.5 text-sm font-medium text-gray-500 transition-all hover:bg-gray-100 hover:text-red-700"
              >
                <Trash2 size={16} />
                Delete Workflow
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
