'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { type AdminSetting, fetchAdminSettings, updateAdminSetting } from '@/lib/api/admin';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type DraftMap = Record<string, string>;
type SavingMap = Record<string, boolean>;
type ErrorMap = Record<string, string>;

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<AdminSetting[]>([]);
  const [drafts, setDrafts] = useState<DraftMap>({});
  const [saving, setSaving] = useState<SavingMap>({});
  const [itemErrors, setItemErrors] = useState<ErrorMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('admin_access_token');
    if (!token) {
      window.location.href = '/admin';
      return;
    }

    fetchAdminSettings(token)
      .then((items) => {
        setSettings(items);
        const nextDrafts: DraftMap = {};
        items.forEach((item) => {
          nextDrafts[item.key] = item.value ?? '';
        });
        setDrafts(nextDrafts);
      })
      .catch((err) => {
        setError((err as Error).message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const sortedSettings = useMemo(() => {
    return [...settings].sort((a, b) => a.key.localeCompare(b.key));
  }, [settings]);

  const setDraftValue = (key: string, value: string) => {
    setDrafts((current) => ({ ...current, [key]: value }));
    setItemErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const handleSave = async (item: AdminSetting) => {
    const token = localStorage.getItem('admin_access_token') || '';
    if (!token) {
      setError('Missing admin session. Please login again.');
      return;
    }

    setSaving((current) => ({ ...current, [item.key]: true }));
    setItemErrors((current) => ({ ...current, [item.key]: '' }));

    try {
      const nextValue = drafts[item.key] ?? '';
      const saved = await updateAdminSetting(token, item.key, nextValue);
      setSettings((current) =>
        current.map((target) => (target.key === item.key ? saved : target))
      );
      setDrafts((current) => ({ ...current, [item.key]: saved.value ?? '' }));
    } catch (err) {
      setItemErrors((current) => ({
        ...current,
        [item.key]: (err as Error).message,
      }));
    } finally {
      setSaving((current) => ({ ...current, [item.key]: false }));
    }
  };

  if (loading) {
    return (
      <PageTransition className="pt-10 pb-20 max-w-5xl mx-auto">
        <div className="card-surface rounded-4xl p-8 flex items-center gap-3 text-ink-muted">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading settings...
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="pt-10 pb-20 max-w-5xl mx-auto">
      <div className="mb-6">
        <Link
          href="/admin"
          className="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-ink transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to admin
        </Link>
      </div>

      <div className="card-surface rounded-4xl p-6 md:p-8">
        <h1 className="text-4xl leading-none">Site Settings</h1>
        <p className="text-ink-muted mt-2">Edit backend settings values directly.</p>

        {error ? (
          <div className="mt-5 rounded-xl border border-[#a6502e]/30 bg-[#a6502e]/10 p-3 text-sm text-[#7d3d22]">
            {error}
          </div>
        ) : null}

        <div className="mt-6 space-y-4">
          {sortedSettings.map((item) => {
            const currentDraft = drafts[item.key] ?? '';
            const isSaving = Boolean(saving[item.key]);
            const isChanged = currentDraft !== (item.value ?? '');

            return (
              <div key={item.id} className="rounded-2xl border border-line bg-white/70 p-4 md:p-5">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="font-mono text-sm text-ink">{item.key}</p>
                  <span className="text-xs text-ink-muted">
                    Updated: {new Date(item.updated_at).toLocaleString()}
                  </span>
                </div>

                <textarea
                  value={currentDraft}
                  onChange={(e) => setDraftValue(item.key, e.target.value)}
                  className="w-full px-4 py-3 bg-white/85 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40 min-h-24 resize-y font-mono text-sm"
                />

                {itemErrors[item.key] ? (
                  <p className="mt-2 text-sm text-[#7d3d22]">{itemErrors[item.key]}</p>
                ) : null}

                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    disabled={isSaving || !isChanged}
                    onClick={() => handleSave(item)}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1f1d1a] text-[#fbf8f1] disabled:opacity-50"
                  >
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {isSaving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            );
          })}

          {sortedSettings.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-white/60 p-8 text-center text-ink-muted">
              No settings found.
            </div>
          ) : null}
        </div>
      </div>
    </PageTransition>
  );
}
