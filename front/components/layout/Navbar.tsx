import { Home, PenTool, Shield, Sparkles } from 'lucide-react';
import Link from 'next/link';

export function Navbar() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 px-4 pt-4 md:pt-6 pointer-events-none">
      <nav className="pointer-events-auto max-w-5xl mx-auto card-surface rounded-2xl md:rounded-full px-4 md:px-6 py-3 flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2 min-w-0">
          <Sparkles className="w-4 h-4 text-burnt shrink-0" />
          <span className="font-semibold tracking-wide text-sm md:text-base truncate">Xiaobaicai Space</span>
        </Link>

        <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm font-medium">
          <Link href="/" className="px-3 py-2 rounded-full text-ink-muted hover:text-ink hover:bg-black/5 transition-colors inline-flex items-center gap-2">
            <Home className="w-3.5 h-3.5" />
            Home
          </Link>
          <Link href="/blog" className="px-3 py-2 rounded-full text-ink-muted hover:text-ink hover:bg-black/5 transition-colors inline-flex items-center gap-2">
            <PenTool className="w-3.5 h-3.5" />
            Blog
          </Link>
          <Link href="/admin" className="px-3 py-2 rounded-full text-ink-muted hover:text-ink hover:bg-black/5 transition-colors inline-flex items-center gap-2">
            <Shield className="w-3.5 h-3.5" />
            Admin
          </Link>
        </div>
      </nav>
    </header>
  );
}
