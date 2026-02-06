'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FAQWorkflowBuilder } from './components';

export default function FAQWorkflowsPage() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in and is admin
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    
    const user = JSON.parse(userData);
    if (user.role !== 'admin') {
      router.push('/chat'); // Redirect non-admins to chat
      return;
    }
  }, [router]);

  return <FAQWorkflowBuilder />;
}
