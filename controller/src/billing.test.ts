// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { AccessError } from './access.ts';
import {
  createStripeCheckout,
  createStripePortal,
  handleStripeWebhook,
  reconcileStripeSubscription,
  stripeBillingStatus,
  stripeCheckoutAvailability,
  subscriptionBillingState,
  verifyStripeSignature,
  type StripeEnv,
} from './billing.ts';

const stripeEnv: StripeEnv = {
  APP_ORIGIN: 'https://app.agentsight.us',
  STRIPE_SECRET_KEY: 'sk_test_example',
  STRIPE_WEBHOOK_SECRET: 'whsec_example',
  STRIPE_PRO_MONTHLY_PRICE_ID: 'price_pro_monthly',
  STRIPE_PRO_ANNUAL_PRICE_ID: 'price_pro_annual',
  STRIPE_TEAM_MONTHLY_PRICE_ID: 'price_team_monthly',
};

test('Stripe checkout availability is fail-closed and price-specific', () => {
  assert.equal(stripeCheckoutAvailability({ APP_ORIGIN: stripeEnv.APP_ORIGIN }).enabled, false);
  const availability = stripeCheckoutAvailability(stripeEnv);
  assert.equal(availability.enabled, true);
  assert.equal(availability.plans.pro.monthly, true);
  assert.equal(availability.plans.pro.annual, true);
  assert.equal(availability.plans.team.monthly, false);
  assert.equal(availability.plans.team.annual, false);
});

test('Checkout binds the organization and subscription metadata to a configured price', async () => {
  let requestBody: URLSearchParams | null = null;
  let idempotencyKey = '';
  const url = await createStripeCheckout(stripeEnv, {
    organizationId: 'org_personal_user1',
    organizationKind: 'personal',
    email: 'owner@example.com',
    plan: 'pro',
    interval: 'annual',
    externalCustomerId: null,
    externalSubscriptionId: null,
  }, async (_input, init) => {
    if (String(_input).includes('/subscriptions/search?')) {
      return Response.json({ data: [], has_more: false });
    }
    requestBody = init?.body as URLSearchParams;
    idempotencyKey = new Headers(init?.headers).get('Idempotency-Key') || '';
    return Response.json({ url: 'https://checkout.stripe.com/c/pay/test' });
  });
  assert.equal(url, 'https://checkout.stripe.com/c/pay/test');
  assert.ok(requestBody);
  const body = requestBody as URLSearchParams;
  assert.equal(body.get('line_items[0][price]'), 'price_pro_annual');
  assert.equal(body.get('customer_email'), 'owner@example.com');
  assert.equal(body.get('subscription_data[metadata][organization_id]'), 'org_personal_user1');
  assert.equal(body.get('success_url'), 'https://app.agentsight.us/?billing=success');
  assert.match(idempotencyKey, /^agentsight-[a-f0-9]{64}$/);

  await assert.rejects(
    createStripeCheckout(stripeEnv, {
      organizationId: 'org_personal_user1', organizationKind: 'personal', email: 'owner@example.com',
      plan: 'team', interval: 'monthly', externalCustomerId: null,
      externalSubscriptionId: null,
    }),
    (error: unknown) => error instanceof AccessError && error.message === 'billing_plan_mismatch',
  );
});

