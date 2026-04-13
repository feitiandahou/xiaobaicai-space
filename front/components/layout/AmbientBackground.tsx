'use client';

import { motion } from 'framer-motion';

export function AmbientBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-[-1] opacity-50 dark:opacity-30">
      <div className="absolute inset-0 bg-white dark:bg-black" />
      <motion.div
        className="absolute w-[60vw] h-[60vh] -top-[20vh] -left-[10vw] rounded-full bg-blue-100 dark:bg-blue-900/30 blur-[120px]"
        animate={{
          x: [0, 50, 0, -30, 0],
          y: [0, -30, 20, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
      <motion.div
        className="absolute w-[50vw] h-[50vh] bottom-[10vh] right-[5vw] rounded-full bg-purple-100 dark:bg-purple-900/20 blur-[100px]"
        animate={{
          x: [0, -40, 20, 0],
          y: [0, 50, -20, 0],
          scale: [1, 1.2, 0.9, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
          delay: 2,
        }}
      />
    </div>
  );
}
