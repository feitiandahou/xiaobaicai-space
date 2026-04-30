'use client';

import { motion } from 'framer-motion';

export function AmbientBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-[-1]">
      <div className="absolute inset-0 bg-canvas" />
      <motion.div
        className="absolute w-[56vw] h-[62vh] -top-[22vh] -left-[8vw] rounded-full bg-[#f0c3a8] blur-[120px] opacity-50"
        animate={{
          x: [0, 50, 0, -35, 0],
          y: [0, -30, 24, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
      <motion.div
        className="absolute w-[48vw] h-[50vh] bottom-[8vh] right-[5vw] rounded-full bg-[#86b8bb] blur-[105px] opacity-45"
        animate={{
          x: [0, -40, 20, 0],
          y: [0, 50, -20, 0],
          scale: [1, 1.2, 0.9, 1],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: 'linear',
          delay: 2,
        }}
      />

      <div className="absolute inset-x-0 bottom-0 h-56 bg-linear-to-t from-[#f4efe5] to-transparent" />
    </div>
  );
}