test('Concurrent Checkout choices share one Stripe idempotency generation', async () => {
  const keys: string[] = [];
  const requests = new Map<string, string>();
  let sessionsCreated = 0;
  const checkout = (interval: 'monthly' | 'annual') => createStripeCheckout(stripeEnv, {
    organizationId: 'org_personal_user1', organizationKind: 'personal', email: 'owner@example.com',
    plan: 'pro', interval, externalCustomerId: null, externalSubscriptionId: null,
    billingStatus: 'inactive',
  }, async (_input, init) => {
    if (String(_input).includes('/subscriptions/search?')) {
      return Response.json({ data: [], has_more: false });
    }
    const key = new Headers(init?.headers).get('Idempotency-Key') || '';
    const params = String(init?.body);
    keys.push(key);
    const existing = requests.get(key);
    if (existing && existing !== params) {
      return Response.json({ error: { type: 'idempotency_error' } }, { status: 400 });
    }
    requests.set(key, params);
    sessionsCreated += 1;
    return Response.json({ url: 'https://checkout.stripe.com/c/pay/test' });
  });
  const results = await Promise.allSettled([checkout('monthly'), checkout('annual')]);
  assert.equal(keys.length, 2);
  assert.equal(keys[0], keys[1]);
  assert.equal(results.filter((result) => result.status === 'fulfilled').length, 1);
  assert.equal(results.filter((result) => result.status === 'rejected').length, 1);
  assert.equal(sessionsCreated, 1);
});

test('Team checkout fails closed until seat quantity can be reconciled', async () => {
  await assert.rejects(createStripeCheckout(stripeEnv, {
    organizationId: 'org_team1', organizationKind: 'team', email: 'owner@example.com',
    plan: 'team', interval: 'monthly', externalCustomerId: 'cus_existing',
    externalSubscriptionId: null,
  }), (error: unknown) => error instanceof AccessError
    && error.message === 'billing_team_checkout_requires_seat_sync');
});

test('Portal sessions require an existing Stripe customer', async () => {
  await assert.rejects(
    createStripePortal(stripeEnv, null),
    (error: unknown) => error instanceof AccessError && error.message === 'billing_customer_not_found',
  );
  const url = await createStripePortal(stripeEnv, 'cus_existing', async (_input, init) => {
    assert.equal((init?.body as URLSearchParams).get('return_url'), 'https://app.agentsight.us/');
    return Response.json({ url: 'https://billing.stripe.com/p/session/test' });
  });
  assert.equal(url, 'https://billing.stripe.com/p/session/test');
});

test('Checkout cannot create a second active subscription', async () => {
  await assert.rejects(createStripeCheckout(stripeEnv, {
    organizationId: 'org_personal_user1', organizationKind: 'personal', email: 'owner@example.com',
    plan: 'pro', interval: 'monthly', externalCustomerId: 'cus_existing',
    externalSubscriptionId: 'sub_existing', billingStatus: 'active',
  }), (error: unknown) => error instanceof AccessError
    && error.message === 'billing_subscription_already_exists');
});

test('Checkout finds a live Stripe subscription after local webhook state was lost', async () => {
  let checkoutPosts = 0;
  await assert.rejects(createStripeCheckout(stripeEnv, {
    organizationId: 'org_personal_user1', organizationKind: 'personal', email: 'owner@example.com',
    plan: 'pro', interval: 'monthly', externalCustomerId: null,
    externalSubscriptionId: null, billingStatus: 'inactive',
  }, async (input, init) => {
    const url = new URL(String(input));
    if (url.pathname === '/v1/subscriptions/search') {
      assert.equal(url.searchParams.get('query'), "metadata['organization_id']:'org_personal_user1'");
      assert.equal(new Headers(init?.headers).get('Authorization'), 'Bearer sk_test_example');
      return Response.json({
        data: [{
          id: 'sub_webhook_lost', customer: 'cus_test', status: 'active',
          metadata: { organization_id: 'org_personal_user1' },
          items: { data: [{ price: { id: 'price_pro_monthly' } }] },
        }],
        has_more: false,
      });
    }
    checkoutPosts += 1;
    return Response.json({ url: 'https://checkout.stripe.com/c/pay/duplicate' });
  }), (error: unknown) => error instanceof AccessError
    && error.message === 'billing_subscription_already_exists');
  assert.equal(checkoutPosts, 0);
});

