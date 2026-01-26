import { Handle, Position } from 'reactflow';
import { memo } from 'react';
import { clsx } from 'clsx';
import { MessageSquare } from 'lucide-react';

type WorkflowNodeProps = {
  data: {
    label: string;
    isSelected?: boolean;
  };
  isConnecting?: boolean;
  selected?: boolean;
};

export const WorkflowNode = memo(({ data, selected }: WorkflowNodeProps) => {
  return (
    <div
      className={clsx(
        "relative min-w-[180px] rounded-xl border-2 bg-white p-4 text-center text-sm font-medium transition-all duration-200 shadow-sm",
        selected
          ? "border-primary shadow-lg shadow-primary/10 ring-4 ring-primary/5"
          : "border-gray-200 hover:border-gray-300 hover:shadow-md"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-3 !w-3 !bg-gray-400 !border-2 !border-white transition-colors hover:!bg-primary"
      />

      <div className="flex flex-col items-center gap-2">
        <div className={clsx(
          "h-8 w-8 rounded-full flex items-center justify-center transition-colors",
          selected ? "bg-primary/10 text-primary" : "bg-gray-50 text-gray-400"
        )}>
          <MessageSquare size={16} />
        </div>
        <div className="text-gray-700 line-clamp-3 leading-relaxed">
          {data.label}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-3 !w-3 !bg-gray-400 !border-2 !border-white transition-colors hover:!bg-primary"
      />
    </div>
  );
});

WorkflowNode.displayName = 'WorkflowNode';
