'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  MiniMap,
  NodeMouseHandler,
  useEdgesState,
  useNodesState,
  Node,
} from 'reactflow';
import type { Edge as RFEdge } from 'reactflow';
import 'reactflow/dist/style.css';
import { FileText } from 'lucide-react';

import { API_ENDPOINTS } from '@/config/api';
import { auth } from '@/lib/auth';
import { WorkflowHeader, WorkflowNode } from '../../workflow/components';
import { FAQWorkflowLeftPanel, FAQWorkflowRightPanel } from './';

const nodeTypes = { default: WorkflowNode };

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
    const res = await fetch(API_ENDPOINTS.TREE_WORKFLOWS, {
      headers: auth.getAuthHeaders(),
    });
    const data = await res.json();
    if (Array.isArray(data)) setWorkflows(data);
  }, []);

  const loadGraph = useCallback(
    async (workflowId: string) => {
      const [nodesRes, edgesRes] = await Promise.all([
        fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${workflowId}/nodes`, {
          headers: auth.getAuthHeaders(),
        }),
        fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${workflowId}/edges`, {
          headers: auth.getAuthHeaders(),
        }),
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
        headers: auth.getAuthHeaders(),
        body: JSON.stringify({ name }),
      });
      const wf = await res.json();
      if (!wf?.id) return;

      // create first empty FAQ node (mirrors normal workflow behavior)
      await fetch(API_ENDPOINTS.TREE_NODES, {
        method: 'POST',
        headers: auth.getAuthHeaders(),
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
      headers: auth.getAuthHeaders(),
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
      headers: auth.getAuthHeaders(),
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
        headers: auth.getAuthHeaders(),
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
        headers: auth.getAuthHeaders(),
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
      headers: auth.getAuthHeaders(),
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
      headers: auth.getAuthHeaders(),
    });

    setEdges(prev => prev.filter(e => e.id !== selectedEdgeId));
    setSelectedEdgeId(null);
  };

  const deleteFaqWorkflow = async () => {
    if (!selectedWorkflow) return;

    await fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${selectedWorkflow.id}`, {
      method: 'DELETE',
      headers: auth.getAuthHeaders(),
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
        <FAQWorkflowLeftPanel
          workflows={workflows}
          selectedWorkflow={selectedWorkflow}
          workflowName={name}
          isCreating={isCreating}
          onWorkflowNameChange={setName}
          onCreateWorkflow={createWorkflow}
          onSelectWorkflow={selectWorkflow}
        />

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
        <FAQWorkflowRightPanel
          selectedWorkflow={selectedWorkflow}
          selectedNode={selectedNode}
          selectedEdgeId={selectedEdgeId}
          editValue={editValue}
          onEditValueChange={setEditValue}
          onSaveNode={saveFaqNode}
          onAddNode={addFaqNode}
          onDeleteNode={deleteFaqNode}
          onDeleteEdge={deleteFaqEdge}
          onDeleteWorkflow={deleteFaqWorkflow}
        />
      </div>
    </div>
  );
}
