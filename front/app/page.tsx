'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { fetchPosts, fetchSiteConfig } from '@/lib/api';
import { motion } from 'framer-motion';
import { ArrowUpRight, Flame, Newspaper, PenLine } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type HomeSnapshot = {
  postCount: number;
  latestTitle: string;
};

export default function Home() {
  const [subtitle, setSubtitle] = useState('Writing software, systems, and clear thoughts.');
  const [snapshot, setSnapshot] = useState<HomeSnapshot>({
    postCount: 0,
    latestTitle: 'No published post yet',
  });

  useEffect(() => {
    fetchSiteConfig().then((config) => {
      if (config?.subtitle) {
        setSubtitle(config.subtitle);
      }
    });

    fetchPosts({ page: 1, page_size: 3 }).then((result) => {
      setSnapshot({
        postCount: result.meta.total,
        latestTitle: result.data[0]?.title || 'No published post yet',
      });
    });
  }, []);

  const chips = useMemo(
    () => [
      { icon: Newspaper, label: `${snapshot.postCount} published essays` },
      { icon: Flame, label: `Latest: ${snapshot.latestTitle}` },
    ],
    [snapshot]
  );

  return (
    <PageTransition className="pt-8 md:pt-14">
      <motion.div
        initial={{ scale: 0.95, opacity: 0, filter: 'blur(8px)' }}
        animate={{ scale: 1, opacity: 1, filter: 'blur(0px)' }}
        transition={{ duration: 0.75, ease: 'easeOut' }}
        className="card-surface grain-overlay rounded-4xl p-7 md:p-12"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-line bg-white/50 text-xs font-semibold uppercase tracking-[0.14em] text-ink-muted">
          <PenLine className="w-3.5 h-3.5" />
          Independent Publication
        </span>

        <h1 className="mt-6 text-5xl md:text-7xl leading-[0.92] text-ink">
          Build systems.
          <br />
          Publish clarity.
        </h1>

        <p className="mt-6 max-w-2xl text-base md:text-xl text-ink-muted leading-relaxed">{subtitle}</p>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3">
          {chips.map((chip, index) => (
            <motion.div
              key={chip.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.16 + index * 0.08, duration: 0.45 }}
              className="rounded-2xl border border-line bg-white/55 px-4 py-3 text-sm text-ink-muted flex items-center gap-3"
            >
              <chip.icon className="w-4 h-4 text-burnt" />
              <span className="truncate">{chip.label}</span>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
          className="mt-9 flex flex-wrap items-center gap-3"
        >
          <Link
            href="/blog"
            className="group inline-flex items-center gap-2 rounded-full bg-[#1f1d1a] text-[#fdf9f1] px-6 py-3 text-sm font-semibold tracking-wide hover:opacity-90 transition-opacity"
          >
            Explore Articles
            <ArrowUpRight className="w-4 h-4 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            href="/admin"
            className="inline-flex items-center gap-2 rounded-full border border-line bg-white/60 px-6 py-3 text-sm font-semibold text-ink-muted hover:text-ink hover:bg-white/75 transition-colors"
          >
            Admin Console
          </Link>
        </motion.div>
      </motion.div>
    </PageTransition>
  );
}

