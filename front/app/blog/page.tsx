'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { fetchPosts, Post } from '@/lib/api';
import { useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, Heart } from 'lucide-react';

export default function BlogLandingPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts().then((res) => {
      setPosts(res);
      setLoading(false);
    });
  }, []);

  return (
    <PageTransition className="max-w-3xl mx-auto pt-16">
      <div className="mb-16">
        <h1 className="text-4xl font-bold tracking-tight mb-4">My Writing</h1>
        <p className="text-muted-foreground text-lg">
          Insights on programming, design, and navigating the digital world.
        </p>
      </div>

      <div className="space-y-6">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-black/5 dark:bg-white/5 h-32 rounded-2xl w-full" />
          ))
        ) : posts.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground border border-dashed rounded-3xl">
            No articles published yet.
          </div>
        ) : (
          posts.map((post, idx) => (
            <Link key={post.id} href={`/blog/${post.slug}`}>
              <motion.article
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className="group relative flex flex-col items-start justify-between p-6 rounded-3xl bg-white/40 dark:bg-black/40 backdrop-blur-md border border-black/5 dark:border-white/5 hover:border-black/20 dark:hover:border-white/20 transition-all hover:shadow-lg hover:shadow-black/5"
              >
                <div className="flex items-center gap-x-4 text-xs text-muted-foreground mb-3">
                  <time dateTime={post.created_at} className="flex items-center gap-x-1.5">
                    <CalendarDays className="w-3.5 h-3.5" />
                    {new Date(post.created_at).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </time>
                  <span className="flex items-center gap-1">
                    <Heart className="w-3.5 h-3.5 text-rose-500/70" />
                    {post.likes}
                  </span>
                </div>
                
                <h3 className="text-xl font-semibold leading-8 tracking-tight text-foreground transition-colors group-hover:text-blue-600 dark:group-hover:text-blue-400">
                  {post.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground line-clamp-2">
                  {post.summary}
                </p>

                <div className="mt-4 flex items-center text-sm font-medium text-foreground tracking-wide group-hover:text-blue-600 dark:group-hover:text-blue-400">
                  Read article <ArrowRight className="ml-1 w-4 h-4 transition-transform group-hover:translate-x-1" />
                </div>
              </motion.article>
            </Link>
          ))
        )}
      </div>
    </PageTransition>
  );
}
