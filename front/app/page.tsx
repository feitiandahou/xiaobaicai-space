'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { MoveRight } from 'lucide-react';

export default function Home() {
  return (
    <PageTransition className="flex flex-col items-center justify-center min-h-[60vh] text-center pt-24">
      <motion.div
        initial={{ scale: 0.9, opacity: 0, filter: "blur(10px)" }}
        animate={{ scale: 1, opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="mb-8"
      >
        <span className="px-4 py-1.5 rounded-full border border-black/10 dark:border-white/10 bg-black/5 dark:bg-white/5 text-xs font-medium tracking-wide text-muted-foreground inline-block mb-3">
          Welcome to the Space
        </span>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-foreground leading-tight">
          Crafting Art <br /> Through Code
        </h1>
      </motion.div>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="text-lg md:text-xl text-muted-foreground max-w-[500px] mb-10 leading-relaxed font-light"
      >
        A minimalist personal sanctuary designed to showcase thoughts, engineering, and digital aesthetics.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="flex items-center space-x-4"
      >
        <Link
          href="/blog"
          className="group flex items-center space-x-2 bg-black dark:bg-white text-white dark:text-black px-6 py-3 rounded-full font-medium hover:scale-105 transition-transform active:scale-95 shadow-md"
        >
          <span>Read Articles</span>
          <MoveRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>
        <Link
          href="https://github.com"
          target="_blank"
          className="px-6 py-3 rounded-full font-medium hover:bg-black/5 dark:hover:bg-white/5 transition-colors border border-transparent hover:border-black/10 dark:hover:border-white/10 text-muted-foreground hover:text-foreground"        
        >
          GitHub
        </Link>
      </motion.div>
    </PageTransition>
  );
}

