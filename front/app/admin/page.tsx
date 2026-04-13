'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { fetchAdminPosts } from '@/lib/api/admin';
import { Post } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, Plus, Settings, Unlock, RefreshCw, PenTool } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

export default function AdminDashboard() {
  const [token, setToken] = useState<string>('');
  const [isAuth, setIsAuth] = useState(false);
  const [inputToken, setInputToken] = useState('');
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('admin_token');
    if (savedToken) {
      setToken(savedToken);
      verifyAndLoad(savedToken);
    }
  }, []);

  const verifyAndLoad = async (t: string) => {
    setLoading(true);
    try {
      const data = await fetchAdminPosts(t);
      setPosts(data);
      setIsAuth(true);
      localStorage.setItem('admin_token', t);
    } catch (err) {
      setIsAuth(false);
      localStorage.removeItem('admin_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputToken) {
      setToken(inputToken);
      verifyAndLoad(inputToken);
    }
  };

  if (!isAuth) {
    return (
      <PageTransition className="min-h-[70vh] flex flex-col items-center justify-center pt-24">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-sm"
        >
          <div className="bg-white/50 dark:bg-black/50 backdrop-blur-xl p-10 rounded-3xl border border-black/10 dark:border-white/10 shadow-2xl">
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 rounded-full bg-black/5 dark:bg-white/5 flex items-center justify-center text-foreground">
                <Settings className="w-8 h-8" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-center tracking-tight mb-2">Workspace Access</h2>
            <p className="text-sm text-center text-muted-foreground mb-8">Enter your master token to continue</p>
            
            <form onSubmit={handleLogin} className="space-y-4">
              <input
                type="password"
                placeholder="Secret Token..."
                value={inputToken}
                onChange={(e) => setInputToken(e.target.value)}
                className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all backdrop-blur-sm"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full relative flex items-center justify-center gap-2 py-3 bg-black dark:bg-white text-white dark:text-black rounded-xl font-medium hover:opacity-90 transition-opacity active:scale-[0.98] shadow-md"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Unlock className="w-4 h-4" />}
                {loading ? 'Authenticating...' : 'Enter Console'}
              </button>
            </form>
          </div>
        </motion.div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="pt-16 pb-24 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-16">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2 flex items-center gap-3">
            <Settings className="w-8 h-8 text-muted-foreground" />
            Console
          </h1>
          <p className="text-muted-foreground">Manage your articles and data.</p>
        </div>
        <Link
          href="/admin/posts/new"
          className="flex items-center gap-2 px-5 py-2.5 bg-black dark:bg-white text-white dark:text-black rounded-full font-medium shadow-sm hover:shadow-md hover:scale-105 transition-all active:scale-95"
        >
          <Plus className="w-4 h-4" />
          New Article
        </Link>
      </div>

      <AnimatePresence mode="popLayout">
        <motion.div className="space-y-4">
          {posts.map((post, idx) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: idx * 0.05 }}
              className="flex items-center justify-between p-5 rounded-2xl bg-white/60 dark:bg-black/40 backdrop-blur border border-black/10 dark:border-white/10 group transition-all hover:bg-white/80 dark:hover:bg-black/60"
            >
              <div className="flex-1 min-w-0 pr-4">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-lg font-semibold truncate text-foreground">
                    {post.title}
                  </h3>
                  {post.is_published ? (
                     <span className="shrink-0 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-medium border border-emerald-500/20">Live</span>
                  ) : (
                     <span className="shrink-0 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-xs font-mono font-medium border border-amber-500/20">Draft</span>
                  )}
                </div>
                <div className="text-sm text-muted-foreground font-mono truncate">
                  /{post.slug}
                </div>
              </div>
              <Link
                href={`/admin/posts/${post.id}`}
                className="shrink-0 flex items-center justify-center w-10 h-10 rounded-full border border-black/5 dark:border-white/10 bg-white dark:bg-black text-muted-foreground hover:text-foreground hover:border-black/20 dark:hover:border-white/20 transition-colors shadow-sm"
              >
                <Edit2 className="w-4 h-4" />
              </Link>
            </motion.div>
          ))}
          {posts.length === 0 && (
             <div className="text-center py-20 text-muted-foreground border border-dashed border-black/10 dark:border-white/10 rounded-3xl bg-black/5 dark:bg-white/5">
                No articles found. Time to craft some art.
             </div>
          )}
        </motion.div>
      </AnimatePresence>
    </PageTransition>
  );
}
