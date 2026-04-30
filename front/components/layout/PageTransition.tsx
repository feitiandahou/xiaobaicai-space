'use client'

import type { Variants } from 'framer-motion'
import { motion } from 'framer-motion'
import { ReactNode } from 'react'

interface PageTransitionProps {
  children: ReactNode
  className?: string
}

const transitionVariants: Variants = {
  hidden: { opacity: 0, y: 18, filter: 'blur(6px)' },
  enter: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { duration: 0.55, ease: 'easeOut' },
  },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25, ease: 'easeIn' } },
}

export function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <motion.div
      initial="hidden"
      animate="enter"
      exit="exit"
      variants={transitionVariants}
      className={className}
    >
      {children}
    </motion.div>
  )
}
