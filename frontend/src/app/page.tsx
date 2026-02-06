'use client';

import { motion } from 'framer-motion';
import { MessageCircle, Workflow, ArrowRight, Zap, Database, BookOpen, UserPlus } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-white to-white overflow-hidden selection:bg-primary/20">

      {/* Navigation */}
      <nav className="sticky top-0 z-50 glass-panel border-b-0 border-b-border/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2"
            >
              <div className="h-8 w-8 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/30">
                <MessageCircle size={18} />
              </div>
              <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
                Chatbot Workflow
              </h1>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-4"
            >
              <Link
                href="/login"
                className="text-sm font-medium text-gray-600 hover:text-primary transition-colors py-2"
              >
                Login
              </Link>
              <Link
                href="/signup"
                className="text-sm font-medium px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
              >
                Sign Up
              </Link>
            </motion.div>
          </div>
        </div>
      </nav>

      <main>
        {/* Hero Section */}
        <section className="relative pt-20 pb-32 overflow-hidden">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div
              variants={container}
              initial="hidden"
              animate="show"
              className="text-center max-w-3xl mx-auto"
            >
              <motion.div variants={item} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/5 text-primary text-xs font-semibold uppercase tracking-wide border border-primary/10 mb-8">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
                Next Gen AI Workflow
              </motion.div>

              <motion.h1 variants={item} className="text-5xl sm:text-7xl font-bold tracking-tight text-gray-900 mb-8">
                Build intelligent <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-indigo-400">conversational flows</span>
              </motion.h1>

              <motion.p variants={item} className="text-xl text-gray-600 mb-10 leading-relaxed">
                Design, test, and deploy powerful chatbot workflows with our visual editor.
                Seamlessly integrate logic and AI responses.
              </motion.p>

              <motion.div variants={item} className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  href="/login"
                  className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-xl bg-primary px-8 font-medium text-white shadow-xl shadow-primary/20 transition-all hover:bg-primary/90 hover:scale-[1.02]"
                >
                  <span className="mr-2">Get Started</span>
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  href="/signup"
                  className="group inline-flex h-12 items-center justify-center rounded-xl bg-white px-8 font-medium text-gray-700 shadow-lg shadow-gray-200/50 border border-gray-100 transition-all hover:bg-gray-50 hover:border-gray-200 hover:scale-[1.02]"
                >
                  <UserPlus size={18} className="mr-2 text-gray-500 group-hover:text-gray-700" />
                  Sign Up Free
                </Link>
              </motion.div>
            </motion.div>
          </div>

          {/* Background Decorative Elements */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full z-0 pointer-events-none">
            <div className="absolute top-20 left-[20%] w-72 h-72 bg-purple-200/30 rounded-full blur-3xl mix-blend-multiply filter animate-blob"></div>
            <div className="absolute top-20 right-[20%] w-72 h-72 bg-blue-200/30 rounded-full blur-3xl mix-blend-multiply filter animate-blob animation-delay-2000"></div>
            <div className="absolute -bottom-8 left-[30%] w-72 h-72 bg-indigo-200/30 rounded-full blur-3xl mix-blend-multiply filter animate-blob animation-delay-4000"></div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 bg-white/50 relative">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4"
            >
              {[
                {
                  icon: <MessageCircle className="w-6 h-6 text-blue-500" />,
                  title: "Natural Conversations",
                  desc: "Fluid interactions that feel human, powered by advanced language models."
                },
                {
                  icon: <Workflow className="w-6 h-6 text-indigo-500" />,
                  title: "Visual Builder",
                  desc: "Drag-and-drop interface to create complex logic paths without writing code."
                },
                {
                  icon: <BookOpen className="w-6 h-6 text-green-500" />,
                  title: "Knowledge Base",
                  desc: "Upload and manage documents to power intelligent, context-aware responses."
                },
                {
                  icon: <Database className="w-6 h-6 text-purple-500" />,
                  title: "Persistent Memory",
                  desc: "Remember context across sessions for more personalized user experiences."
                }
              ].map((feature, i) => (
                <div key={i} className="group p-8 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300">
                  <div className="mb-4 h-12 w-12 rounded-lg bg-gray-50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-500 leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </motion.div>
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-100 py-12 bg-white">
        <div className="mx-auto max-w-7xl px-4 text-center">
          <p className="text-gray-400 text-sm">© 2026 Chatbot Workflow. Designed for excellence.</p>
        </div>
      </footer>
    </div>
  );
}
