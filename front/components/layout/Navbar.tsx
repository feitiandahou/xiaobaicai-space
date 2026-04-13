import Link from 'next/link';
import { Home, PenTool, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Navbar() {
  return (
    <div className="fixed top-0 inset-x-0 z-50 flex justify-center pt-6 px-4 pointer-events-none">
      <nav className="pointer-events-auto bg-white/70 dark:bg-black/70 backdrop-blur-xl border border-black/10 dark:border-white/10 shadow-sm rounded-full px-6 py-3 flex items-center space-x-8 text-sm font-medium transition-all hover:shadow-md">
        <Link href="/" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2">
          <Home className="w-4 h-4" />
          <span>Home</span>
        </Link>
        <Link href="/blog" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2">
          <PenTool className="w-4 h-4" />
          <span>Articles</span>
        </Link>
        <Link href="/blog" className="text-muted-foreground hover:text-foreground transition-colors flex items-center space-x-2">
          <Search className="w-4 h-4" />
          <span>Search</span>
        </Link>
      </nav>
    </div>
  );
}
