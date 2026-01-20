# Quick Reference Guide - Using the New Structure

## How to Use API Endpoints

### In any component:

```typescript
import { API_ENDPOINTS } from '@/config/api';

// Fetch all workflows
const res = await fetch(API_ENDPOINTS.WORKFLOWS);

// Fetch specific workflow nodes
const res = await fetch(API_ENDPOINTS.WORKFLOW_NODES(workflowId));

// Create a new node
const res = await fetch(API_ENDPOINTS.NODES, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ workflow_id, value }),
});

// Update a node
const res = await fetch(API_ENDPOINTS.NODE_BY_ID(nodeId), {
  method: 'PATCH',
  body: JSON.stringify({ value }),
});

// Chat
const res = await fetch(API_ENDPOINTS.CHAT, {
  method: 'POST',
  body: JSON.stringify({ message }),
});
```

## How to Import Workflow Components

```typescript
import {
  WorkflowNode,
  WorkflowLeftPanel,
  WorkflowCanvas,
  WorkflowRightPanel,
  WorkflowHeader,
} from '@/components/Workflow';
```

## How to Change API URL

1. Open `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://new-api-host:port
```

2. Restart dev server (hot reload will automatically pick up changes)

No code changes needed!

## Adding New API Endpoints

1. Edit `src/config/api.ts`:
```typescript
export const API_ENDPOINTS = {
  // ... existing endpoints
  
  // New endpoint
  NEW_FEATURE: `${API_URL}/new-feature`,
  NEW_FEATURE_BY_ID: (id: string) => `${API_URL}/new-feature/${id}`,
};
```

2. Use in components:
```typescript
import { API_ENDPOINTS } from '@/config/api';

await fetch(API_ENDPOINTS.NEW_FEATURE);
```

## Creating New Components

1. Create file in `src/components/YourComponent/`:
   - `YourComponent.tsx` - Main component
   - (optional) `index.ts` - If creating multiple related components

2. Export from index file:
```typescript
export { YourComponent } from './YourComponent';
```

3. Import anywhere using path alias:
```typescript
import { YourComponent } from '@/components/YourComponent';
```

## File Location Best Practices

- **Page components**: `src/app/[feature]/page.tsx`
- **Reusable components**: `src/components/[FeatureName]/Component.tsx`
- **Configuration**: `src/config/`
- **Utilities**: `src/lib/` (if needed)
- **Types/Interfaces**: In component files or `src/types/` (if many)

## Environment Variables

Available in browser with `NEXT_PUBLIC_` prefix:
- `process.env.NEXT_PUBLIC_API_URL`

Only on server with any prefix:
- `process.env.NEXT_PUBLIC_API_URL`

Add more as needed in `.env.local`.
