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

const LOGIN_PROVIDERS: Array<{ id: LoginProvider; label: string }> = [
  { id: 'github', label: 'GitHub' },
  { id: 'google', label: 'Google' },
];

export function ConnectionDialog({
  error, busy, allowSignIn, canClose, onClose, onDemo,
}: ConnectionDialogProps) {
  const { t } = useTranslation();
  const [providers, setProviders] = useState<LoginProvider[] | null>(null);
  const [providerError, setProviderError] = useState('');

  useEffect(() => {
    if (!allowSignIn) return;
    setProviders(null);
    setProviderError('');
    void fetchLoginProviders()
      .then(setProviders)
      .catch((cause) => {
        setProviderError(cause instanceof Error ? cause.message : 'Could not read Controller sign-in status.');
      });
  }, [allowSignIn]);

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

        <div className={`grid gap-4 ${allowSignIn ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">{t('connect.nodeTitle')}</h2>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-950 px-3 py-2 text-xs text-white">agentsight bind</pre>
            <p className="mt-3 text-xs text-slate-500">{t('connect.nodeArgs')}</p>
          </section>

          {allowSignIn && <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">{t('connect.signInTitle')}</h2>
            <div className="mt-4 space-y-3">
              {LOGIN_PROVIDERS.map(({ id, label }) => {
                const configured = providers?.includes(id) === true;
                const checking = providers === null && !providerError;
                return <div key={id}>
                  <button type="button" disabled={busy || !configured}
                    onClick={() => { void startLogin(id); }}
                    className={`block w-full rounded-lg px-3 py-2 text-center text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${
                      id === 'github'
                        ? 'bg-slate-950 text-white hover:bg-slate-800'
                        : 'border border-slate-300 text-slate-800 hover:bg-slate-50'
                    }`}>
                    {id === 'github' ? t('connect.github') : t('connect.google')}
                  </button>
                  {!configured && <p className={`mt-1 text-xs ${providerError ? 'text-red-600' : 'text-slate-500'}`}>
                    {providerError
                      ? `${label} sign-in status unavailable: ${providerError}`
                      : checking
                        ? `Checking ${label} sign-in configuration…`
                        : `${label} sign-in is unavailable because its OAuth credentials are not configured on the Controller.`}
                  </p>}
                </div>;
              })}
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
