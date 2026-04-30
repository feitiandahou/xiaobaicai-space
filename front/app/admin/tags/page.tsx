'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { createAdminTag, deleteAdminTag, fetchAdminTags, type TagOption, updateAdminTag } from '@/lib/api/admin';
import { ArrowLeft, Loader2, Pencil, Plus, Save, Trash2, X } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

function makeSlug(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

export default function AdminTagsPage() {
  const [tags, setTags] = useState<TagOption[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'post_count'>('name');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [batchDeleting, setBatchDeleting] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');
  const [editingSlug, setEditingSlug] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('admin_access_token');
    if (!token) {
      window.location.href = '/admin';
      return;
    }

    fetchAdminTags(token)
      .then((items) => {
        setTags(items.filter((item) => item.id > 0 && item.name));
      })
      .catch((err) => {
        setError((err as Error).message);
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredTags = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    const base = keyword
      ? tags.filter((item) => {
          return item.name.toLowerCase().includes(keyword) || item.slug.toLowerCase().includes(keyword);
        })
      : tags;

    return [...base].sort((a, b) => {
      if (sortBy === 'post_count') {
        const countA = a.post_count || 0;
        const countB = b.post_count || 0;
        if (countA !== countB) {
          return countB - countA;
        }
      }
      return a.name.localeCompare(b.name);
    });
  }, [tags, query, sortBy]);

  const visibleIds = useMemo(() => filteredTags.map((item) => item.id), [filteredTags]);
  const selectedVisibleCount = useMemo(
    () => selectedIds.filter((id) => visibleIds.includes(id)).length,
    [selectedIds, visibleIds]
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const token = localStorage.getItem('admin_access_token') || '';
    if (!token) {
      setError('Missing admin session. Please login again.');
      return;
    }

    const finalSlug = makeSlug(slug || name);
    if (!name.trim() || !finalSlug) {
      setError('Tag name and slug are required.');
      return;
    }

    setCreating(true);
    try {
      const created = await createAdminTag(token, {
        name: name.trim(),
        slug: finalSlug,
      });
      setTags((current) => [...current, created]);
      setSelectedIds((current) => current.filter((id) => id !== created.id));
      setName('');
      setSlug('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this tag?')) return;

    setError('');
    const token = localStorage.getItem('admin_access_token') || '';
    if (!token) {
      setError('Missing admin session. Please login again.');
      return;
    }

    setDeletingId(id);
    try {
      await deleteAdminTag(token, id);
      setTags((current) => current.filter((item) => item.id !== id));
      setSelectedIds((current) => current.filter((itemId) => itemId !== id));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleStartEdit = (item: TagOption) => {
    setEditingId(item.id);
    setEditingName(item.name);
    setEditingSlug(item.slug);
    setError('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingName('');
    setEditingSlug('');
  };

  const handleSaveEdit = async (id: number) => {
    setError('');
    const token = localStorage.getItem('admin_access_token') || '';
    if (!token) {
      setError('Missing admin session. Please login again.');
      return;
    }

    const finalName = editingName.trim();
    const finalSlug = makeSlug(editingSlug || finalName);
    if (!finalName || !finalSlug) {
      setError('Tag name and slug are required.');
      return;
    }

    setUpdatingId(id);
    try {
      const updated = await updateAdminTag(token, id, {
        name: finalName,
        slug: finalSlug,
      });
      setTags((current) => current.map((item) => (item.id === id ? updated : item)));
      handleCancelEdit();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUpdatingId(null);
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id]
    );
  };

  const selectAllVisible = () => {
    setSelectedIds((current) => {
      const merged = new Set([...current, ...visibleIds]);
      return Array.from(merged);
    });
  };

  const clearVisibleSelection = () => {
    setSelectedIds((current) => current.filter((id) => !visibleIds.includes(id)));
  };

  const handleBatchDelete = async () => {
    const targetIds = selectedIds.filter((id) => visibleIds.includes(id));
    if (targetIds.length === 0) {
      setError('Please select tags to delete.');
      return;
    }
    if (!confirm(`Delete ${targetIds.length} selected tags?`)) return;

    setError('');
    const token = localStorage.getItem('admin_access_token') || '';
    if (!token) {
      setError('Missing admin session. Please login again.');
      return;
    }

    setBatchDeleting(true);
    try {
      const nameMap = new Map(tags.map((item) => [item.id, item.name]));
      const results = await Promise.allSettled(targetIds.map((id) => deleteAdminTag(token, id)));

      const succeededIds: number[] = [];
      const failedNames: string[] = [];

      results.forEach((result, index) => {
        const id = targetIds[index];
        if (result.status === 'fulfilled') {
          succeededIds.push(id);
          return;
        }
        failedNames.push(nameMap.get(id) || `#${id}`);
      });

      if (succeededIds.length > 0) {
        setTags((current) => current.filter((item) => !succeededIds.includes(item.id)));
        setSelectedIds((current) => current.filter((id) => !succeededIds.includes(id)));
      }

      if (failedNames.length > 0) {
        setError(`Deleted ${succeededIds.length}, failed ${failedNames.length}: ${failedNames.join(', ')}`);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBatchDeleting(false);
    }
  };

  if (loading) {
    return (
      <PageTransition className="pt-10 pb-20 max-w-5xl mx-auto">
        <div className="card-surface rounded-4xl p-8 flex items-center gap-3 text-ink-muted">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading tags...
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="pt-10 pb-20 max-w-5xl mx-auto">
      <div className="mb-6">
        <Link href="/admin" className="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-ink">
          <ArrowLeft className="w-4 h-4" />
          Back to admin
        </Link>
      </div>

      <div className="card-surface rounded-4xl p-6 md:p-8">
        <h1 className="text-4xl leading-none">Tags</h1>
        <p className="text-ink-muted mt-2">Manage content tags used by your posts.</p>

        {error ? (
          <div className="mt-5 rounded-xl border border-[#a6502e]/30 bg-[#a6502e]/10 p-3 text-sm text-[#7d3d22]">
            {error}
          </div>
        ) : null}

        <form onSubmit={handleCreate} className="mt-6 grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tag name"
            className="w-full px-4 py-3 bg-white/80 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
            required
          />
          <input
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="Slug (optional)"
            className="w-full px-4 py-3 bg-white/80 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
          />
          <button
            type="submit"
            disabled={creating}
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#1f1d1a] text-[#fbf8f1] disabled:opacity-50"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {creating ? 'Creating...' : 'Create'}
          </button>
        </form>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or slug"
            className="w-full md:w-80 px-4 py-2.5 bg-white/80 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
          />
          <div className="flex items-center gap-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'post_count')}
              className="px-3 py-2.5 bg-white/80 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
            >
              <option value="name">Sort: Name</option>
              <option value="post_count">Sort: Post Count</option>
            </select>
            <span className="text-sm text-ink-muted">
              {filteredTags.length} result{filteredTags.length === 1 ? '' : 's'}
            </span>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-ink-muted">
            <button
              type="button"
              onClick={selectAllVisible}
              className="px-3 py-1.5 rounded-lg border border-line hover:text-ink"
            >
              Select Visible
            </button>
            <button
              type="button"
              onClick={clearVisibleSelection}
              className="px-3 py-1.5 rounded-lg border border-line hover:text-ink"
            >
              Clear Visible
            </button>
            <span>{selectedVisibleCount} selected</span>
          </div>
          <button
            type="button"
            onClick={handleBatchDelete}
            disabled={batchDeleting || selectedVisibleCount === 0}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#a6502e]/30 text-[#7d3d22] disabled:opacity-50"
          >
            {batchDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            Delete Selected
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {filteredTags.map((item) => (
            <div key={item.id} className="rounded-2xl border border-line bg-white/70 px-4 py-3 flex items-center justify-between gap-4">
              {editingId === item.id ? (
                <div className="w-full grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 items-center">
                  <input
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40"
                  />
                  <input
                    value={editingSlug}
                    onChange={(e) => setEditingSlug(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40 font-mono"
                  />
                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => handleCancelEdit()}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-line text-ink-muted"
                    >
                      <X className="w-4 h-4" />
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSaveEdit(item.id)}
                      disabled={updatingId === item.id}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1f1d1a] text-[#fbf8f1] disabled:opacity-50"
                    >
                      {updatingId === item.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={() => toggleSelect(item.id)}
                    />
                    <div>
                      <p className="text-ink font-medium">{item.name}</p>
                      <p className="text-sm text-ink-muted font-mono">
                        {item.slug}
                        {typeof item.post_count === 'number' ? ` · ${item.post_count} posts` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleStartEdit(item)}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-line text-ink-muted"
                    >
                      <Pencil className="w-4 h-4" />
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(item.id)}
                      disabled={deletingId === item.id}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#a6502e]/30 text-[#7d3d22] disabled:opacity-50"
                    >
                      {deletingId === item.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      Delete
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}

          {filteredTags.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-white/60 p-8 text-center text-ink-muted">
              No tags matched your search.
            </div>
          ) : null}
        </div>
      </div>
    </PageTransition>
  );
}
