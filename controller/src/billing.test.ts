// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { AccessError } from './access.ts';
import {
  createStripeCheckout,
  createStripePortal,
  handleStripeWebhook,
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
  const url = await createStripeCheckout(stripeEnv, {
    organizationId: 'org_personal_user1',
    organizationKind: 'personal',
    email: 'owner@example.com',
    plan: 'pro',
    interval: 'annual',
    externalCustomerId: null,
    externalSubscriptionId: null,
  }, async (_input, init) => {
    requestBody = init?.body as URLSearchParams;
    return Response.json({ url: 'https://checkout.stripe.com/c/pay/test' });
  });
  assert.equal(url, 'https://checkout.stripe.com/c/pay/test');
  assert.ok(requestBody);
  const body = requestBody as URLSearchParams;
  assert.equal(body.get('line_items[0][price]'), 'price_pro_annual');
  assert.equal(body.get('customer_email'), 'owner@example.com');
  assert.equal(body.get('subscription_data[metadata][organization_id]'), 'org_personal_user1');
  assert.equal(body.get('success_url'), 'https://app.agentsight.us/?billing=success');

  await assert.rejects(
    createStripeCheckout(stripeEnv, {
      organizationId: 'org_personal_user1', organizationKind: 'personal', email: 'owner@example.com',
      plan: 'team', interval: 'monthly', externalCustomerId: null,
      externalSubscriptionId: null,
    }),
    (error: unknown) => error instanceof AccessError && error.message === 'billing_plan_mismatch',
  );
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
  assert.equal(stripeBillingStatus('unpaid'), 'past_due');
  assert.equal(stripeBillingStatus('incomplete'), 'inactive');
  assert.throws(
    () => subscriptionBillingState({
      customer: 'cus_test', status: 'active', metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_attacker' } }] },
    }, stripeEnv),
    (error: unknown) => error instanceof AccessError && error.message === 'stripe_price_unrecognized',
  );
});

test('Verified subscription webhook updates existing billing columns without a migration', async () => {
  const event = JSON.stringify({
    id: 'evt_test', type: 'customer.subscription.updated', livemode: false,
    data: { object: { id: 'sub_test' } },
  });
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = await stripeSignature(event, timestamp, stripeEnv.STRIPE_WEBHOOK_SECRET!);
  let bound: unknown[] = [];
  const db = {
    prepare: (_query: string) => ({
      bind: (...values: unknown[]) => ({
        run: async () => {
          bound = values;
          return { success: true, meta: { changes: 1 } };
        },
      }),
    }),
  } as unknown as D1Database;
  const response = await handleStripeWebhook(new Request('https://control.agentsight.us/v1/billing/webhook', {
    method: 'POST', body: event, headers: { 'Stripe-Signature': `t=${timestamp},v1=${signature}` },
  }), { ...stripeEnv, DB: db }, async () => Response.json({
    id: 'sub_test', customer: 'cus_test', status: 'trialing', current_period_end: 1_900_000_000,
    metadata: { organization_id: 'org_personal_user1' },
    items: { data: [{ price: { id: 'price_pro_annual' } }] },
  }));
  assert.equal(response.status, 200);
  assert.deepEqual(bound.slice(0, 6), [
    'pro', 'annual', 'trialing', 'cus_test', 'sub_test', 1_900_000_000,
  ]);
  assert.equal(bound.at(-1), 'org_personal_user1');
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
  ), { ...stripeEnv, DB: db }), (error: unknown) => error instanceof AccessError
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
