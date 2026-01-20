import { Handle, Position } from 'reactflow';

type WorkflowNodeProps = {
  data: {
    label: string;
    isSelected?: boolean;
  };
  isConnecting?: boolean;
  selected?: boolean;
};

export function WorkflowNode({ data, selected }: WorkflowNodeProps) {
  return (
    <div
      style={{
        background: selected ? '#dbeafe' : '#ffffff',
        border: selected ? '3px solid #3b82f6' : '2px solid #d1d5db',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        minWidth: '150px',
        textAlign: 'center',
        wordWrap: 'break-word',
      }}
    >
      <Handle type="target" position={Position.Top} />
      <div>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
