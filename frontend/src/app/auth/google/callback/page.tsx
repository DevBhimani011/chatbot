'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { XCircle } from 'lucide-react';

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = () => {
      try {
        // Extract user data from query parameters
        const user_id = searchParams.get('user_id');
        const username = searchParams.get('username');
        const email = searchParams.get('email');
        const role = searchParams.get('role');
        const access_token = searchParams.get('access_token');
        const token_type = searchParams.get('token_type');

        // Validate required fields
        if (!user_id || !email || !access_token) {
          throw new Error('Missing required authentication data');
        }

        // Construct user object
        const userData = {
          user_id,
          username: username || email.split('@')[0],
          email,
          role: role || 'user',
          access_token,
          token_type: token_type || 'bearer'
        };

        // Store in localStorage
        localStorage.setItem('user', JSON.stringify(userData));

        // Replace current page with chat (no back navigation)
        router.replace('/chat');

      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'Authentication failed. Please try again.');

        // Redirect to login after delay
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  // Only show UI if there's an error, otherwise nothing (redirect happens instantly)
  if (!error) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md w-full">
        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Authentication Failed
        </h2>
        <p className="text-gray-600">{error}</p>
      </div>
    </div>
  );
}
