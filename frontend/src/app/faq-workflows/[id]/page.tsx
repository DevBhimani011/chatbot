'use client';

import { useParams } from 'next/navigation';
import FAQWorkflowBuilder from '../FAQWorkflowBuilder';

export default function Page() {
  const params = useParams<{ id: string }>();
  return <FAQWorkflowBuilder initialWorkflowId={params.id} />;
}
