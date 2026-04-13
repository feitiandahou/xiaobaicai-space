'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { createPost, PostCreateData } from '@/lib/api/admin';
import { motion } from 'framer-motion';
import { Save, ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export default function NewPost() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [isError, setIsError] = useState('');
  
  const [formData, setFormData] = useState<PostCreateData>({
    title: '',
    slug: '',
    summary: '',
    content: '',
    cover_image: '',
    is_published: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsError('');
    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token') || '';
      await createPost(token, formData);
      router.push('/admin');
    } catch (err) {
      setIsError((err as Error).message);
      setLoading(false);
    }
  };

  return (
    <PageTransition className="pt-16 pb-24 max-w-4xl mx-auto relative">
      <Link
        href="/admin"
        className="group mb-8 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-1" />
        Back to Console
      </Link>

      <div className="mb-12">
        <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2">Create New Piece</h1>
        <p className="text-muted-foreground">Craft your next beautiful article.</p>
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
               className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all font-serif text-lg"
               placeholder="A poetic title..."
             />
          </div>
          
          <div className="space-y-2">
             <label className="text-sm font-medium tracking-tight">Slug</label>
             <input
               required
               value={formData.slug}
               onChange={(e) => setFormData({...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})}
               className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all font-mono text-muted-foreground"
               placeholder="a-poetic-title"
             />
          </div>
        </div>

        <div className="space-y-2">
           <label className="text-sm font-medium tracking-tight">Summary (Optional)</label>
           <textarea
             value={formData.summary}
             onChange={(e) => setFormData({...formData, summary: e.target.value})}
             className="w-full px-4 py-3 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-2xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all min-h-[80px] resize-y"
             placeholder="A short brief of what is to come..."
           />
        </div>

        <div className="space-y-2">
           <label className="text-sm font-medium tracking-tight flex items-center justify-between">
             Content
             <span className="text-xs text-muted-foreground bg-black/5 dark:bg-white/5 px-2 py-1 rounded-md">Markdown supported</span>
           </label>
           <textarea
             required
             value={formData.content}
             onChange={(e) => setFormData({...formData, content: e.target.value})}
             className="w-full px-5 py-4 bg-white/70 dark:bg-black/70 border border-black/10 dark:border-white/20 rounded-3xl focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent transition-all min-h-[40vh] resize-y font-mono text-sm leading-loose shadow-inner"
             placeholder="# Start writing..."
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
            {loading ? 'Saving...' : 'Save Art piece'}
          </button>
        </div>
      </form>
    </PageTransition>
  );
}
