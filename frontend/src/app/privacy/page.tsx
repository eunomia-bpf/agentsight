// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy · AgentSight',
  description: 'How the hosted AgentSight service handles account and coordination data.',
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-12 text-slate-800 sm:px-8">
      <a href={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/`}
        className="text-sm font-medium text-blue-700 hover:underline">← AgentSight</a>
      <h1 className="mt-6 text-3xl font-bold text-slate-950">Privacy Policy</h1>
      <p className="mt-2 text-sm text-slate-500">Effective August 18, 2026</p>

      <div className="mt-8 space-y-8 text-sm leading-7">
        <section>
          <h2 className="text-lg font-semibold text-slate-950">What this policy covers</h2>
          <p className="mt-2">
            This policy covers the hosted AgentSight application at app.agentsight.us and its
            Controller. The open-source AgentSight software can also run locally without a hosted
            account; data that stays on your own machine is controlled by you.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Data the hosted service stores</h2>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>OAuth identity details such as email, display name, avatar, and provider account ID.</li>
            <li>Organizations, memberships, roles, invitations, and registered Node metadata.</li>
            <li>Login sessions, short-lived OAuth state, and hashed Node or session credentials.</li>
            <li>Plan, entitlement, Stripe customer/subscription identifiers, and billing status.</li>
            <li>Short-lived Stripe Checkout reservation metadata used to prevent duplicate subscriptions.</li>
            <li>An optional Direct endpoint and bootstrap key only when you choose account sync; it is encrypted before storage.</li>
          </ul>
          <p className="mt-3">
            The Controller does not persist Node snapshots, session transcripts, prompts,
            responses, process activity, or relay response bodies. Those remain on the Node;
            relayed traffic is held in runtime memory only while a request is active.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">How data is used</h2>
          <p className="mt-2">
            We use this data to authenticate users, authorize organization access, coordinate
            Direct and relay connections, provide account recovery across browsers, operate
            subscriptions, prevent abuse, and diagnose service failures. We do not sell personal
            data or use private Node evidence to train models.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Service providers</h2>
          <p className="mt-2">
            Cloudflare hosts the application and Controller. GitHub or Google provides login when
            selected. Stripe processes checkout, payment, and subscription management. Their own
            privacy terms apply to the data they process.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Retention and your choices</h2>
          <p className="mt-2">
            Login sessions expire after 30 days. Expired OAuth state, authorization codes,
            sessions, and invitations are removed during sign-in maintenance. Account, organization, Node, and
            billing records remain while needed to provide the service or meet legal obligations.
            You can sign out, remove Nodes, delete an account-saved Direct configuration, manage
            billing through Stripe, or ask us to delete hosted account data.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Security and changes</h2>
          <p className="mt-2">
            We use scoped authorization, hashed bearer credentials, encrypted optional Direct
            configuration, and signed Stripe webhooks. No system is perfectly secure. We may
            update this policy as the service changes and will revise the effective date here.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-950">Contact</h2>
          <p className="mt-2">
            Privacy questions or deletion requests can be sent to{' '}
            <a className="text-blue-700 hover:underline" href="mailto:yunwei356@gmail.com">yunwei356@gmail.com</a>.
          </p>
        </section>
      </div>
    </main>
  );
}
