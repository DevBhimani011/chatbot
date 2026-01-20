// Centralized API configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const API_ENDPOINTS = {
  // Workflows
  WORKFLOWS: `${API_URL}/workflows`,
  WORKFLOW_BY_ID: (id: string) => `${API_URL}/workflows/${id}`,
  WORKFLOW_NODES: (id: string) => `${API_URL}/workflows/${id}/nodes`,

  // Nodes
  NODES: `${API_URL}/nodes`,
  NODE_BY_ID: (id: string) => `${API_URL}/nodes/${id}`,

  // Edges
  EDGES: `${API_URL}/edges`,
  EDGES_BY_WORKFLOW: (workflowId: string) =>
    `${API_URL}/edges/workflow/${workflowId}`,

  // Chat
  CHAT: `${API_URL}/chat/`,
};

export default API_URL;
