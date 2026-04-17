'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { fetchPostBySlug, likePostAPI, Post } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, ChevronLeft, CalendarDays } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils'; // if you need styling conditional

export default function BlogPost() {
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [likeCount, setLikeCount] = useState(0);
  const [isLiking, setIsLiking] = useState(false);

  useEffect(() => {
    fetchPostBySlug(slug).then((res) => {
      setPost(res);
      if (res) setLikeCount(res.likes);
      setLoading(false);
    });
  }, [slug]);

  const handleLike = async () => {
    if (isLiking || !post) return;
    setIsLiking(true);
    const newLikes = await likePostAPI(post.slug);
    if (newLikes !== null) {
      setLikeCount(newLikes);
    }
    setIsLiking(false);
  };

  if (loading) {
    return (
      <PageTransition className="max-w-3xl mx-auto pt-16 flex justify-center items-center h-[50vh]">
        <div className="animate-pulse bg-black/10 dark:bg-white/10 w-16 h-16 rounded-full" />
      </PageTransition>
    );
  }

  if (!post) {
    return (
      <PageTransition className="max-w-3xl mx-auto pt-16 text-center text-muted-foreground font-light text-xl h-[40vh] flex items-center justify-center">
        404 - Article not found.
      </PageTransition>
    );
  }

  return (
    <PageTransition className="max-w-3xl mx-auto pt-16 pb-24">
      <Link
        href="/blog"
        className="group mb-8 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-1" />
        Back to articles
      </Link>

      <motion.article 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <header className="mb-14">
          <time
            dateTime={post.created_at}
            className="flex items-center text-sm text-muted-foreground mb-4"
          >
            <CalendarDays className="h-4 w-4 mr-2" />
            {new Date(post.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </time>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground sm:text-5xl mb-6 leading-tight">
            {post.title}
          </h1>
          {post.summary && (
            <p className="text-xl text-muted-foreground leading-relaxed font-light">
              {post.summary}
            </p>
          )}
          {post.tags?.length ? (
            <div className="mt-6 flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-black/5 dark:bg-white/10 px-3 py-1 text-sm text-muted-foreground"
                >
                  #{tag}
                </span>
              ))}
            </div>
          ) : null}
        </header>

        {/* Since content is likely markdown/html in a real app, you would parse it here 
            For now, we just display plain text or use dangerouslySetInnerHTML */}
        <div
          className="prose prose-slate dark:prose-invert max-w-none text-base md:text-lg leading-loose
                     prose-pre:bg-black/5 prose-pre:dark:bg-white/5 prose-pre:border prose-pre:border-black/10 prose-pre:dark:border-white/10
                     prose-code:text-rose-500 prose-code:font-medium prose-img:rounded-3xl"
          dangerouslySetInnerHTML={{ __html: post.content || '' }}
        />

        {/* Like Section */}
        <div className="mt-20 pt-10 border-t border-black/5 dark:border-white/10 flex flex-col items-center">
          <p className="text-sm font-medium text-muted-foreground mb-4 uppercase tracking-widest">
            Show some love
          </p>
          <motion.button
            onClick={handleLike}
            disabled={isLiking}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={cn(
              "relative flex items-center gap-3 px-8 py-4 rounded-full border shadow-sm transition-colors",
              isLiking ? "opacity-70" : "hover:shadow-md",
              "bg-white/50 dark:bg-black/50 backdrop-blur-md border-black/10 dark:border-white/10"
            )}
          >
            <AnimatePresence>
              {isLiking && (
                <motion.div 
                  initial={{ scale: 0.5, opacity: 1 }}
                  animate={{ scale: 2, opacity: 0 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-rose-500/20 rounded-full"
                />
              )}
            </AnimatePresence>
            <Heart className={cn("w-6 h-6", likeCount > 0 ? "fill-rose-500 text-rose-500" : "text-muted-foreground")} />
            <span className="text-lg font-medium text-foreground min-w-5 text-center">
              {likeCount}
            </span>
          </motion.button>
        </div>
      </motion.article>
    </PageTransition>
  );
}
