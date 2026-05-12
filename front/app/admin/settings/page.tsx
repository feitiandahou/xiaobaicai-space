'use client';

import { PageTransition } from '@/components/layout/PageTransition';
import { type AdminSetting, fetchAdminSettings, updateAdminSetting } from '@/lib/api/admin';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type DraftMap = Record<string, string>;
type SavingMap = Record<string, boolean>;
type ErrorMap = Record<string, string>;

const DEFAULT_SETTINGS: AdminSetting[] = [
  { id: -1, key: 'site.title', value: 'My Blog', updated_at: new Date(0).toISOString() },
  { id: -2, key: 'site.subtitle', value: '', updated_at: new Date(0).toISOString() },
  { id: -3, key: 'site.description', value: '', updated_at: new Date(0).toISOString() },
  { id: -4, key: 'site.icp_beian', value: '', updated_at: new Date(0).toISOString() },
  { id: -5, key: 'site.social_links', value: '[]', updated_at: new Date(0).toISOString() },
  { id: -6, key: 'site.footer.text', value: '', updated_at: new Date(0).toISOString() },
  { id: -7, key: 'site.footer.copyright', value: '', updated_at: new Date(0).toISOString() },
  { id: -8, key: 'site.footer.links', value: '[]', updated_at: new Date(0).toISOString() },
];

const JSON_SETTING_KEYS = new Set(['site.social_links', 'site.footer.links']);

const SETTING_HELP: Record<string, { where: string; test: string }> = {
  'site.title': {
    where: 'Used in the browser tab title and as footer fallback text.',
    test: 'Save it, then refresh the homepage and check the browser tab title and footer text.',
  },
  'site.subtitle': {
    where: 'Shown in the homepage hero paragraph.',
    test: 'Save it, then refresh /. You should see the new subtitle under the main heading.',
  },
  'site.description': {
    where: 'Used in page metadata and SEO description, not as visible page copy.',
    test: 'Save it, refresh the page, then inspect the page source or browser devtools metadata.',
  },
  'site.icp_beian': {
    where: 'Stored in backend, but not rendered anywhere in the current frontend yet.',
    test: 'You can confirm it via the database or GET /api/v1/site-config for now.',
  },
  'site.social_links': {
    where: 'Stored in backend site config, but not rendered anywhere in the current frontend yet.',
    test: 'Save JSON, then verify it via GET /api/v1/site-config.',
  },
  'site.footer.text': {
    where: 'Shown in the footer when footer copyright is empty.',
    test: 'Save it, clear site.footer.copyright if needed, then refresh the page footer.',
  },
  'site.footer.copyright': {
    where: 'Shown in the footer with highest priority.',
    test: 'Save it, refresh any page, and check the bottom footer text.',
  },
  'site.footer.links': {
    where: 'Stored in backend site config, but not rendered anywhere in the current frontend yet.',
    test: 'Save JSON, then verify it via GET /api/v1/site-config.',
  },
};

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
        const nextSettings = items.length > 0 ? items : DEFAULT_SETTINGS;
        setSettings(nextSettings);
        const nextDrafts: DraftMap = {};
        nextSettings.forEach((item) => {
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
          {settings === DEFAULT_SETTINGS || settings.some((item) => item.id < 0) ? (
            <div className="rounded-2xl border border-[#1e5f63]/20 bg-[#1e5f63]/8 p-4 text-sm text-[#24575b]">
              Settings table is empty. The fields below are starter keys. Click Save on any item to create it in the backend.
            </div>
          ) : null}

          {sortedSettings.map((item) => {
            const currentDraft = drafts[item.key] ?? '';
            const isSaving = Boolean(saving[item.key]);
            const isChanged = currentDraft !== (item.value ?? '');

            return (
              <div key={item.id} className="rounded-2xl border border-line bg-white/70 p-4 md:p-5">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="font-mono text-sm text-ink">{item.key}</p>
                  {item.id > 0 ? (
                    <span className="text-xs text-ink-muted">
                      Updated: {new Date(item.updated_at).toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-xs text-ink-muted">Not created yet</span>
                  )}
                </div>

                {SETTING_HELP[item.key] ? (
                  <div className="mb-3 rounded-xl bg-black/5 px-3 py-2 text-xs text-ink-muted">
                    <p><span className="font-medium text-ink">Where:</span> {SETTING_HELP[item.key].where}</p>
                    <p className="mt-1"><span className="font-medium text-ink">Test:</span> {SETTING_HELP[item.key].test}</p>
                  </div>
                ) : null}

                <textarea
                  value={currentDraft}
                  onChange={(e) => setDraftValue(item.key, e.target.value)}
                  className="w-full px-4 py-3 bg-white/85 border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e5f63]/40 min-h-24 resize-y font-mono text-sm"
                  placeholder={JSON_SETTING_KEYS.has(item.key) ? '[]' : ''}
                />

                {JSON_SETTING_KEYS.has(item.key) ? (
                  <p className="mt-2 text-xs text-ink-muted">Use JSON array format, for example: [{'{"name":"GitHub","url":"https://github.com"}'}]</p>
                ) : null}

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
