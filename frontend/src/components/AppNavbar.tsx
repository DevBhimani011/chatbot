'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { MessageCircle, Workflow, BookOpen, LogOut, User, Menu, X } from 'lucide-react';
import Link from 'next/link';

interface UserData {
  user_id: string;
  username: string;
  email: string;
  role: string;
}

export function AppNavbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserData | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout error:', err);
    }
    
    localStorage.removeItem('user');
    router.push('/login');
  };

  if (!user) return null;

  const isAdmin = user.role === 'admin';

  const navLinks = [
    { href: '/chat', label: 'Chat', icon: MessageCircle, show: true },
    { href: '/workflow', label: 'FAQ', icon: Workflow, show: isAdmin },
    { href: '/faq-workflows', label: 'Workflows', icon: Workflow, show: isAdmin },
    { href: '/knowledge-base', label: 'Knowledge Base', icon: BookOpen, show: isAdmin },
  ];

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm sticky top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/30">
              <MessageCircle size={20} />
            </div>
            <h1 className="text-lg font-bold text-gray-900">
              AI Chatbot
            </h1>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.filter(link => link.show).map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-colors ${
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon size={18} />
                  <span>{link.label}</span>
                </Link>
              );
            })}

            {/* User Info and Logout */}
            <div className="flex items-center gap-3 ml-4 pl-4 border-l border-gray-200">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100">
                <User size={16} className="text-gray-600" />
                <span className="text-sm font-medium text-gray-700">{user.username}</span>
                {isAdmin && (
                  <span className="ml-2 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                    Admin
                  </span>
                )}
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-red-50 hover:text-red-600 font-medium transition-colors"
              >
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col gap-2">
              {navLinks.filter(link => link.show).map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href;
                
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium ${
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon size={18} />
                    <span>{link.label}</span>
                  </Link>
                );
              })}

              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600">
                  <User size={16} />
                  <span>{user.username}</span>
                  {isAdmin && (
                    <span className="ml-auto px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                      Admin
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 font-medium"
                >
                  <LogOut size={18} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
