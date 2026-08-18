// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  AccessError,
  getStripeBillingRecord,
  setStripeBilling,
  type BillingStatus,
  type Plan,
} from './access.ts';

const STRIPE_API = 'https://api.stripe.com/v1';
const WEBHOOK_TOLERANCE_SECONDS = 5 * 60;
const MAX_WEBHOOK_BYTES = 512 * 1024;
const STRIPE_TIMEOUT_MS = 10_000;
// Stripe accepts explicit Checkout expiry only when it is at least 30 minutes
// away. Five minutes cover the subscription search and provider/network skew.
export const STRIPE_CHECKOUT_LIFETIME_SECONDS = 35 * 60;
const ORGANIZATION_ID_PATTERN = /^org_[A-Za-z0-9_]{1,124}$/;
const SUBSCRIPTION_ID_PATTERN = /^sub_[A-Za-z0-9_]{1,250}$/;
const EVENT_ID_PATTERN = /^evt_[A-Za-z0-9_]{1,250}$/;
const CHECKOUT_SESSION_ID_PATTERN = /^cs_(?:test|live)_[A-Za-z0-9_]{1,250}$/;
const CUSTOMER_ID_PATTERN = /^cus_[A-Za-z0-9_]{1,250}$/;
const CHECKOUT_GENERATION_PATTERN = /^[A-Za-z0-9_-]{16,128}$/;
const INACTIVE_BILLING = new Set<BillingStatus>(['inactive', 'canceled']);

export interface StripeEnv {
  APP_ORIGIN: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  STRIPE_PRO_MONTHLY_PRICE_ID?: string;
  STRIPE_PRO_ANNUAL_PRICE_ID?: string;
  STRIPE_PRO_MONTHLY_LEGACY_PRICE_IDS?: string;
  STRIPE_PRO_ANNUAL_LEGACY_PRICE_IDS?: string;
  STRIPE_TEAM_MONTHLY_PRICE_ID?: string;
}

export interface BillingProviderState {
  externalCustomerId: string | null;
  externalSubscriptionId: string | null;
}

export interface CheckoutInput extends BillingProviderState {
  organizationId: string;
  organizationKind: 'personal' | 'team';
  email: string;
  plan: 'pro' | 'team';
  interval: 'monthly' | 'annual';
  billingStatus?: BillingStatus;
}

export interface StripeCheckoutAttempt {
  generation: string;
  expiresAtSeconds: number;
}

export interface StripeCheckoutSession {
  id: string;
  url: string;
  expiresAt: number;
}

export type StripeCheckoutStatus = 'open' | 'complete' | 'expired';

interface StripeSubscription {
  id?: string;
  customer?: string | { id?: string };
  status?: string;
  metadata?: Record<string, string>;
  current_period_end?: number;
  items?: {
    data?: Array<{
      current_period_end?: number;
      price?: { id?: string };
    }>;
  };
}

interface StripeEvent {
  id?: string;
  type?: string;
  livemode?: boolean;
  data?: { object?: StripeSubscription };
}

interface StripeSubscriptionSearch {
  data?: StripeSubscription[];
  has_more?: boolean;
}

type StripeFetch = (input: string | URL | Request, init?: RequestInit) => Promise<Response>;

export function stripeCheckoutAvailability(env: StripeEnv) {
  const enabled = Boolean(env.STRIPE_SECRET_KEY && env.STRIPE_WEBHOOK_SECRET);
  return {
    provider: 'stripe' as const,
    enabled,
    plans: {
      pro: {
        monthly: enabled && Boolean(env.STRIPE_PRO_MONTHLY_PRICE_ID),
        annual: enabled && Boolean(env.STRIPE_PRO_ANNUAL_PRICE_ID),
      },
      team: {
        // Team is priced per seat, but updating a membership and Stripe's
        // quantity cannot be made atomic without durable reconciliation.
        monthly: false,
        annual: false,
      },
    },
  };
}

