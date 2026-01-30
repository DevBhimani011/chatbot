'use client';

import { useParams } from 'next/navigation';
import { FAQWorkflowBuilder } from '../components';

export default function Page() {
  const params = useParams<{ id: string }>();
  return <FAQWorkflowBuilder initialWorkflowId={params.id} />;
}
