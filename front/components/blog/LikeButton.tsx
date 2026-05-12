'use client';

import { likePostAPI } from '@/lib/api';
import { cn } from '@/lib/utils';
import { AnimatePresence, motion } from 'framer-motion';
import { Heart } from 'lucide-react';
import { useState } from 'react';

const likedStorageKey = (slug: string, actorScope: string) => `post-liked:${actorScope}:${slug}`;

function getLikeActorScope() {
  if (typeof window === 'undefined') {
    return {
      hasAccountSession: false,
      storageKeyPrefix: 'browser',
    };
  }

  const accessToken = window.localStorage.getItem('admin_access_token');
  const userId = window.localStorage.getItem('admin_user_id');
  if (accessToken && userId) {
    return {
      hasAccountSession: true,
      storageKeyPrefix: `user:${userId}`,
    };
  }

  return {
    hasAccountSession: false,
    storageKeyPrefix: 'browser',
  };
}

export function LikeButton({
  slug,
  initialLikeCount,
}: {
  slug: string;
  initialLikeCount: number;
}) {
  const [likeCount, setLikeCount] = useState(initialLikeCount);
  const [isLiking, setIsLiking] = useState(false);
  const [hasLiked, setHasLiked] = useState(() => {
    if (typeof window === 'undefined') {
      return false;
    }

    const actorScope = getLikeActorScope();
    return window.localStorage.getItem(likedStorageKey(slug, actorScope.storageKeyPrefix)) === '1';
  });

  const handleLike = async () => {
    if (isLiking || hasLiked) return;
    setIsLiking(true);
    const actorScope = getLikeActorScope();
    const result = await likePostAPI(slug);
    if (result?.alreadyLiked) {
      setHasLiked(true);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(likedStorageKey(slug, actorScope.storageKeyPrefix), '1');
      }
      setIsLiking(false);
      return;
    }

    if (result !== null) {
      setLikeCount(result.likeCount);
      setHasLiked(true);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(likedStorageKey(slug, actorScope.storageKeyPrefix), '1');
      }
    }
    setIsLiking(false);
  };

  const actorScope = getLikeActorScope();

  return (
    <div className="mt-20 pt-10 border-t border-line flex flex-col items-center">
      <p className="text-sm font-medium text-ink-muted mb-4 uppercase tracking-widest">Show some love</p>
      <motion.button
        onClick={handleLike}
        disabled={isLiking || hasLiked}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={cn(
          'relative flex items-center gap-3 px-8 py-4 rounded-full border shadow-sm transition-colors',
          isLiking || hasLiked ? 'opacity-70' : 'hover:shadow-md',
          'bg-white/70 backdrop-blur-md border-line'
        )}
      >
        <AnimatePresence>
          {isLiking ? (
            <motion.div
              initial={{ scale: 0.5, opacity: 1 }}
              animate={{ scale: 2, opacity: 0 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-[#a6502e]/20 rounded-full"
            />
          ) : null}
        </AnimatePresence>
        <Heart className={cn('w-6 h-6', likeCount > 0 ? 'fill-[#a6502e] text-[#a6502e]' : 'text-ink-muted')} />
        <span className="text-lg font-medium text-ink min-w-5 text-center">{likeCount}</span>
      </motion.button>
      <p className="mt-3 text-xs uppercase tracking-[0.24em] text-ink-muted">
        {hasLiked
          ? actorScope.hasAccountSession
            ? 'Already liked from this account'
            : 'Already liked from this browser'
          : actorScope.hasAccountSession
            ? 'One like per account'
            : 'One like per browser'}
      </p>
    </div>
  );
}