export function stripePrice(
  env: StripeEnv,
  plan: 'pro' | 'team',
  interval: 'monthly' | 'annual',
): string | null {
  if (plan === 'pro' && interval === 'monthly') return env.STRIPE_PRO_MONTHLY_PRICE_ID || null;
  if (plan === 'pro' && interval === 'annual') return env.STRIPE_PRO_ANNUAL_PRICE_ID || null;
  if (plan === 'team' && interval === 'monthly') return env.STRIPE_TEAM_MONTHLY_PRICE_ID || null;
  return null;
}

export function validateStripeCheckoutInput(
  env: StripeEnv,
  input: CheckoutInput,
  attempt?: StripeCheckoutAttempt,
): { secret: string; price: string } {
  const secret = requiredStripeSecret(env);
  if (!ORGANIZATION_ID_PATTERN.test(input.organizationId)
      || (input.organizationKind !== 'personal' && input.organizationKind !== 'team')
      || typeof input.email !== 'string' || !input.email || input.email.length > 320
      || (input.plan !== 'pro' && input.plan !== 'team')
      || (input.interval !== 'monthly' && input.interval !== 'annual')
      || (input.externalCustomerId !== null
        && !CUSTOMER_ID_PATTERN.test(input.externalCustomerId))
      || (input.externalSubscriptionId !== null
        && !SUBSCRIPTION_ID_PATTERN.test(input.externalSubscriptionId))) {
    throw new AccessError(400, 'invalid_billing_checkout');
  }
  if (attempt && (!CHECKOUT_GENERATION_PATTERN.test(attempt.generation)
      || !Number.isSafeInteger(attempt.expiresAtSeconds))) {
    throw new AccessError(400, 'invalid_billing_checkout');
  }
  if ((input.organizationKind === 'personal' && input.plan !== 'pro')
      || (input.organizationKind === 'team' && input.plan !== 'team')) {
    throw new AccessError(400, 'billing_plan_mismatch');
  }
  if (input.plan === 'team') {
    throw new AccessError(409, 'billing_team_checkout_requires_seat_sync');
  }
  if (input.externalSubscriptionId
      && input.billingStatus !== 'inactive' && input.billingStatus !== 'canceled') {
    throw new AccessError(409, 'billing_subscription_already_exists');
  }
  const price = stripePrice(env, input.plan, input.interval);
  if (!price) throw new AccessError(503, 'billing_price_unavailable');
  return { secret, price };
}

export async function createStripeCheckout(
  env: StripeEnv,
  input: CheckoutInput,
  stripeFetch: StripeFetch = fetch,
  attempt: StripeCheckoutAttempt = {
    generation: crypto.randomUUID(),
    expiresAtSeconds: Math.floor(Date.now() / 1000) + STRIPE_CHECKOUT_LIFETIME_SECONDS,
  },
): Promise<StripeCheckoutSession> {
  const { secret, price } = validateStripeCheckoutInput(env, input, attempt);

  // Stripe only guarantees idempotency-key retention for at least 24 hours,
  // while a lost webhook can be retried for days. Reconcile that gap against
  // Stripe's subscription index before a new Checkout Session is created, so
  // stale local billing columns cannot create a second live subscription.
  const signal = AbortSignal.timeout(STRIPE_TIMEOUT_MS);
  await assertNoBlockingStripeSubscription(
    env, input.organizationId, secret, stripeFetch, signal,
  );

  const origin = new URL(env.APP_ORIGIN).origin;
  const body = new URLSearchParams({
    mode: 'subscription',
    success_url: `${origin}/?billing=success`,
    cancel_url: `${origin}/?billing=canceled`,
    client_reference_id: input.organizationId,
    'line_items[0][price]': price,
    'line_items[0][quantity]': '1',
    'metadata[organization_id]': input.organizationId,
    'metadata[plan]': input.plan,
    'metadata[interval]': input.interval,
    'subscription_data[metadata][organization_id]': input.organizationId,
    'subscription_data[metadata][plan]': input.plan,
    'subscription_data[metadata][interval]': input.interval,
    expires_at: String(attempt.expiresAtSeconds),
    allow_promotion_codes: 'true',
    billing_address_collection: 'auto',
  });
  if (input.externalCustomerId) body.set('customer', input.externalCustomerId);
  else body.set('customer_email', input.email);

  const session = await stripeRequest<{ id?: string; url?: string; expires_at?: number }>(
    '/checkout/sessions', secret, body, stripeFetch,
    await checkoutIdempotencyKey(input, attempt.generation), signal,
  );
  if (!session.id || !CHECKOUT_SESSION_ID_PATTERN.test(session.id)
      || !session.url || !session.url.startsWith('https://checkout.stripe.com/')
      || session.expires_at !== attempt.expiresAtSeconds) {
    throw new AccessError(502, 'billing_provider_invalid_response');
  }
  return { id: session.id, url: session.url, expiresAt: session.expires_at * 1000 };
}

