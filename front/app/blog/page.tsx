'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { fetchPosts, type Post } from '@/lib/api';
import { motion } from 'framer-motion';
import { ArrowRight, CalendarDays, Heart, Search } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function BlogLandingPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(9);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts({ page, page_size: pageSize, search: search || undefined }).then((res) => {
      setPosts(res.data);
      setTotal(res.meta.total);
      setLoading(false);
    });
  }, [page, pageSize, search]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setPage(1);
    setSearch(searchInput.trim());
  };

  return (
    <PageTransition className="pt-4 md:pt-8">
      <div className="card-surface rounded-4xl p-6 md:p-9 mb-10">
        <h1 className="text-5xl md:text-6xl leading-none">Journal</h1>
        <p className="text-ink-muted text-base md:text-lg mt-4 max-w-2xl">
          Long-form notes about engineering decisions, product thinking, and architecture from real projects.
        </p>

        <form onSubmit={onSubmit} className="mt-6 flex items-center gap-2 rounded-2xl border border-line bg-white/60 px-3 py-2">
          <Search className="w-4 h-4 text-ink-muted" />
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by title or summary"
            className="w-full bg-transparent outline-none text-sm text-ink"
          />
          <button
            type="submit"
            className="shrink-0 rounded-xl bg-[#1f1d1a] px-3 py-1.5 text-xs font-semibold tracking-wide text-[#fbf8f1]"
          >
            Search
          </button>
        </form>

        <div className="mt-4 text-sm text-ink-muted">
          Showing {posts.length} of {total} results
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-black/5 h-48 rounded-3xl w-full" />
          ))
        ) : posts.length === 0 ? (
          <div className="lg:col-span-2 text-center py-20 text-ink-muted border border-dashed border-line rounded-3xl bg-white/50">
            No articles published yet.
          </div>
        ) : (
          posts.map((post, idx) => (
            <Link key={post.id} href={`/blog/${post.slug}`}>
              <motion.article
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className="group h-full card-surface rounded-3xl p-6 flex flex-col"
              >
                <div className="flex items-center gap-x-4 text-xs text-ink-muted mb-3">
                  <time dateTime={post.created_at} className="flex items-center gap-x-1.5">
                    <CalendarDays className="w-3.5 h-3.5" />
                    {new Date(post.created_at).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </time>
                  <span className="flex items-center gap-1">
                    <Heart className="w-3.5 h-3.5 text-[#a6502e]" />
                    {post.like_count}
                  </span>
                </div>
                
                <h3 className="text-3xl leading-tight text-ink transition-colors group-hover:text-burnt">
                  {post.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-ink-muted line-clamp-2">
                  {post.summary}
                </p>

                {post.tags?.length ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {post.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-black/5 px-2.5 py-1 text-xs text-ink-muted"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                ) : null}

                <div className="mt-auto pt-6 flex items-center text-sm font-medium text-ink tracking-wide group-hover:text-burnt">
                  Read article <ArrowRight className="ml-1 w-4 h-4 transition-transform group-hover:translate-x-1" />
                </div>
              </motion.article>
            </Link>
          ))
        )}
      </div>

      {!loading && totalPages > 1 ? (
        <div className="mt-10 flex items-center justify-center gap-3">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => {
              setLoading(true);
              setPage((current) => Math.max(1, current - 1));
            }}
            className="px-4 py-2 rounded-xl border border-line text-sm text-ink disabled:opacity-45"
          >
            Previous
          </button>
          <span className="text-sm text-ink-muted">
            Page {page} / {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => {
              setLoading(true);
              setPage((current) => Math.min(totalPages, current + 1));
            }}
            className="px-4 py-2 rounded-xl border border-line text-sm text-ink disabled:opacity-45"
          >
            Next
          </button>
        </div>
      ) : null}
    </PageTransition>
  );
}