test('Stripe signatures require the exact payload and a recent timestamp', async () => {
  const payload = JSON.stringify({ id: 'evt_test' });
  const timestamp = 1_800_000_000;
  const signature = await stripeSignature(payload, timestamp, stripeEnv.STRIPE_WEBHOOK_SECRET!);
  assert.equal(await verifyStripeSignature(
    payload, `t=${timestamp},v1=${signature}`, stripeEnv.STRIPE_WEBHOOK_SECRET!, timestamp,
  ), true);
  assert.equal(await verifyStripeSignature(
    `${payload} `, `t=${timestamp},v1=${signature}`, stripeEnv.STRIPE_WEBHOOK_SECRET!, timestamp,
  ), false);
  assert.equal(await verifyStripeSignature(
    payload, `t=${timestamp},v1=${signature}`, stripeEnv.STRIPE_WEBHOOK_SECRET!, timestamp + 301,
  ), false);
});

test('Subscription state is derived from configured prices rather than untrusted plan metadata', () => {
  const mapped = subscriptionBillingState({
    id: 'sub_test', customer: 'cus_test', status: 'active', current_period_end: 1_900_000_000,
    metadata: { organization_id: 'org_personal_user1', plan: 'team' },
    items: { data: [{ price: { id: 'price_pro_monthly' } }] },
  }, stripeEnv);
  assert.equal(mapped.plan, 'pro');
  assert.equal(mapped.interval, 'monthly');
  assert.equal(mapped.status, 'active');
  const legacy = subscriptionBillingState({
    id: 'sub_legacy', customer: 'cus_test', status: 'active',
    metadata: { organization_id: 'org_personal_user1' },
    items: { data: [{ price: { id: 'price_pro_monthly_legacy' } }] },
  }, { ...stripeEnv, STRIPE_PRO_MONTHLY_LEGACY_PRICE_IDS: 'price_older, price_pro_monthly_legacy' });
  assert.equal(legacy.interval, 'monthly');
  assert.equal(stripeBillingStatus('unpaid'), 'past_due');
  assert.equal(stripeBillingStatus('incomplete'), 'past_due');
  assert.throws(
    () => subscriptionBillingState({
      customer: 'cus_test', status: 'active', metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_attacker' } }] },
    }, stripeEnv),
    (error: unknown) => error instanceof AccessError && error.message === 'stripe_price_unrecognized',
  );
  assert.throws(
    () => subscriptionBillingState({
      customer: 'cus_test', status: 'active', metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_ambiguous' } }] },
    }, {
      ...stripeEnv,
      STRIPE_PRO_MONTHLY_LEGACY_PRICE_IDS: 'price_ambiguous',
      STRIPE_PRO_ANNUAL_LEGACY_PRICE_IDS: 'price_ambiguous',
    }),
    (error: unknown) => error instanceof AccessError && error.message === 'stripe_price_unrecognized',
  );
  assert.throws(
    () => subscriptionBillingState({
      customer: 'cus_test', status: 'active', metadata: { organization_id: 'org_personal_user1' },
      items: { data: [
        { price: { id: 'price_pro_monthly' } },
        { price: { id: 'price_pro_annual' } },
      ] },
    }, stripeEnv),
    (error: unknown) => error instanceof AccessError
      && error.message === 'stripe_subscription_shape_invalid',
  );
  assert.throws(
    () => subscriptionBillingState({
      id: 'sub_team', customer: 'cus_test', status: 'active',
      metadata: { organization_id: 'org_team1' },
      items: { data: [{ price: { id: 'price_team_monthly' } }] },
    }, stripeEnv),
    (error: unknown) => error instanceof AccessError && error.message === 'stripe_price_unrecognized',
  );
});

test('Only terminal Stripe states allow a replacement Checkout', () => {
  assert.equal(stripeBillingStatus('canceled'), 'canceled');
  assert.equal(stripeBillingStatus('incomplete_expired'), 'canceled');
  assert.equal(stripeBillingStatus('incomplete'), 'past_due');
  assert.equal(stripeBillingStatus('paused'), 'past_due');
  assert.equal(stripeBillingStatus('future_recoverable_state'), 'past_due');
});

