'use client';

import { useEffect, useState } from 'react';
import { API_ENDPOINTS } from '@/config/api';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';

type TreeNode = {
  id: string;
  value: string;
};

export default function FAQEditor({ treeWorkflowId }: { treeWorkflowId: string }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [editValue, setEditValue] = useState('');

  /* ---------------- LOAD NODES ---------------- */

  useEffect(() => {
    if (!treeWorkflowId) return;

    fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${treeWorkflowId}/nodes`)
      .then(res => res.json())
      .then((data: TreeNode[]) => {
        if (!Array.isArray(data)) return;

        const rfNodes = data.map((n, index) => ({
          id: n.id,
          data: { label: n.value ?? '' },
          position: { x: 200, y: index * 120 },
        }));

        setNodes(rfNodes);
      });
  }, [treeWorkflowId]);

  /* ---------------- LOAD EDGES ---------------- */

  useEffect(() => {
    fetch(`${API_ENDPOINTS.TREE_WORKFLOWS}/${treeWorkflowId}/edges`)
      .then(res => res.json())
      .then(data => {
        if (!Array.isArray(data)) return;

        setEdges(
          data.map((e: any) => ({
            id: e.id,
            source: e.from_node_id,
            target: e.to_node_id,
          }))
        );
      });
  }, [treeWorkflowId]);

  /* ---------------- HANDLERS ---------------- */

  const onConnect = async (connection: Connection) => {
    if (!connection.source || !connection.target) return;

    const res = await fetch(API_ENDPOINTS.TREE_EDGES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tree_workflow_id: treeWorkflowId,
        from_node_id: connection.source,
        to_node_id: connection.target,
      }),
    });

    if (!res.ok) {
      console.error('Failed to create edge', await res.text());
      return;
    }

    setEdges(prev => addEdge(connection, prev));
  };

  const addNode = async () => {
    const res = await fetch(API_ENDPOINTS.TREE_NODES, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tree_workflow_id: treeWorkflowId,
        value: '',
      }),
    });

    if (!res.ok) {
      console.error('Failed to create node', await res.text());
      return;
    }

    const node = await res.json();

    // ReactFlow requires stable unique ids; if backend didn't return one, don't append.
    if (!node?.id || typeof node.id !== 'string') {
      console.error('Create node API did not return a valid id', node);
      return;
    }

    setNodes(prev => [
      ...prev,
      {
        id: node.id,
        data: { label: node.value ?? '' },
        position: { x: 200, y: prev.length * 120 },
      },
    ]);
  };

  const saveNode = async () => {
    if (!selectedNode) return;

    const res = await fetch(`${API_ENDPOINTS.TREE_NODES}/${selectedNode.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: editValue }),
    });

    if (!res.ok) {
      console.error('Failed to save node', await res.text());
      return;
    }

    setNodes(prev =>
      prev.map(n =>
        n.id === selectedNode.id
          ? { ...n, data: { label: editValue } }
          : n
      )
    );
  };

  /* ---------------- UI ---------------- */

  return (
    <div className="flex h-screen">
      {/* CANVAS */}
      <div className="flex-1 bg-gray-100">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onConnect={onConnect}
          onNodeClick={(_, node) => {
            setSelectedNode(node);
            setEditValue(node.data.label);
          }}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      {/* RIGHT PANEL */}
      <div className="w-80 border-l p-4 bg-white">
        <h3 className="font-bold mb-2">FAQ Node</h3>

        {selectedNode ? (
          <>
            <textarea
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              className="w-full border rounded p-2 mb-3"
              rows={6}
            />
            <button
              onClick={saveNode}
              className="w-full bg-blue-600 text-white py-2 rounded mb-2"
            >
              Save
            </button>
          </>
        ) : (
          <p>Select a node</p>
        )}

        <button
          onClick={addNode}
          className="w-full bg-green-600 text-white py-2 rounded"
        >
          ➕ Add FAQ Node
        </button>
      </div>
    </div>
  );
}
