// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { type CloudIdentity, loginUrl } from '@/lib/connection';

interface ConnectionDialogProps {
  error: string;
  busy: boolean;
  identity: CloudIdentity | null;
  onDemo: () => void;
  onSignOut: () => void;
}

export function ConnectionDialog({ error, busy, identity, onDemo, onSignOut }: ConnectionDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-8">
      <div role="dialog" aria-modal="true" aria-labelledby="connect-title"
        className="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl sm:p-8">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">AgentSight</p>
          <h1 id="connect-title" className="mt-1 text-2xl font-bold text-slate-950">Choose how to continue</h1>
          <p className="mt-2 text-sm text-slate-600">
            Your detailed session data stays on the AgentSight Node unless you explicitly open it here.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">Bind this device</h2>
            <p className="mt-2 text-sm text-slate-600">Run this once. It opens a short-lived, single-use binding link.</p>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-950 px-3 py-2 text-xs text-white">agentsight bind</pre>
            <p className="mt-3 text-xs text-slate-500">The browser may ask for Local network access.</p>
          </section>

          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">Sign in</h2>
            {identity ? (
              <>
                <p className="mt-2 text-sm text-slate-600">
                  Signed in as <span className="font-medium text-slate-900">{identity.name || identity.email}</span>.
                  Bind this device to add it to your account.
                </p>
                <button type="button" onClick={onSignOut}
                  className="mt-4 text-sm font-medium text-slate-600 hover:text-slate-900">
                  Sign out
                </button>
              </>
            ) : (
              <>
                <p className="mt-2 text-sm text-slate-600">Keep a list of Nodes linked to your AgentSight account.</p>
                <div className="mt-4 space-y-2">
                  <a href={loginUrl('github')} className="block rounded-lg bg-slate-950 px-3 py-2 text-center text-sm font-medium text-white hover:bg-slate-800">
                    Continue with GitHub
                  </a>
                  <a href={loginUrl('google')} className="block rounded-lg border border-slate-300 px-3 py-2 text-center text-sm font-medium text-slate-800 hover:bg-slate-50">
                    Continue with Google
                  </a>
                </div>
              </>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-semibold text-slate-950">Explore the demo</h2>
            <p className="mt-2 text-sm text-slate-600">Open the retained recorded session without signing in or binding a device.</p>
            <button type="button" onClick={onDemo} disabled={busy}
              className="mt-4 w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {busy ? 'Loading…' : 'Enter demo'}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
