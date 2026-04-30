import { LikeButton } from '@/components/blog/LikeButton';
import { PageTransition } from '@/components/layout/PageTransition';
import { fetchPostBySlug, fetchPosts, fetchSiteConfig, type Post } from '@/lib/api';
import { CalendarDays, ChevronLeft, Eye } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

type PageParams = {
  slug: string;
};

type TocHeading = {
  id: string;
  text: string;
  level: 2 | 3;
};

function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

function stripHtml(value: string): string {
  return decodeHtmlEntities(value.replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
}

function toAnchorId(text: string, fallbackIndex: number): string {
  const normalized = text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
  return normalized || `section-${fallbackIndex}`;
}

function injectHeadingIdsAndBuildToc(content: string): {
  html: string;
  toc: TocHeading[];
} {
  const toc: TocHeading[] = [];
  const headingRegex = /<h([23])([^>]*)>([\s\S]*?)<\/h\1>/gi;
  let index = 0;

  const html = content.replace(headingRegex, (_, levelRaw: string, attrs: string, inner: string) => {
    index += 1;
    const text = stripHtml(inner);
    const level = Number(levelRaw) as 2 | 3;
    const existingId = /\sid=["']([^"']+)["']/i.exec(attrs)?.[1];
    const id = existingId || toAnchorId(text, index);

    if (text) {
      toc.push({ id, text, level });
    }

    if (existingId) {
      return `<h${level}${attrs}>${inner}</h${level}>`;
    }
    return `<h${level}${attrs} id="${id}">${inner}</h${level}>`;
  });

  return { html, toc };
}

async function getAdjacentPosts(currentSlug: string): Promise<{
  previous: Post | null;
  next: Post | null;
}> {
  const list = await fetchPosts({ page: 1, page_size: 100 });
  const posts = list.data;
  const currentIndex = posts.findIndex((item) => item.slug === currentSlug);

  if (currentIndex === -1) {
    return { previous: null, next: null };
  }

  return {
    previous: posts[currentIndex + 1] || null,
    next: currentIndex > 0 ? posts[currentIndex - 1] : null,
  };
}

export async function generateMetadata({
  params,
}: {
  params: Promise<PageParams>;
}): Promise<Metadata> {
  const { slug } = await params;
  const [post, siteConfig] = await Promise.all([fetchPostBySlug(slug), fetchSiteConfig()]);

  if (!post) {
    return {
      title: 'Article Not Found',
      description: siteConfig?.description || 'Article not found.',
    };
  }

  const siteTitle = siteConfig?.title || 'Xiaobaicai Space';
  const description = post.summary || stripHtml(post.content || '').slice(0, 160) || siteConfig?.description || '';
  const canonicalPath = `/blog/${post.slug}`;
  const ogImage = post.cover_image || '/og-default.png';

  return {
    title: `${post.title} | ${siteTitle}`,
    description,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      type: 'article',
      title: post.title,
      description,
      url: canonicalPath,
      siteName: siteTitle,
      publishedTime: post.published_at || post.created_at,
      modifiedTime: post.updated_at,
      tags: post.tags,
      images: [
        {
          url: ogImage,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description,
      images: [ogImage],
    },
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<PageParams>;
}) {
  const { slug } = await params;
  const post = await fetchPostBySlug(slug);

  if (!post) {
    notFound();
  }

  const [{ html: htmlContent, toc }, adjacent] = await Promise.all([
    Promise.resolve(injectHeadingIdsAndBuildToc(post.content || '')),
    getAdjacentPosts(post.slug),
  ]);

  return (
    <PageTransition className="max-w-6xl mx-auto pt-8 pb-24">
      <Link
        href="/blog"
        className="group mb-8 inline-flex items-center text-sm font-medium text-ink-muted hover:text-ink transition-colors"
      >
        <ChevronLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-1" />
        Back to articles
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_250px] gap-8 items-start">
        <article className="card-surface rounded-4xl p-7 md:p-10">
          <header className="mb-14">
            <div className="mb-5 flex flex-wrap items-center gap-4 text-sm text-ink-muted">
              <time dateTime={post.created_at} className="flex items-center">
                <CalendarDays className="h-4 w-4 mr-2" />
                {new Date(post.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </time>
              <span className="inline-flex items-center">
                <Eye className="w-4 h-4 mr-2" />
                {post.view_count} views
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl text-ink mb-6 leading-[0.94]">{post.title}</h1>

            {post.summary ? (
              <p className="text-xl text-ink-muted leading-relaxed font-light">{post.summary}</p>
            ) : null}

            {post.tags?.length ? (
              <div className="mt-6 flex flex-wrap gap-2">
                {post.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-black/5 px-3 py-1 text-sm text-ink-muted">
                    #{tag}
                  </span>
                ))}
              </div>
            ) : null}
          </header>

          <div
            className="prose prose-stone max-w-none text-base md:text-lg leading-loose
                     prose-headings:text-ink prose-p:text-ink prose-a:text-[#1e5f63]
                     prose-pre:bg-[#efe8db] prose-pre:border prose-pre:border-line
                     prose-code:text-[#a6502e] prose-code:font-medium prose-img:rounded-3xl"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />

          <LikeButton slug={post.slug} initialLikeCount={post.like_count} />

          <nav className="mt-14 pt-8 border-t border-line grid grid-cols-1 md:grid-cols-2 gap-4">
            {adjacent.previous ? (
              <Link
                href={`/blog/${adjacent.previous.slug}`}
                className="rounded-2xl border border-line bg-white/60 p-4 hover:bg-white/80 transition-colors"
              >
                <p className="text-xs uppercase tracking-wider text-ink-muted mb-2">Previous</p>
                <p className="text-ink leading-snug">{adjacent.previous.title}</p>
              </Link>
            ) : (
              <div className="rounded-2xl border border-dashed border-line p-4 text-ink-muted text-sm">No previous article</div>
            )}

            {adjacent.next ? (
              <Link
                href={`/blog/${adjacent.next.slug}`}
                className="rounded-2xl border border-line bg-white/60 p-4 hover:bg-white/80 transition-colors text-right"
              >
                <p className="text-xs uppercase tracking-wider text-ink-muted mb-2">Next</p>
                <p className="text-ink leading-snug">{adjacent.next.title}</p>
              </Link>
            ) : (
              <div className="rounded-2xl border border-dashed border-line p-4 text-ink-muted text-sm text-right">No next article</div>
            )}
          </nav>
        </article>

        {toc.length > 0 ? (
          <aside className="hidden lg:block sticky top-28 card-surface rounded-3xl p-5">
            <p className="text-xs uppercase tracking-widest text-ink-muted mb-4">On this page</p>
            <ul className="space-y-2">
              {toc.map((item) => (
                <li key={item.id} className={item.level === 3 ? 'pl-4' : ''}>
                  <a
                    href={`#${item.id}`}
                    className="text-sm text-ink-muted hover:text-ink transition-colors leading-snug block"
                  >
                    {item.text}
                  </a>
                </li>
              ))}
            </ul>
          </aside>
        ) : null}
      </div>
    </PageTransition>
  );
}
