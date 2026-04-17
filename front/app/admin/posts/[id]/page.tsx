'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { updatePost, deletePost, PostUpdateData, fetchAdminPosts } from '@/lib/api/admin';
import { Post } from '@/lib/api';
import { motion } from 'framer-motion';
import { Save, ArrowLeft, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

function parseTags(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(',')
        .map((tag) => tag.trim().toLowerCase())
        .filter(Boolean)
    )
  );
}

export default function EditPost() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [initLoading, setInitLoading] = useState(true);
  const [isError, setIsError] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  
  const [formData, setFormData] = useState<PostUpdateData>({
    title: '',
    slug: '',
    summary: '',
    content: '',
    cover_image: '',
    tags: [],
    is_published: false,
  });

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (!token) return router.push('/admin');

    fetchAdminPosts(token).then((data) => {
      const p = data.find(post => post.id === id);
      if (p) {
        setFormData({
          title: p.title,
          slug: p.slug,
          summary: p.summary,
          content: p.content || '',
          cover_image: p.cover_image,
          tags: p.tags || [],
          is_published: p.is_published || false,
        });
        setTagsInput((p.tags || []).join(', '));
      }
      setInitLoading(false);
    });
  }, [id, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsError('');
    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token') || '';
      await updatePost(token, id, {
        ...formData,
        tags: parseTags(tagsInput),
      });
      router.push('/admin');
    } catch (err) {
      setIsError((err as Error).message);
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you certain you want to delete this piece of art?')) return;
    setDeleting(true);
    try {
      const token = localStorage.getItem('admin_token') || '';
      await deletePost(token, id);
      router.push('/admin');
    } catch (err) {
      setIsError((err as Error).message);
      setDeleting(false);
    }
  };

  if (initLoading) {
    return (
      <PageTransition className="pt-32 flex justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </PageTransition>
    );
  }

  return (
    <PageTransition className="pt-16 pb-24 max-w-4xl mx-auto relative">
      <Link
        href="/admin"
        className="group mb-8 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-1" />
        Back to Console
      </Link>

      <div className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2">Edit Piece</h1>
          <p className="text-muted-foreground font-mono text-sm tracking-wide">ID :: {id}</p>
        </div>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          className="p-3 text-rose-500 rounded-full hover:bg-rose-500/10 dark:hover:bg-rose-500/20 transition-colors"
          title="Delete Article"
        >
          {deleting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Trash2 className="w-5 h-5" />}
        </button>
      </div>

      {isError && (
        <div className="p-4 mb-8 bg-rose-500/10 text-rose-600 rounded-xl border border-rose-500/20 font-medium">
          {isError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-2">
             <label className="text-sm font-medium tracking-tight">Title</label>
             <input
               required
               value={formData.title}
               onChange={(e) => setFormData({...formData, title: e.target.value})}
               className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all font-serif text-lg shadow-sm"
               placeholder="A poetic title..."
             />
          </div>
          
          <div className="space-y-2">
             <label className="text-sm font-medium tracking-tight">Slug</label>
             <input
               required
               value={formData.slug}
               onChange={(e) => setFormData({...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})}
               className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all font-mono text-muted-foreground shadow-sm"
               placeholder="a-poetic-title"
             />
          </div>
        </div>

        <div className="space-y-2">
           <label className="text-sm font-medium tracking-tight">Summary</label>
           <textarea
             value={formData.summary}
             onChange={(e) => setFormData({...formData, summary: e.target.value})}
             className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all min-h-20 resize-y shadow-sm"
           />
        </div>

          <div className="space-y-2">
            <label className="text-sm font-medium tracking-tight">Tags</label>
            <input
             value={tagsInput}
             onChange={(e) => setTagsInput(e.target.value)}
             className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all shadow-sm"
             placeholder="react, fastapi, supabase"
            />
            <p className="text-xs text-muted-foreground">Use commas to separate tags.</p>
          </div>

        <div className="space-y-2">
           <label className="text-sm font-medium tracking-tight">Content</label>
           <textarea
             required
             value={formData.content}
             onChange={(e) => setFormData({...formData, content: e.target.value})}
             className="w-full px-5 py-4 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-3xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all min-h-[40vh] resize-y font-mono text-sm leading-loose shadow-inner"
           />
        </div>

        <div className="flex items-center justify-between py-6 border-t border-black/5 dark:border-white/10">
          <label className="flex items-center gap-3 cursor-pointer group">
             <div className={cn(
               "relative w-12 h-6 rounded-full transition-colors",
               formData.is_published ? "bg-emerald-500" : "bg-black/20 dark:bg-white/20"
             )}>
               <motion.div 
                 layout
                 className="absolute left-1 flex items-center justify-center w-4 h-4 mt-1 bg-white rounded-full shadow-md"
                 animate={{ x: formData.is_published ? 24 : 0 }}
                 transition={{ type: "spring", stiffness: 500, damping: 30 }}
               />
             </div>
             <span className="text-sm font-medium tracking-wide">Publish immediately</span>
             <input
               type="checkbox"
               className="hidden"
               checked={formData.is_published}
               onChange={(e) => setFormData({...formData, is_published: e.target.checked})}
             />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-8 py-3.5 bg-black dark:bg-white text-white dark:text-black rounded-full font-medium shadow-md hover:shadow-lg hover:scale-105 active:scale-95 transition-all text-sm tracking-wide"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {loading ? 'Updating...' : 'Update Art piece'}
          </button>
        </div>
      </form>
    </PageTransition>
  );
}
