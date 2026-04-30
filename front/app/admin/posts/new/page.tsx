'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import {
  CategoryOption,
  createAdminCategory,
  createAdminTag,
  createPost,
  fetchAdminCategories,
  fetchAdminTags,
  PostCreateData,
  TagOption,
} from '@/lib/api/admin';
import { ArrowLeft, Loader2, Plus, Save, X } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

function makeSlug(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

export default function NewPost() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [isError, setIsError] = useState('');
  const [userId, setUserId] = useState<number | null>(null);
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [tags, setTags] = useState<TagOption[]>([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showTagModal, setShowTagModal] = useState(false);
  const [creatingCategory, setCreatingCategory] = useState(false);
  const [creatingTag, setCreatingTag] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategorySlug, setNewCategorySlug] = useState('');
  const [newTagName, setNewTagName] = useState('');
  const [newTagSlug, setNewTagSlug] = useState('');
  
  const [formData, setFormData] = useState<PostCreateData>({
    user_id: 0,
    title: '',
    slug: '',
    summary: '',
    content: '',
    cover_image: '',
    category_id: null,
    status: 0,
    is_top: 0,
    tag_ids: [],
  });

  useEffect(() => {
    const token = localStorage.getItem('admin_access_token');
    const savedUserId = Number(localStorage.getItem('admin_user_id') || 0);
    if (!token || !savedUserId) {
      router.push('/admin');
      return;
    }
    setUserId(savedUserId);
    setFormData((current) => ({ ...current, user_id: savedUserId }));

    Promise.all([fetchAdminCategories(token), fetchAdminTags(token)])
      .then(([categoryList, tagList]) => {
        setCategories(categoryList.filter((item) => item.id > 0 && item.name));
        setTags(tagList.filter((item) => item.id > 0 && item.name));
      })
      .catch((err) => {
        setIsError((err as Error).message);
      })
      .finally(() => {
        setOptionsLoading(false);
      });
  }, [router]);

  const toggleTag = (tagId: number) => {
    setFormData((current) => {
      const existed = current.tag_ids.includes(tagId);
      return {
        ...current,
        tag_ids: existed
          ? current.tag_ids.filter((id) => id !== tagId)
          : [...current.tag_ids, tagId],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsError('');
    setLoading(true);
    try {
      const token = localStorage.getItem('admin_access_token') || '';
      if (!token || !userId) {
        throw new Error('Missing admin session. Please login again.');
      }
      await createPost(token, {
        ...formData,
        user_id: userId,
      });
      router.push('/admin');
    } catch (err) {
      setIsError((err as Error).message);
      setLoading(false);
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsError('');
    const token = localStorage.getItem('admin_access_token') || '';
    const slug = makeSlug(newCategorySlug || newCategoryName);
    if (!token) {
      setIsError('Missing admin session. Please login again.');
      return;
    }
    if (!newCategoryName.trim() || !slug) {
      setIsError('Category name and slug are required.');
      return;
    }

    setCreatingCategory(true);
    try {
      const created = await createAdminCategory(token, {
        name: newCategoryName.trim(),
        slug,
      });
      setCategories((current) => [...current, created]);
      setFormData((current) => ({ ...current, category_id: created.id }));
      setNewCategoryName('');
      setNewCategorySlug('');
      setShowCategoryModal(false);
    } catch (err) {
      setIsError((err as Error).message);
    } finally {
      setCreatingCategory(false);
    }
  };

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsError('');
    const token = localStorage.getItem('admin_access_token') || '';
    const slug = makeSlug(newTagSlug || newTagName);
    if (!token) {
      setIsError('Missing admin session. Please login again.');
      return;
    }
    if (!newTagName.trim() || !slug) {
      setIsError('Tag name and slug are required.');
      return;
    }

    setCreatingTag(true);
    try {
      const created = await createAdminTag(token, {
        name: newTagName.trim(),
        slug,
      });
      setTags((current) => [...current, created]);
      setFormData((current) => ({ ...current, tag_ids: [...current.tag_ids, created.id] }));
      setNewTagName('');
      setNewTagSlug('');
      setShowTagModal(false);
    } catch (err) {
      setIsError((err as Error).message);
    } finally {
      setCreatingTag(false);
    }
  };

  return (
    <PageTransition className="pt-8 pb-24 max-w-4xl mx-auto relative">
      <Link
        href="/admin"
        className="group mb-8 inline-flex items-center text-sm font-medium text-ink-muted hover:text-ink transition-colors"
      >
        <ArrowLeft className="mr-1 h-4 w-4 transition-transform group-hover:-translate-x-1" />
        Back to Console
      </Link>

      <div className="card-surface rounded-4xl p-7 md:p-9">
        <div className="mb-10">
          <h1 className="text-5xl leading-none text-ink mb-2">Create Article</h1>
          <p className="text-ink-muted">Compose content and publish through backend API.</p>
        </div>

        {isError && (
          <div className="p-4 mb-8 bg-[#a6502e]/10 text-[#7d3d22] rounded-xl border border-[#a6502e]/20 font-medium">
            {isError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
               <label className="text-sm font-medium tracking-tight text-ink-muted">Title</label>
               <input
                 required
                 value={formData.title}
                 onChange={(e) => setFormData({...formData, title: e.target.value})}
                 className="w-full px-4 py-3 bg-white/75 border border-line rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
                 placeholder="A practical title"
               />
            </div>
            
            <div className="space-y-2">
               <label className="text-sm font-medium tracking-tight text-ink-muted">Slug (optional)</label>
               <input
                 value={formData.slug}
                 onChange={(e) => setFormData({...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, '-')})}
                 className="w-full px-4 py-3 bg-white/75 border border-line rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
                 placeholder="my-article-slug"
               />
            </div>
          </div>

          <div className="space-y-2">
             <label className="text-sm font-medium tracking-tight text-ink-muted">Summary</label>
             <textarea
               value={formData.summary}
               onChange={(e) => setFormData({...formData, summary: e.target.value})}
               className="w-full px-4 py-3 bg-white/75 border border-line rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40 min-h-20 resize-y"
               placeholder="A short introduction"
             />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <label className="text-sm font-medium tracking-tight text-ink-muted">Category</label>
                <button
                  type="button"
                  onClick={() => setShowCategoryModal(true)}
                  className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-[#ece7db] text-ink-muted hover:text-ink transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  New
                </button>
              </div>
              <select
                value={formData.category_id ?? ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    category_id: e.target.value ? Number(e.target.value) : null,
                  })
                }
                className="w-full px-4 py-3 bg-white/75 border border-line rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
                disabled={optionsLoading}
              >
                <option value="">Uncategorized</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name} ({category.slug})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium tracking-tight text-ink-muted">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: Number(e.target.value) })}
                className="w-full px-4 py-3 bg-white/75 border border-line rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
              >
                <option value={0}>Draft</option>
                <option value={1}>Published</option>
                <option value={2}>Archived</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <label className="text-sm font-medium tracking-tight text-ink-muted">Tags</label>
              <button
                type="button"
                onClick={() => setShowTagModal(true)}
                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-[#ece7db] text-ink-muted hover:text-ink transition-colors"
              >
                <Plus className="w-3 h-3" />
                New
              </button>
            </div>
            <div className="rounded-2xl border border-line bg-white/70 px-4 py-3">
              {optionsLoading ? (
                <p className="text-sm text-ink-muted">Loading tags...</p>
              ) : tags.length === 0 ? (
                <p className="text-sm text-ink-muted">No tags available.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => {
                    const active = formData.tag_ids.includes(tag.id);
                    return (
                      <button
                        key={tag.id}
                        type="button"
                        onClick={() => toggleTag(tag.id)}
                        className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                          active
                            ? 'bg-[#1f1d1a] text-[#fbf8f1]'
                            : 'bg-[#ece7db] text-ink-muted hover:text-ink'
                        }`}
                      >
                        <span className="font-medium">{tag.name}</span>
                        <span className={`ml-2 text-xs ${active ? 'text-[#efe9de]' : 'text-ink-muted'}`}>
                          {tag.slug}
                          {typeof tag.post_count === 'number' ? ` · ${tag.post_count}` : ''}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium tracking-tight text-ink-muted">Content (HTML)</label>
            <textarea
              required
              value={formData.content}
              onChange={(e) => setFormData({...formData, content: e.target.value})}
              className="w-full px-5 py-4 bg-white/75 border border-line rounded-3xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40 min-h-[42vh] resize-y font-mono text-sm leading-loose"
              placeholder="<h2>Start writing...</h2>"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 py-6 border-t border-line">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_top === 1}
                onChange={(e) => setFormData({ ...formData, is_top: e.target.checked ? 1 : 0 })}
              />
              <span className="text-sm font-medium tracking-wide text-ink-muted">Set as top article</span>
            </label>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-8 py-3.5 bg-[#1f1d1a] text-[#fbf8f1] rounded-full font-medium"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {loading ? 'Saving...' : 'Publish'}
            </button>
          </div>
        </form>
      </div>

      {showCategoryModal && (
        <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-sm grid place-items-center p-4">
          <div className="w-full max-w-md rounded-3xl bg-[#fbf8f1] border border-line p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl text-ink">Quick Create Category</h2>
              <button
                type="button"
                onClick={() => setShowCategoryModal(false)}
                className="p-2 rounded-full hover:bg-[#ece7db]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateCategory} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm text-ink-muted">Name</label>
                <input
                  required
                  value={newCategoryName}
                  onChange={(e) => {
                    setNewCategoryName(e.target.value);
                    if (!newCategorySlug) {
                      setNewCategorySlug(makeSlug(e.target.value));
                    }
                  }}
                  className="w-full px-3 py-2.5 bg-white border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/30"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm text-ink-muted">Slug</label>
                <input
                  required
                  value={newCategorySlug}
                  onChange={(e) => setNewCategorySlug(makeSlug(e.target.value))}
                  className="w-full px-3 py-2.5 bg-white border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/30"
                />
              </div>
              <button
                type="submit"
                disabled={creatingCategory}
                className="w-full py-2.5 rounded-xl bg-[#1f1d1a] text-[#fbf8f1] font-medium"
              >
                {creatingCategory ? 'Creating...' : 'Create Category'}
              </button>
            </form>
          </div>
        </div>
      )}

      {showTagModal && (
        <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-sm grid place-items-center p-4">
          <div className="w-full max-w-md rounded-3xl bg-[#fbf8f1] border border-line p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl text-ink">Quick Create Tag</h2>
              <button
                type="button"
                onClick={() => setShowTagModal(false)}
                className="p-2 rounded-full hover:bg-[#ece7db]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateTag} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm text-ink-muted">Name</label>
                <input
                  required
                  value={newTagName}
                  onChange={(e) => {
                    setNewTagName(e.target.value);
                    if (!newTagSlug) {
                      setNewTagSlug(makeSlug(e.target.value));
                    }
                  }}
                  className="w-full px-3 py-2.5 bg-white border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/30"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm text-ink-muted">Slug</label>
                <input
                  required
                  value={newTagSlug}
                  onChange={(e) => setNewTagSlug(makeSlug(e.target.value))}
                  className="w-full px-3 py-2.5 bg-white border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/30"
                />
              </div>
              <button
                type="submit"
                disabled={creatingTag}
                className="w-full py-2.5 rounded-xl bg-[#1f1d1a] text-[#fbf8f1] font-medium"
              >
                {creatingTag ? 'Creating...' : 'Create Tag'}
              </button>
            </form>
          </div>
        </div>
      )}
    </PageTransition>
  );
}
