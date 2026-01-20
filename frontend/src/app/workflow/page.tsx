'use client';

import { useEffect, useState, useCallback } from 'react';
import { Node, Edge, addEdge, Connection, useNodesState, useEdgesState, NodeMouseHandler } from 'reactflow';
import 'reactflow/dist/style.css';
import {
  WorkflowNode,
  WorkflowLeftPanel,
  WorkflowCanvas,
  WorkflowRightPanel,
  WorkflowHeader,
} from '@/components/Workflow';
import { API_ENDPOINTS } from '@/config/api';

type Workflow = {
  id: string;
  name: string;
};

type NodeData = {
  id: string;
  value: string;
};

type BackendEdge = {
  id: string;
  from_node_id: string;
  to_node_id: string;
};

// Define nodeTypes outside component to prevent warnings
const nodeTypes = { default: WorkflowNode };

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [backendNodes, setBackendNodes] = useState<NodeData[]>([]);
  const [backendEdges, setBackendEdges] = useState<BackendEdge[]>([]);
  const [name, setName] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const selectedNode = backendNodes.find(n => n.id === selectedNodeId);

  /* -------------------- API CALLS -------------------- */

  const fetchWorkflows = async () => {
    const res = await fetch(API_ENDPOINTS.WORKFLOWS);
    const data = await res.json();
    setWorkflows(data);
  };

  const fetchNodes = async (workflowId: string) => {
    try {
      const res = await fetch(API_ENDPOINTS.WORKFLOW_NODES(workflowId));
      const data = await res.json();
      setBackendNodes(data);

      // Fetch edges from backend using the new endpoint
      let edgesData: BackendEdge[] = [];
      try {
        const edgesRes = await fetch(
          API_ENDPOINTS.EDGES_BY_WORKFLOW(workflowId)
        );
        if (edgesRes.ok) {
          const edgesResponseData = await edgesRes.json();
          if (Array.isArray(edgesResponseData)) {
            edgesData = edgesResponseData;
          }
        }
      } catch (error) {
      }
      setBackendEdges(edgesData);

      // Convert to React Flow format
      const rfNodes: Node[] = data.map((node: NodeData, index: number) => {
        const isSelected = selectedNodeId === node.id;
        return {
          id: node.id,
          data: { label: node.value || '(empty)', isSelected },
          position: { x: 250, y: index * 150 },
          type: 'default',
          selected: isSelected,
          style: {
            background: isSelected ? '#dbeafe' : '#ffffff',
            border: isSelected ? '3px solid #3b82f6' : '2px solid #d1d5db',
            borderRadius: '8px',
            padding: '12px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
          },
        };
      });

      // Convert edges to React Flow format
      const rfEdges: Edge[] = edgesData.map((edge: BackendEdge) => ({
        id: edge.id,
        source: edge.from_node_id,
        target: edge.to_node_id,
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
    } catch (error) {
      console.error('Error fetching nodes:', error);
    }
  };

  const createWorkflow = async () => {
    if (!name.trim()) return;

    const res = await fetch(API_ENDPOINTS.WORKFLOWS, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });

    const workflow = await res.json();

    // create first empty card
    await fetch(API_ENDPOINTS.NODES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow_id: workflow.id,
        value: '',
      }),
    });

    setName('');
    fetchWorkflows();
  };

  const selectWorkflow = (wf: Workflow) => {
    setSelectedWorkflow(wf);
    setSelectedNodeId(null);
    fetchNodes(wf.id);
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

    const newNode = await res.json();

    // Add new node to React Flow
    const newRFNode: Node = {
      id: newNode.id,
      data: { label: '' },
      position: { x: 250, y: backendNodes.length * 150 },
      type: 'default',
      style: {
        background: '#ffffff',
        border: '2px solid #d1d5db',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
      },
    };

    setNodes(prev => [...prev, newRFNode]);
    setBackendNodes(prev => [...prev, newNode]);

    // Create edge from last node to new node
    if (backendNodes.length > 0) {
      const lastNode = backendNodes[backendNodes.length - 1];
      try {
        const edgeRes = await fetch(API_ENDPOINTS.EDGES, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workflow_id: selectedWorkflow.id,
            from_node_id: lastNode.id,
            to_node_id: newNode.id,
          }),
        });

        if (edgeRes.ok) {
          const newEdge = await edgeRes.json();
          const edge: Edge = {
            id: newEdge.id || `${lastNode.id}-${newNode.id}`,
            source: lastNode.id,
            target: newNode.id,
          };
          setEdges(prev => [...prev, edge]);
          setBackendEdges(prev => [...prev, newEdge]);
        }
      } catch (error) {
        console.error('Error creating edge:', error);
      }
    }

    setSelectedNodeId(newNode.id);
  };

  const saveNode = async () => {
    if (!selectedNode || !selectedWorkflow) return;

    await fetch(API_ENDPOINTS.NODE_BY_ID(selectedNode.id), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        value: editValue,
      }),
    });

    // Update only the changed node without refetching all nodes
    setBackendNodes(prevNodes =>
      prevNodes.map(node =>
        node.id === selectedNode.id ? { ...node, value: editValue } : node
      )
    );

    // Update React Flow nodes
    setNodes(prevNodes =>
      prevNodes.map(node =>
        node.id === selectedNode.id
          ? { ...node, data: { ...node.data, label: editValue || '(empty)' } }
          : node
      )
    );
  };

  /* -------------------- EFFECTS -------------------- */

  useEffect(() => {
    fetchWorkflows();
  }, []);

  useEffect(() => {
    if (selectedNode) {
      setEditValue(selectedNode.value || '');
    }
  }, [selectedNodeId, selectedNode]);

  // Update node styles when selectedNodeId changes
  useEffect(() => {
    setNodes(prevNodes =>
      prevNodes.map(node => ({
        ...node,
        selected: node.id === selectedNodeId,
        style: {
          ...node.style,
          background: node.id === selectedNodeId ? '#dbeafe' : '#ffffff',
          border: node.id === selectedNodeId ? '3px solid #3b82f6' : '2px solid #d1d5db',
        },
      }))
    );
  }, [selectedNodeId, setNodes]);

  const deleteWorkflow = async () => {
    if (!selectedWorkflow) return;

    const ok = window.confirm(
      `Are you sure you want to delete workflow "${selectedWorkflow.name}"?`
    );

    if (!ok) return;

    await fetch(API_ENDPOINTS.WORKFLOW_BY_ID(selectedWorkflow.id), {
      method: 'DELETE',
    });

    // reset UI state
    setSelectedWorkflow(null);
    setSelectedNodeId(null);
    setBackendNodes([]);
    setBackendEdges([]);
    setEditValue('');
    setNodes([]);
    setEdges([]);

    fetchWorkflows();
  };

  // Handle node click to select it
  const handleNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNodeId(node.id);
  }, [setSelectedNodeId]);

  // Handle connection between nodes
  const handleConnect = useCallback(
    async (connection: Connection) => {
      if (!selectedWorkflow || !connection.source || !connection.target) return;

      try {
        // Create edge in backend
        const edgeRes = await fetch(API_ENDPOINTS.EDGES, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workflow_id: selectedWorkflow.id,
            from_node_id: connection.source,
            to_node_id: connection.target,
          }),
        });

        if (edgeRes.ok) {
          const newEdge = await edgeRes.json();
          // Add the edge to backend edges state
          setBackendEdges(prev => [...prev, newEdge]);
          
          // Add edge to React Flow with proper ID
          const edge: Edge = {
            id: newEdge.id || `${connection.source}-${connection.target}`,
            source: connection.source,
            target: connection.target,
          };
          setEdges(eds => addEdge(edge, eds));
        }
      } catch (error) {
        console.error('Error creating edge:', error);
      }
    },
    [selectedWorkflow, setEdges]
  );

  // Handle pane click to deselect
  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  /* -------------------- UI -------------------- */

  return (
    <div className="flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <WorkflowHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANEL - Workflows List */}
        <WorkflowLeftPanel
          workflows={workflows}
          selectedWorkflow={selectedWorkflow}
          onSelectWorkflow={selectWorkflow}
          onRefresh={fetchWorkflows}
        />

        {/* CANVAS - React Flow */}
        <WorkflowCanvas
          selectedWorkflow={selectedWorkflow}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          onConnect={handleConnect}
          nodeTypes={nodeTypes}
          backendNodes={backendNodes}
        />

        {/* RIGHT PANEL - Properties */}
        <WorkflowRightPanel
          selectedNode={selectedNode}
          editValue={editValue}
          onEditValueChange={setEditValue}
          onSaveNode={saveNode}
          onAddNextCard={addNextCard}
          onDeleteWorkflow={deleteWorkflow}
          selectedWorkflow={selectedWorkflow}
        />
      </div>
    </div>
  );
}