test('Verified subscription webhook routes reconciliation through the organization coordinator', async () => {
  const event = JSON.stringify({
    id: 'evt_test', type: 'customer.subscription.updated', livemode: false,
    data: { object: { id: 'sub_test', metadata: { organization_id: 'org_personal_user1' } } },
  });
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = await stripeSignature(event, timestamp, stripeEnv.STRIPE_WEBHOOK_SECRET!);
  let coordinatorName = '';
  let coordinatorBody: unknown;
  const relay = {
    idFromName: (name: string) => {
      coordinatorName = name;
      return {} as DurableObjectId;
    },
    get: () => ({
      fetch: async (request: Request) => {
        coordinatorBody = await request.json();
        return Response.json({ queued: true }, { status: 202 });
      },
    }) as unknown as DurableObjectStub,
  } as unknown as DurableObjectNamespace;
  const response = await handleStripeWebhook(new Request('https://control.agentsight.us/v1/billing/webhook', {
    method: 'POST', body: event, headers: { 'Stripe-Signature': `t=${timestamp},v1=${signature}` },
  }), { ...stripeEnv, DB: {} as D1Database, NODE_RELAY: relay });
  assert.equal(response.status, 200);
  assert.equal(coordinatorName, 'billing:org_personal_user1');
  assert.deepEqual(coordinatorBody, {
    eventId: 'evt_test', organizationId: 'org_personal_user1', subscriptionId: 'sub_test',
  });
});

test('Reconciliation fetches current Stripe state and updates existing columns without a migration', async () => {
  let query = '';
  let bound: unknown[] = [];
  const db = {
    prepare: (sql: string) => {
      query = sql;
      return {
        bind: (...values: unknown[]) => ({
          first: async () => ({
            kind: 'personal', billing_status: 'inactive', external_subscription_id: null,
          }),
          run: async () => {
            bound = values;
            return { success: true, meta: { changes: 1 } };
          },
        }),
      };
    },
  } as unknown as D1Database;
  const result = await reconcileStripeSubscription({ ...stripeEnv, DB: db },
    'org_personal_user1', 'sub_test', async () => Response.json({
    id: 'sub_test', customer: 'cus_test', status: 'trialing', current_period_end: 1_900_000_000,
    metadata: { organization_id: 'org_personal_user1' },
    items: { data: [{ price: { id: 'price_pro_annual' } }] },
  }));
  assert.equal(result, 'updated');
  assert.match(query, /external_subscription_id = \?5/);
  assert.deepEqual(bound.slice(0, 6), [
    'pro', 'annual', 'trialing', 'cus_test', 'sub_test', 1_900_000_000,
  ]);
  assert.equal(bound.at(-1), 'org_personal_user1');
});

test('A stale or duplicate subscription cannot replace a different active subscription', async () => {
  const queries: string[] = [];
  const db = {
    prepare: (query: string) => {
      queries.push(query);
      return {
        bind: () => ({
          run: async () => ({ success: true, meta: { changes: 0 } }),
          first: async () => ({
            kind: 'personal', billing_status: 'active', external_subscription_id: 'sub_current',
          }),
        }),
      };
    },
  } as unknown as D1Database;
  const result = await reconcileStripeSubscription({ ...stripeEnv, DB: db },
    'org_personal_user1', 'sub_stale', async () => Response.json({
      id: 'sub_stale', customer: 'cus_test', status: 'canceled', current_period_end: 1_900_000_000,
      metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_pro_monthly' } }] },
    }));
  assert.equal(result, 'ignored');
  assert.equal(queries.length, 1);
  assert.match(queries[0], /SELECT kind, billing_status, external_subscription_id/);
});