export async function createStripePortal(
  env: StripeEnv,
  customerId: string | null,
  stripeFetch: StripeFetch = fetch,
): Promise<string> {
  if (!customerId) throw new AccessError(409, 'billing_customer_not_found');
  const origin = new URL(env.APP_ORIGIN).origin;
  const session = await stripeRequest<{ url?: string }>(
    '/billing_portal/sessions',
    requiredStripeSecret(env),
    new URLSearchParams({ customer: customerId, return_url: `${origin}/` }),
    stripeFetch,
  );
  if (!session.url || !session.url.startsWith('https://billing.stripe.com/')) {
    throw new AccessError(502, 'billing_provider_invalid_response');
  }
  return session.url;
}

export async function inspectStripeCheckoutSession(
  env: StripeEnv,
  organizationId: string,
  sessionId: string,
  stripeFetch: StripeFetch = fetch,
): Promise<StripeCheckoutStatus> {
  if (!ORGANIZATION_ID_PATTERN.test(organizationId)
      || !CHECKOUT_SESSION_ID_PATTERN.test(sessionId)) {
    throw new AccessError(400, 'invalid_billing_checkout');
  }
  const response = await stripeFetch(
    `${STRIPE_API}/checkout/sessions/${encodeURIComponent(sessionId)}`,
    {
      headers: { Authorization: `Bearer ${requiredStripeSecret(env)}` },
      signal: AbortSignal.timeout(STRIPE_TIMEOUT_MS),
    },
  );
  const session = await stripeResponse<{
    id?: string; client_reference_id?: string; status?: string;
  }>(response);
  if (session.id !== sessionId || session.client_reference_id !== organizationId
      || (session.status !== 'open' && session.status !== 'complete'
        && session.status !== 'expired')) {
    throw new AccessError(502, 'billing_provider_invalid_response');
  }
  return session.status;
}

