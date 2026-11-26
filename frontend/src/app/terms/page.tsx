// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service · AgentSight',
  description: 'Terms for using the hosted AgentSight service.',
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-12 text-slate-800 sm:px-8">
      <a href={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/`}
        className="text-sm font-medium text-blue-700 hover:underline">← AgentSight</a>
      <h1 className="mt-6 text-3xl font-bold text-slate-950">Terms of Service</h1>
      <p className="mt-2 text-sm text-slate-500">Effective August 18, 2026</p>

      <div className="mt-8 space-y-8 text-sm leading-7">
        <section>
          <h2 className="text-lg font-semibold text-slate-950">Using AgentSight</h2>
          <p className="mt-2">
            These terms apply to the hosted AgentSight application and Controller. By using the
            hosted service, you agree to these terms. The separately distributed open-source
            software remains governed by its repository license.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Your account and Nodes</h2>
          <p className="mt-2">
            You are responsible for your OAuth account, Node credentials, organization members,
            and activity performed through them. Only connect machines and inspect sessions that
            you are authorized to access. Keep bootstrap keys and account access secure, and
            promptly remove access that is no longer needed.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Acceptable use</h2>
          <p className="mt-2">
            Do not use the service to access another person&apos;s systems or data without permission,
            disrupt the service, evade limits, distribute malware, violate law, or infringe the
            rights of others. We may restrict or suspend abusive access to protect users and the
            service.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Preview and paid plans</h2>
          <p className="mt-2">
            Hosted preview features and limits may change. When paid checkout is available, Stripe
            processes payment and provides the billing portal. Prices, billing interval, and any
            recurring terms are shown before purchase. You can manage or cancel a subscription in
            the portal; access may continue through the paid period as indicated there.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Service availability</h2>
          <p className="mt-2">
            We aim to operate the hosted service reliably, but it is provided on an “as is” and
            “as available” basis without a service-level guarantee. You should keep your own copies
            of important local data and not rely on AgentSight as the sole record of agent activity.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Liability</h2>
          <p className="mt-2">
            To the extent permitted by law, the AgentSight maintainers are not liable for indirect,
            incidental, special, consequential, or lost-profit damages arising from the hosted
            service. Nothing here excludes rights or liability that cannot legally be excluded.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Changes and contact</h2>
          <p className="mt-2">
            We may update these terms as the service changes and will revise the effective date.
            Questions can be sent to{' '}
            <a className="text-blue-700 hover:underline" href="mailto:yunwei356@gmail.com">yunwei356@gmail.com</a>.
          </p>
        </section>
      </div>
    </main>
  );
}
