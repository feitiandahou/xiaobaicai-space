'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { type Post } from '@/lib/api';
import { fetchAdminDashboard, fetchAdminPosts, loginAdmin, type AdminDashboard } from '@/lib/api/admin';
import { AnimatePresence, motion } from 'framer-motion';
import { Edit2, FolderTree, LogOut, Plus, RefreshCw, Settings, ShieldCheck, Tags } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function AdminDashboard() {
  const [token, setToken] = useState('');
  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');
  const [isAuth, setIsAuth] = useState(false);
  const [posts, setPosts] = useState<Post[]>([]);
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const savedToken = localStorage.getItem('admin_access_token');
    if (savedToken) {
      setToken(savedToken);
      verifyAndLoad(savedToken, false);
    }
  }, []);

  const verifyAndLoad = async (authToken: string, saveToken: boolean) => {
    setLoading(true);
    setError('');
    try {
      const [postPayload, dashboardPayload] = await Promise.all([
        fetchAdminPosts(authToken),
        fetchAdminDashboard(authToken),
      ]);
      setPosts(postPayload.data);
      setDashboard(dashboardPayload);
      setIsAuth(true);
      if (saveToken) {
        localStorage.setItem('admin_access_token', authToken);
      }
    } catch {
      setIsAuth(false);
      localStorage.removeItem('admin_access_token');
      localStorage.removeItem('admin_user_id');
      setError('Authentication failed or your account has no admin permission.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await loginAdmin(account, password);
      if (result.user.role !== 'admin') {
        throw new Error('Current account is not admin.');
      }
      setToken(result.access_token);
      localStorage.setItem('admin_user_id', String(result.user.id));
      await verifyAndLoad(result.access_token, true);
    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_access_token');
    localStorage.removeItem('admin_user_id');
    setToken('');
    setIsAuth(false);
    setPosts([]);
    setDashboard(null);
    setAccount('');
    setPassword('');
  };

  if (!isAuth) {
    return (
      <PageTransition className="min-h-[70vh] flex flex-col items-center justify-center pt-12 md:pt-20">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          <div className="card-surface p-8 md:p-10 rounded-3xl">
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 rounded-full bg-black/5 flex items-center justify-center text-ink">
                <Settings className="w-8 h-8" />
              </div>
            </div>
            <h2 className="text-4xl text-center leading-none mb-2">Admin Console</h2>
            <p className="text-sm text-center text-ink-muted mb-8">Use your backend account to sign in.</p>

            {error ? (
              <div className="mb-4 rounded-xl border border-[#a6502e]/30 bg-[#a6502e]/10 p-3 text-sm text-[#7d3d22]">
                {error}
              </div>
            ) : null}
            
            <form onSubmit={handleLogin} className="space-y-4">
              <input
                type="text"
                required
                autoComplete="username"
                placeholder="Username or email"
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                className="w-full px-4 py-3 bg-white/70 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
              />
              <input
                type="password"
                required
                autoComplete="current-password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white/70 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full relative flex items-center justify-center gap-2 py-3 bg-[#1f1d1a] text-[#fbf8f1] rounded-xl font-medium hover:opacity-90 transition-opacity"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                {loading ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
          </div>
        </motion.div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="pt-8 pb-24 max-w-6xl mx-auto">
      <div className="card-surface rounded-4xl p-6 md:p-8 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-5xl leading-none">Control Room</h1>
            <p className="text-ink-muted mt-2">Token active. Connected to backend API.</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => verifyAndLoad(token, false)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-line text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-line text-sm text-[#7d3d22]"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>

        {dashboard ? (
          <div className="mt-5 grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="rounded-2xl bg-white/65 border border-line p-4">
              <div className="text-xs text-ink-muted uppercase">Total Posts</div>
              <div className="text-3xl leading-none mt-2">{dashboard.total_posts}</div>
            </div>
            <div className="rounded-2xl bg-white/65 border border-line p-4">
              <div className="text-xs text-ink-muted uppercase">Published</div>
              <div className="text-3xl leading-none mt-2">{dashboard.published_posts}</div>
            </div>
            <div className="rounded-2xl bg-white/65 border border-line p-4">
              <div className="text-xs text-ink-muted uppercase">Draft</div>
              <div className="text-3xl leading-none mt-2">{dashboard.draft_posts}</div>
            </div>
            <div className="rounded-2xl bg-white/65 border border-line p-4">
              <div className="text-xs text-ink-muted uppercase">7-Day New</div>
              <div className="text-3xl leading-none mt-2">{dashboard.posts_created_last_7_days}</div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl leading-none">Post Library</h2>
          <p className="text-ink-muted mt-1">Manage drafts and published content.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/admin/categories"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full border border-line text-sm text-ink-muted hover:text-ink"
          >
            <FolderTree className="w-4 h-4" />
            Categories
          </Link>
          <Link
            href="/admin/tags"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full border border-line text-sm text-ink-muted hover:text-ink"
          >
            <Tags className="w-4 h-4" />
            Tags
          </Link>
          <Link
            href="/admin/settings"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full border border-line text-sm text-ink-muted hover:text-ink"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>
          <Link
            href="/admin/posts/new"
            className="flex items-center gap-2 px-5 py-2.5 bg-[#1f1d1a] text-[#fbf8f1] rounded-full font-medium"
          >
            <Plus className="w-4 h-4" />
            New Article
          </Link>
        </div>
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
              className="flex items-center justify-between p-5 rounded-2xl bg-white/70 border border-line group transition-all hover:bg-white/90"
            >
              <div className="flex-1 min-w-0 pr-4">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-lg font-semibold truncate text-ink">
                    {post.title}
                  </h3>
                  {post.status === 1 ? (
                     <span className="shrink-0 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 text-xs font-mono font-medium border border-emerald-500/20">Live</span>
                  ) : post.status === 2 ? (
                     <span className="shrink-0 px-2 py-0.5 rounded-full bg-stone-500/10 text-stone-700 text-xs font-mono font-medium border border-stone-500/20">Archived</span>
                  ) : (
                     <span className="shrink-0 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 text-xs font-mono font-medium border border-amber-500/20">Draft</span>
                  )}
                </div>
                <div className="text-sm text-ink-muted font-mono truncate">
                  /{post.slug}
                </div>
                {post.tag_ids?.length ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {post.tag_ids.map((tagId) => (
                      <span
                        key={tagId}
                        className="px-2 py-1 rounded-full bg-black/5 text-xs text-ink-muted"
                      >
                        tag:{tagId}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
              <Link
                href={`/admin/posts/${post.id}`}
                className="shrink-0 flex items-center justify-center w-10 h-10 rounded-full border border-line bg-white text-ink-muted hover:text-ink transition-colors"
              >
                <Edit2 className="w-4 h-4" />
              </Link>
            </motion.div>
          ))}
          {posts.length === 0 && (
             <div className="text-center py-20 text-ink-muted border border-dashed border-line rounded-3xl bg-white/50">
                No posts found yet.
             </div>
          )}
        </motion.div>
      </AnimatePresence>
    </PageTransition>
  );
}