export async function handleStripeWebhook(
  request: Request,
  env: StripeEnv & { DB: D1Database; NODE_RELAY: DurableObjectNamespace },
): Promise<Response> {
  if (!env.STRIPE_WEBHOOK_SECRET || !env.STRIPE_SECRET_KEY) {
    throw new AccessError(503, 'billing_not_configured');
  }
  const payload = await readBoundedBody(request, MAX_WEBHOOK_BYTES);
  const signature = request.headers.get('Stripe-Signature') || '';
  if (!await verifyStripeSignature(payload, signature, env.STRIPE_WEBHOOK_SECRET)) {
    throw new AccessError(400, 'stripe_signature_invalid');
  }
  let event: StripeEvent;
  try { event = JSON.parse(payload) as StripeEvent; } catch {
    throw new AccessError(400, 'stripe_event_invalid');
  }
  if (event.livemode !== env.STRIPE_SECRET_KEY.startsWith('sk_live_')) {
    throw new AccessError(400, 'stripe_mode_mismatch');
  }
  if (!event.type?.startsWith('customer.subscription.')) {
    return json({ received: true });
  }
  const eventSubscription = event.data?.object;
  const subscriptionId = eventSubscription?.id || '';
  const organizationId = eventSubscription?.metadata?.organization_id || '';
  const eventId = event.id || '';
  if (!EVENT_ID_PATTERN.test(eventId) || !SUBSCRIPTION_ID_PATTERN.test(subscriptionId)
      || !ORGANIZATION_ID_PATTERN.test(organizationId)) {
    throw new AccessError(400, 'stripe_event_invalid');
  }
  const coordinator = env.NODE_RELAY.get(env.NODE_RELAY.idFromName(`billing:${organizationId}`));
  const result = await coordinator.fetch(new Request('https://relay.internal/billing/enqueue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ eventId, organizationId, subscriptionId }),
  }));
  if (!result.ok) {
    const body = await result.json().catch(() => null) as { error?: string } | null;
    throw new AccessError(result.status, body?.error || 'billing_reconciliation_failed');
  }
  return json({ received: true });
}

export async function reconcileStripeSubscription(
  env: StripeEnv & { DB: D1Database },
  organizationId: string,
  subscriptionId: string,
  stripeFetch: StripeFetch = fetch,
  assertWriteCurrent: () => Promise<void> = async () => {},
): Promise<'updated' | 'ignored'> {
  if (!ORGANIZATION_ID_PATTERN.test(organizationId)
      || !SUBSCRIPTION_ID_PATTERN.test(subscriptionId)) {
    throw new AccessError(400, 'stripe_event_invalid');
  }
  const subscription = await stripeGetSubscription(
    subscriptionId, requiredStripeSecret(env), stripeFetch,
  );
  if (subscription.id !== subscriptionId) {
    throw new AccessError(502, 'billing_provider_invalid_response');
  }
  const mapped = subscriptionBillingState(subscription, env);
  if (mapped.organizationId !== organizationId) {
    throw new AccessError(400, 'stripe_organization_mismatch');
  }
  const current = await getStripeBillingRecord(env.DB, organizationId);
  if (current.kind !== 'personal') throw new AccessError(400, 'billing_plan_mismatch');
  if (current.externalSubscriptionId
      && current.externalSubscriptionId !== subscriptionId) {
    // A terminal event for an older subscription must never replace the
    // organization's current subscription pointer, even if both are canceled.
    if (INACTIVE_BILLING.has(mapped.status)) return 'ignored';
    if (!INACTIVE_BILLING.has(current.billingStatus)) {
      // The active event may legitimately be for a replacement subscription
      // whose predecessor was canceled before its webhook arrived. Re-read the
      // predecessor from Stripe while still inside the per-organization queue.
      const predecessor = await stripeGetSubscription(
        current.externalSubscriptionId, requiredStripeSecret(env), stripeFetch,
      );
      if (predecessor.id !== current.externalSubscriptionId) {
        throw new AccessError(502, 'billing_provider_invalid_response');
      }
      const predecessorState = subscriptionBillingState(predecessor, env);
      if (predecessorState.organizationId !== organizationId) {
        throw new AccessError(400, 'stripe_organization_mismatch');
      }
      if (!INACTIVE_BILLING.has(predecessorState.status)) return 'ignored';
      await assertWriteCurrent();
      await setStripeBilling(env.DB, organizationId, {
        plan: 'pro',
        interval: predecessorState.interval,
        status: predecessorState.status,
        externalCustomerId: predecessorState.customerId,
        externalSubscriptionId: predecessor.id,
        currentPeriodEnd: predecessorState.currentPeriodEnd,
      });
    }
  }
  await assertWriteCurrent();
  return setStripeBilling(env.DB, organizationId, {
    plan: 'pro',
    interval: mapped.interval,
    status: mapped.status,
    externalCustomerId: mapped.customerId,
    externalSubscriptionId: subscription.id || subscriptionId,
    currentPeriodEnd: mapped.currentPeriodEnd,
  });
}