test('A replacement subscription can activate when Stripe shows its predecessor is canceled', async () => {
  const state = {
    kind: 'personal',
    billingStatus: 'active',
    externalSubscriptionId: 'sub_old' as string | null,
  };
  const updates: Array<{ status: unknown; subscriptionId: unknown }> = [];
  const db = {
    prepare: (query: string) => ({
      bind: (...values: unknown[]) => ({
        first: async () => ({
          kind: state.kind,
          billing_status: state.billingStatus,
          external_subscription_id: state.externalSubscriptionId,
        }),
        run: async () => {
          if (!query.startsWith('UPDATE organizations')) throw new Error('unexpected write');
          const status = values[2] as 'inactive' | 'trialing' | 'active' | 'past_due' | 'canceled';
          const subscriptionId = values[4] as string;
          const allowed = state.externalSubscriptionId === null
            || state.externalSubscriptionId === subscriptionId
            || state.billingStatus === 'inactive'
            || state.billingStatus === 'canceled';
          if (allowed) {
            state.billingStatus = status;
            state.externalSubscriptionId = subscriptionId;
            updates.push({ status, subscriptionId });
          }
          return { success: true, meta: { changes: allowed ? 1 : 0 } };
        },
      }),
    }),
  } as unknown as D1Database;
  const fetched: string[] = [];
  const result = await reconcileStripeSubscription({ ...stripeEnv, DB: db },
    'org_personal_user1', 'sub_new', async (input) => {
      const id = new URL(String(input)).pathname.split('/').pop()!;
      fetched.push(id);
      return Response.json({
        id,
        customer: 'cus_test',
        status: id === 'sub_old' ? 'canceled' : 'active',
        metadata: { organization_id: 'org_personal_user1' },
        items: { data: [{ price: { id: 'price_pro_monthly' } }] },
      });
    });
  assert.equal(result, 'updated');
  assert.deepEqual(fetched, ['sub_new', 'sub_old']);
  assert.deepEqual(updates, [
    { status: 'canceled', subscriptionId: 'sub_old' },
    { status: 'active', subscriptionId: 'sub_new' },
  ]);
  assert.equal(state.externalSubscriptionId, 'sub_new');
  assert.equal(state.billingStatus, 'active');
});

test('A stale Durable Object instance is fenced after Stripe reads and before D1 writes', async () => {
  let writes = 0;
  const db = {
    prepare: (query: string) => ({
      bind: () => ({
        first: async () => ({
          kind: 'personal', billing_status: 'active', external_subscription_id: 'sub_test',
        }),
        run: async () => {
          if (query.startsWith('UPDATE organizations')) writes += 1;
          return { success: true, meta: { changes: 1 } };
        },
      }),
    }),
  } as unknown as D1Database;

  await assert.rejects(reconcileStripeSubscription(
    { ...stripeEnv, DB: db },
    'org_personal_user1',
    'sub_test',
    async () => Response.json({
      id: 'sub_test', customer: 'cus_test', status: 'canceled',
      metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_pro_monthly' } }] },
    }),
    async () => { throw new Error('Durable Object is no longer current'); },
  ), /no longer current/);
  assert.equal(writes, 0);
});

test('Webhook rejects an oversized body before parsing or touching D1', async () => {
  let databaseTouched = false;
  const db = {
    prepare: () => {
      databaseTouched = true;
      throw new Error('unexpected D1 access');
    },
  } as unknown as D1Database;
  await assert.rejects(handleStripeWebhook(new Request(
    'https://control.agentsight.us/v1/billing/webhook',
    { method: 'POST', body: '{}', headers: { 'Content-Length': String(512 * 1024 + 1) } },
  ), { ...stripeEnv, DB: db, NODE_RELAY: {} as DurableObjectNamespace }), (error: unknown) => error instanceof AccessError
    && error.status === 413 && error.message === 'request_too_large');
  assert.equal(databaseTouched, false);
});

async function stripeSignature(payload: string, timestamp: number, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const digest = await crypto.subtle.sign(
    'HMAC', key, new TextEncoder().encode(`${timestamp}.${payload}`),
  );
  return Buffer.from(digest).toString('hex');
}
