// Centralized API configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
console.log('Loaded API_URL:', API_URL);
export const API_ENDPOINTS = {
  // Base URL
  BASE_URL: API_URL,
  
  // Workflows
  WORKFLOWS: `${API_URL}/workflows`,
  WORKFLOW_BY_ID: (id: string) => `${API_URL}/workflows/${id}`,
  WORKFLOW_NODES: (id: string) => `${API_URL}/workflows/${id}/nodes`,
  WORKFLOW_EDGES: (id: string) => `${API_URL}/workflows/${id}/edges`,

  // Nodes (for creating/updating)
  NODES: `${API_URL}/workflows/nodes`,
  NODE_BY_ID: (id: string) => `${API_URL}/workflows/nodes/${id}`,
  NODE_POSITION: (id: string) => `${API_URL}/workflows/nodes/${id}/position`,

  // Edges (for creating/deleting)
  EDGES: `${API_URL}/workflows/edges`,
  EDGE_BY_ID: (id: string) => `${API_URL}/workflows/edges/${id}`,

  // Chat
  CHAT: `${API_URL}/chat`,

  // Tree Workflows (FAQ)
  TREE_WORKFLOWS: `${API_URL}/tree-workflows`,
  TREE_NODES: `${API_URL}/tree-workflows/nodes`,
  TREE_EDGES: `${API_URL}/tree-workflows/edges`,

  // Documents
  DOCUMENTS_LIST: `${API_URL}/documents/list`,
  DOCUMENTS_UPLOAD: `${API_URL}/documents/upload-pdf`,
  DOCUMENTS_DELETE: (objectName: string) => `${API_URL}/documents/delete/${objectName}`,
  DOCUMENTS_DOWNLOAD: (objectName: string) => `${API_URL}/documents/download/${objectName}`,
};

export default API_URL;
