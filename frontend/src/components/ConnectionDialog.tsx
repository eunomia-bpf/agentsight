// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { useEffect, useState } from 'react';
import { fetchLoginProviders, startLogin, type LoginProvider } from '@/lib/controllerClient';
import { useTranslation } from '@/i18n';

interface ConnectionDialogProps {
  error: string;
  busy: boolean;
  allowSignIn: boolean;
  canClose: boolean;
  onClose?: () => void;
  onDemo: () => void;
}

export function ConnectionDialog({
  error, busy, allowSignIn, canClose, onClose, onDemo,
}: ConnectionDialogProps) {
  const { t } = useTranslation();
  const [providers, setProviders] = useState<LoginProvider[]>([]);

  useEffect(() => {
    if (!allowSignIn) return;
    void fetchLoginProviders().then(setProviders).catch(() => setProviders([]));
  }, [allowSignIn]);
  const signInVisible = allowSignIn && providers.length > 0;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-8">
      <div role="dialog" aria-modal="true" aria-labelledby="connect-title"
        className="relative w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl sm:p-8">
        {canClose && onClose && (
          <button type="button" onClick={onClose} aria-label={t('connect.close')}
            className="absolute right-5 top-4 text-2xl text-slate-400 hover:text-slate-700">
            ×
          </button>
        )}
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">AgentSight</p>
          <h1 id="connect-title" className="mt-1 text-2xl font-bold text-slate-950">{t('connect.title')}</h1>
        </div>

        {error && (
          <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <div className={`grid gap-4 ${signInVisible ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">{t('connect.nodeTitle')}</h2>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-950 px-3 py-2 text-xs text-white">agentsight bind</pre>
            <p className="mt-3 text-xs text-slate-500">{t('connect.nodeArgs')}</p>
          </section>

          {signInVisible && <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">{t('connect.signInTitle')}</h2>
            <div className="mt-4 space-y-2">
              {providers.includes('github') && <button type="button" onClick={() => { void startLogin('github'); }}
                className="block w-full rounded-lg bg-slate-950 px-3 py-2 text-center text-sm font-medium text-white hover:bg-slate-800">
                {t('connect.github')}
              </button>}
              {providers.includes('google') && <button type="button" onClick={() => { void startLogin('google'); }}
                className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-sm font-medium text-slate-800 hover:bg-slate-50">
                {t('connect.google')}
              </button>}
            </div>
          </section>}

          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">{t('connect.demoTitle')}</h2>
            <p className="mt-2 text-sm text-slate-600">{t('connect.demoBody')}</p>
            <button type="button" onClick={onDemo} disabled={busy}
              className="mt-4 w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {busy ? t('app.opening') : t('connect.demoAction')}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