export async function verifyStripeSignature(
  payload: string,
  header: string,
  secret: string,
  nowSeconds = Math.floor(Date.now() / 1000),
): Promise<boolean> {
  const fields = header.split(',').map((entry) => entry.trim().split('=', 2));
  const timestamp = Number(fields.find(([key]) => key === 't')?.[1]);
  const signatures = fields.filter(([key]) => key === 'v1').map(([, value]) => value);
  if (!Number.isInteger(timestamp) || Math.abs(nowSeconds - timestamp) > WEBHOOK_TOLERANCE_SECONDS
      || !signatures.length) return false;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const digest = await crypto.subtle.sign(
    'HMAC', key, new TextEncoder().encode(`${timestamp}.${payload}`),
  );
  const expected = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  return signatures.some((candidate) => constantTimeEqual(candidate, expected));
}

export function subscriptionBillingState(subscription: StripeSubscription, env: StripeEnv) {
  const items = subscription.items?.data || [];
  if (items.length !== 1) throw new AccessError(400, 'stripe_subscription_shape_invalid');
  const priceId = items[0]?.price?.id || '';
  const matchedIntervals = (['monthly', 'annual'] as const).filter((interval) => (
    recognizedProPriceIds(env, interval).has(priceId)
  ));
  if (matchedIntervals.length !== 1) throw new AccessError(400, 'stripe_price_unrecognized');
  const organizationId = subscription.metadata?.organization_id || '';
  if (!ORGANIZATION_ID_PATTERN.test(organizationId)) {
    throw new AccessError(400, 'stripe_organization_invalid');
  }
  const customer = typeof subscription.customer === 'string'
    ? subscription.customer : subscription.customer?.id;
  if (!customer) throw new AccessError(400, 'stripe_customer_invalid');
  return {
    organizationId,
    plan: 'pro' as Exclude<Plan, 'free' | 'enterprise'>,
    interval: matchedIntervals[0],
    status: stripeBillingStatus(subscription.status || ''),
    customerId: customer,
    currentPeriodEnd: subscription.current_period_end
      || subscription.items?.data?.[0]?.current_period_end || null,
  };
}

function recognizedProPriceIds(
  env: StripeEnv,
  interval: 'monthly' | 'annual',
): Set<string> {
  const current = interval === 'monthly'
    ? env.STRIPE_PRO_MONTHLY_PRICE_ID : env.STRIPE_PRO_ANNUAL_PRICE_ID;
  const legacy = interval === 'monthly'
    ? env.STRIPE_PRO_MONTHLY_LEGACY_PRICE_IDS : env.STRIPE_PRO_ANNUAL_LEGACY_PRICE_IDS;
  return new Set([current || '', ...(legacy || '').split(',').map((id) => id.trim())].filter(Boolean));
}

export function stripeBillingStatus(status: string): BillingStatus {
  if (status === 'active') return 'active';
  if (status === 'trialing') return 'trialing';
  if (status === 'canceled' || status === 'incomplete_expired') return 'canceled';
  // incomplete and paused subscriptions can still become billable. Treat them,
  // and any future unknown Stripe state, as recoverable rather than allowing a
  // second Checkout subscription to be created alongside them.
  return 'past_due';
}

async function stripeGetSubscription(
  id: string,
  secret: string,
  stripeFetch: StripeFetch,
): Promise<StripeSubscription> {
  const response = await stripeFetch(`${STRIPE_API}/subscriptions/${encodeURIComponent(id)}`, {
    headers: { Authorization: `Bearer ${secret}` },
    signal: AbortSignal.timeout(STRIPE_TIMEOUT_MS),
  });
  return stripeResponse<StripeSubscription>(response);
}

async function assertNoBlockingStripeSubscription(
  env: StripeEnv,
  organizationId: string,
  secret: string,
  stripeFetch: StripeFetch,
  signal: AbortSignal,
): Promise<void> {
  const query = new URLSearchParams({
    query: `metadata['organization_id']:'${organizationId}'`,
    limit: '100',
  });
  const response = await stripeFetch(`${STRIPE_API}/subscriptions/search?${query}`, {
    headers: { Authorization: `Bearer ${secret}` },
    signal,
  });
  const search = await stripeResponse<StripeSubscriptionSearch>(response);
  if (!Array.isArray(search.data) || search.has_more) {
    throw new AccessError(502, 'billing_provider_invalid_response');
  }
  for (const subscription of search.data) {
    const organization = subscription.metadata?.organization_id || '';
    if (!SUBSCRIPTION_ID_PATTERN.test(subscription.id || '')
        || organization !== organizationId) {
      throw new AccessError(502, 'billing_provider_invalid_response');
    }
    // A terminal subscription can safely stop blocking Checkout even after its
    // archived Price ID has left the compatibility allowlist. Non-terminal
    // subscriptions must still map to an explicitly trusted current/legacy
    // price before they are allowed to influence billing state.
    if (subscription.status === 'canceled' || subscription.status === 'incomplete_expired') continue;
    const mapped = subscriptionBillingState(subscription, env);
    if (mapped.organizationId !== organizationId) {
      throw new AccessError(502, 'billing_provider_invalid_response');
    }
    if (!INACTIVE_BILLING.has(mapped.status)) {
      throw new AccessError(409, 'billing_subscription_already_exists');
    }
  }
}

async function stripeRequest<T>(
  path: string,
  secret: string,
  body: URLSearchParams,
  stripeFetch: StripeFetch,
  idempotencyKey?: string,
  signal: AbortSignal = AbortSignal.timeout(STRIPE_TIMEOUT_MS),
): Promise<T> {
  const response = await stripeFetch(`${STRIPE_API}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${secret}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    },
    body,
    signal,
  });
  return stripeResponse<T>(response);
}

async function checkoutIdempotencyKey(
  input: CheckoutInput,
  generation: string,
): Promise<string> {
  // The per-organization Durable Object persists generation before this key is
  // used. All retries for one reserved Checkout therefore replay the exact
  // Stripe request, while a replacement generation is created only after the
  // explicitly short-lived Checkout Session has expired.
  const keyMaterial = [
    'agentsight-checkout-v2',
    input.organizationId,
    input.plan,
    input.interval,
    generation,
  ].join(':');
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(keyMaterial));
  return `agentsight-${Array.from(new Uint8Array(digest), (byte) => (
    byte.toString(16).padStart(2, '0')
  )).join('')}`;
}

async function stripeResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null) as (T & { error?: { code?: string } }) | null;
  if (!response.ok || !body) {
    console.error(JSON.stringify({
      event: 'stripe_api_failed', status: response.status, code: body?.error?.code || 'invalid_response',
    }));
    throw new AccessError(502, 'billing_provider_failed');
  }
  return body;
}

function requiredStripeSecret(env: StripeEnv): string {
  if (!env.STRIPE_SECRET_KEY || !env.STRIPE_WEBHOOK_SECRET) {
    throw new AccessError(503, 'billing_not_configured');
  }
  return env.STRIPE_SECRET_KEY;
}

async function readBoundedBody(request: Request, maxBytes: number): Promise<string> {
  const declared = Number(request.headers.get('Content-Length') || '0');
  if (declared > maxBytes) throw new AccessError(413, 'request_too_large');
  if (!request.body) return '';
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > maxBytes) {
        await reader.cancel();
        throw new AccessError(413, 'request_too_large');
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const joined = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    joined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(joined);
}

function constantTimeEqual(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

function json(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
