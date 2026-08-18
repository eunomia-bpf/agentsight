// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  MAX_PENDING_RELAY_REQUESTS,
  MAX_PENDING_BILLING_RECONCILIATIONS,
  NodeRelay,
  RELAY_TIMEOUT_MS,
  browserRelayRoute,
  connectNodeRelay,
  proxyBrowserRelay,
  relayTokenHash,
  relayNodeSocketId,
  validRelayNodeVersion,
  validRelayToken,
} from './relay.ts';
import type { RelayEnv } from './relay.ts';

test('relay waits longer than the Node provider acknowledgement window', () => {
  assert.ok(RELAY_TIMEOUT_MS > 20_000);
  assert.ok(RELAY_TIMEOUT_MS < 30_000);
});

test('relay pending work is capped per Node', () => {
  assert.equal(MAX_PENDING_RELAY_REQUESTS, 64);
});

test('relay pending cap holds across concurrently parsed request bodies', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  const envelopes: Array<{ id: string }> = [];
  const socket = {
    readyState: WebSocket.OPEN,
    send(message: string) {
      envelopes.push(JSON.parse(message) as { id: string });
    },
  } as unknown as WebSocket;
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [socket],
  } as unknown as DurableObjectState;
  const relay = new NodeRelay(ctx, {} as RelayEnv);

  try {
    const requests = Array.from({ length: MAX_PENDING_RELAY_REQUESTS + 1 }, () => relay.fetch(
      new Request('https://relay.internal/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: 'GET', path: '/api/v1/overview' }),
      }),
    ));
    for (let attempt = 0; attempt < 20 && envelopes.length < MAX_PENDING_RELAY_REQUESTS; attempt += 1) {
      await new Promise((resolve) => setImmediate(resolve));
    }
    await new Promise((resolve) => setImmediate(resolve));

    for (const envelope of envelopes) {
      await relay.webSocketMessage(socket, JSON.stringify({
        type: 'response', id: envelope.id, status: 200, body: '{}',
      }));
    }
    const responses = await Promise.all(requests);
    assert.equal(envelopes.length, MAX_PENDING_RELAY_REQUESTS);
    assert.equal(responses.filter((response) => response.status === 200).length, MAX_PENDING_RELAY_REQUESTS);
    assert.equal(responses.filter((response) => response.status === 429).length, 1);
    assert.deepEqual(await responses.find((response) => response.status === 429)?.json(), {
      error: 'relay_busy',
    });
  } finally {
    if (originalPair) {
      Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    } else {
      Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
    }
  }
});

test('billing webhook is durably queued before acknowledgement and reconciled by alarm', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  const originalFetch = globalThis.fetch;
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  let fetchCalls = 0;
  let fenceChecks = 0;
  let webhookGeneration = 'checkout_generation_old';
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return Response.json({
      id: 'sub_test', customer: 'cus_test', status: 'canceled',
      metadata: {
        organization_id: 'org_personal_user1', checkout_generation: webhookGeneration,
      },
      items: { data: [{ price: { id: 'price_retired' } }] },
    });
  };
  const db = {
    prepare: () => ({
      bind: () => ({
        first: async () => ({
          kind: 'personal', billing_status: 'active', billing_interval: 'monthly',
          external_subscription_id: 'sub_test',
        }),
        run: async () => ({ success: true, meta: { changes: 1 } }),
      }),
    }),
  } as unknown as D1Database;
  const stored = new Map<string, unknown>();
  let alarm: number | null = null;
  const transaction = {
    get: async (key: string) => stored.get(key),
    put: async (key: string, value: unknown) => { stored.set(key, value); },
    delete: async (key: string) => stored.delete(key),
    list: async ({ prefix, limit }: { prefix: string; limit: number }) => new Map(
      Array.from(stored.entries()).filter(([key]) => key.startsWith(prefix)).slice(0, limit),
    ),
    getAlarm: async () => alarm,
    setAlarm: async (value: number) => { alarm = value; },
  };
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [],
    storage: {
      transaction: async (callback: (value: typeof transaction) => Promise<void>) => callback(transaction),
      get: async () => {
        fenceChecks += 1;
        return undefined;
      },
      put: async (key: string, value: unknown) => { stored.set(key, value); },
      delete: async (key: string) => stored.delete(key),
      list: async ({ prefix, limit }: { prefix: string; limit: number }) => new Map(
        Array.from(stored.entries()).filter(([key]) => key.startsWith(prefix)).slice(0, limit),
      ),
      setAlarm: async (value: number) => { alarm = value; },
    },
  } as unknown as DurableObjectState;
  const relay = new NodeRelay(ctx, {
    DB: db,
    NODE_RELAY: {} as DurableObjectNamespace,
    APP_ORIGIN: 'https://app.agentsight.us',
    STRIPE_SECRET_KEY: 'sk_test_example',
    STRIPE_WEBHOOK_SECRET: 'whsec_example',
    STRIPE_PRO_MONTHLY_PRICE_ID: 'price_pro_monthly',
  });
  const enqueue = () => relay.fetch(new Request('https://relay.internal/billing/enqueue', {
    method: 'POST',
    body: JSON.stringify({
      eventId: 'evt_test', organizationId: 'org_personal_user1', subscriptionId: 'sub_test',
    }),
  }));

  try {
    const responses = await Promise.all([enqueue(), enqueue()]);
    assert.deepEqual(responses.map((response) => response.status), [202, 202]);
    assert.equal(fetchCalls, 0);
    assert.equal(stored.size, 1);
    assert.ok(alarm !== null);
    stored.set('billing:checkout:v2', {
      version: 2,
      generation: 'checkout_generation_new',
      input: {
        organizationId: 'org_personal_user1', organizationKind: 'personal',
        email: 'owner@example.com', plan: 'pro', interval: 'monthly',
        externalCustomerId: null, externalSubscriptionId: null,
      },
      expiresAt: Date.now() + 60_000,
      priceId: 'price_pro_monthly',
      appOrigin: 'https://app.agentsight.us',
    });
    await relay.alarm();
    assert.equal(fetchCalls, 1);
    assert.equal(fenceChecks, 1);
    assert.equal(stored.size, 1);
    assert.ok(stored.has('billing:checkout:v2'));

    webhookGeneration = 'checkout_generation_new';
    const matching = await relay.fetch(new Request('https://relay.internal/billing/enqueue', {
      method: 'POST',
      body: JSON.stringify({
        eventId: 'evt_matching', organizationId: 'org_personal_user1', subscriptionId: 'sub_test',
      }),
    }));
    assert.equal(matching.status, 202);
    await relay.alarm();
    assert.equal(fetchCalls, 2);
    assert.equal(fenceChecks, 2);
    assert.equal(stored.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalPair) Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    else Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
  }
});

test('billing webhook queue coalesces subscriptions and fails closed at its hard cap', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  const stored = new Map<string, unknown>();
  let alarm: number | null = null;
  const transaction = {
    get: async (key: string) => stored.get(key),
    put: async (key: string, value: unknown) => { stored.set(key, value); },
    delete: async (key: string) => stored.delete(key),
    list: async ({ prefix, limit }: { prefix: string; limit: number }) => new Map(
      Array.from(stored.entries()).filter(([key]) => key.startsWith(prefix)).slice(0, limit),
    ),
    getAlarm: async () => alarm,
    setAlarm: async (value: number) => { alarm = value; },
  };
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [],
    storage: {
      transaction: async (callback: (value: typeof transaction) => Promise<unknown>) => callback(transaction),
    },
  } as unknown as DurableObjectState;
  const relay = new NodeRelay(ctx, {} as RelayEnv);
  const enqueue = (index: number, event = index) => relay.fetch(new Request(
    'https://relay.internal/billing/enqueue', {
      method: 'POST', body: JSON.stringify({
        eventId: `evt_${event}`, organizationId: 'org_personal_user1',
        subscriptionId: `sub_${index}`,
      }),
    },
  ));

  try {
    for (let index = 0; index < MAX_PENDING_BILLING_RECONCILIATIONS; index += 1) {
      assert.equal((await enqueue(index)).status, 202);
    }
    assert.equal(stored.size, MAX_PENDING_BILLING_RECONCILIATIONS);
    assert.equal((await enqueue(MAX_PENDING_BILLING_RECONCILIATIONS)).status, 503);
    assert.equal((await enqueue(0, 999)).status, 202);
    assert.equal(stored.size, MAX_PENDING_BILLING_RECONCILIATIONS);
    assert.ok(alarm !== null);
  } finally {
    if (originalPair) Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    else Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
  }
});

test('billing alarm bounds each run and schedules the remaining due work', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  const originalFetch = globalThis.fetch;
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  let fetchCalls = 0;
  globalThis.fetch = async (input) => {
    fetchCalls += 1;
    const subscriptionId = new URL(String(input)).pathname.split('/').at(-1);
    return Response.json({
      id: subscriptionId, customer: 'cus_test', status: 'active',
      metadata: { organization_id: 'org_personal_user1' },
      items: { data: [{ price: { id: 'price_pro_monthly' } }] },
    });
  };
  const stored = new Map<string, unknown>();
  const due = Date.now() - 1_000;
  for (let index = 0; index < 21; index += 1) {
    stored.set(`billing:subscription:sub_${index}`, {
      eventId: `evt_${index}`,
      organizationId: 'org_personal_user1',
      subscriptionId: `sub_${index}`,
      attempts: 0,
      nextAttemptAt: due,
    });
  }
  let alarm: number | null = null;
  const transaction = {
    get: async (key: string) => stored.get(key),
    put: async (key: string, value: unknown) => { stored.set(key, value); },
    delete: async (key: string) => stored.delete(key),
  };
  const list = async ({ prefix, limit }: { prefix: string; limit: number }) => new Map(
    Array.from(stored.entries()).filter(([key]) => key.startsWith(prefix)).slice(0, limit),
  );
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [],
    storage: {
      transaction: async (callback: (value: typeof transaction) => Promise<unknown>) => callback(transaction),
      get: async () => undefined,
      list,
      setAlarm: async (value: number) => { alarm = value; },
    },
  } as unknown as DurableObjectState;
  const db = {
    prepare: () => ({
      bind: () => ({
        first: async () => ({
          kind: 'personal', billing_status: 'inactive', billing_interval: null,
          external_subscription_id: null,
        }),
        run: async () => ({ success: true, meta: { changes: 1 } }),
      }),
    }),
  } as unknown as D1Database;
  const relay = new NodeRelay(ctx, {
    DB: db,
    NODE_RELAY: {} as DurableObjectNamespace,
    APP_ORIGIN: 'https://app.agentsight.us',
    STRIPE_SECRET_KEY: 'sk_test_example',
    STRIPE_WEBHOOK_SECRET: 'whsec_example',
    STRIPE_PRO_MONTHLY_PRICE_ID: 'price_pro_monthly',
  });

  try {
    await relay.alarm();
    assert.equal(fetchCalls, 20);
    assert.equal(stored.size, 1);
    assert.ok(alarm !== null && alarm <= Date.now());

    await relay.alarm();
    assert.equal(fetchCalls, 21);
    assert.equal(stored.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalPair) Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    else Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
  }
});

test('billing Checkout reserves one durable generation before calling Stripe', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  const originalFetch = globalThis.fetch;
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  const stored = new Map<string, unknown>();
  const transaction = {
    get: async (key: string) => stored.get(key),
    put: async (key: string, value: unknown) => { stored.set(key, value); },
    delete: async (key: string) => stored.delete(key),
  };
  let transactionQueue: Promise<unknown> = Promise.resolve();
  let checkoutPosts = 0;
  const checkoutPrices: string[] = [];
  globalThis.fetch = async (input, init) => {
    if (String(input).includes('/subscriptions/search?')) {
      return Response.json({ data: [], has_more: false });
    }
    if (String(input).includes('/checkout/sessions/cs_test_durable')) {
      const sessionId = new URL(String(input)).pathname.split('/').at(-1);
      return Response.json({
        id: sessionId,
        client_reference_id: 'org_personal_user1',
        status: 'expired',
      });
    }
    checkoutPosts += 1;
    const body = init?.body as URLSearchParams;
    checkoutPrices.push(body.get('line_items[0][price]') || '');
    return Response.json({
      id: `cs_test_durable${checkoutPosts}`,
      url: `https://checkout.stripe.com/c/pay/durable${checkoutPosts}`,
      expires_at: Math.floor(Date.now() / 1_000) + 24 * 60 * 60,
    });
  };
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [],
    storage: {
      transaction: (callback: (value: typeof transaction) => Promise<unknown>) => {
        const result = transactionQueue.then(() => callback(transaction));
        transactionQueue = result.catch(() => undefined);
        return result;
      },
      get: async (key: string) => stored.get(key),
      put: async (key: string, value: unknown) => { stored.set(key, value); },
      delete: async (key: string) => stored.delete(key),
    },
  } as unknown as DurableObjectState;
  const relayEnv: RelayEnv = {
    DB: {} as D1Database,
    NODE_RELAY: {} as DurableObjectNamespace,
    APP_ORIGIN: 'https://app.agentsight.us',
    STRIPE_SECRET_KEY: 'sk_test_example',
    STRIPE_WEBHOOK_SECRET: 'whsec_example',
    STRIPE_PRO_MONTHLY_PRICE_ID: 'price_pro_monthly',
    STRIPE_PRO_ANNUAL_PRICE_ID: 'price_pro_annual',
  };
  const relay = new NodeRelay(ctx, relayEnv);
  const checkout = (interval: 'monthly' | 'annual') => relay.fetch(new Request(
    'https://relay.internal/billing/checkout',
    {
      method: 'POST',
      body: JSON.stringify({
        organizationId: 'org_personal_user1', organizationKind: 'personal',
        email: 'owner@example.com', plan: 'pro', interval,
        externalCustomerId: null, externalSubscriptionId: null, billingStatus: 'inactive',
      }),
    },
  ));

  try {
    const responses = await Promise.all([checkout('monthly'), checkout('annual')]);
    assert.deepEqual(responses.map((response) => response.status).sort(), [200, 409]);
    assert.equal(checkoutPosts, 1);
    assert.deepEqual(await responses.find((response) => response.status === 409)?.json(), {
      error: 'billing_checkout_in_progress',
    });

    const retry = await checkout('monthly');
    assert.equal(retry.status, 200);
    assert.deepEqual(await retry.json(), {
      url: 'https://checkout.stripe.com/c/pay/durable1',
    });
    assert.equal(checkoutPosts, 1);
    assert.equal(stored.size, 1);
    assert.deepEqual(checkoutPrices, ['price_pro_monthly']);

    const [checkoutKey, checkoutState] = Array.from(stored.entries())[0] as [
      string, { expiresAt: number; session?: unknown; priceId: string },
    ];
    assert.equal(checkoutState.priceId, 'price_pro_monthly');
    assert.ok(checkoutState.expiresAt - Date.now() > 23 * 60 * 60 * 1_000);
    relayEnv.STRIPE_PRO_MONTHLY_PRICE_ID = 'price_pro_monthly_v2';
    stored.set(checkoutKey, {
      ...checkoutState, session: undefined, expiresAt: Date.now() - 120_000,
    });
    const recovered = await checkout('monthly');
    assert.equal(recovered.status, 200);
    assert.equal(checkoutPosts, 2);
    assert.equal(checkoutPrices[1], 'price_pro_monthly_v2');

    const recoveredState = stored.get(checkoutKey) as { expiresAt: number };
    stored.set(checkoutKey, { ...recoveredState, expiresAt: Date.now() - 120_000 });
    const replacement = await checkout('annual');
    assert.equal(replacement.status, 200);
    assert.deepEqual(await replacement.json(), {
      url: 'https://checkout.stripe.com/c/pay/durable3',
    });
    assert.equal(checkoutPosts, 3);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalPair) Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    else Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
  }
});

test('Node relay socket path accepts only stable Node IDs', () => {
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_0123abcdef'), 'node_0123abcdef');
  assert.equal(relayNodeSocketId('/v1/relay/nodes/not-a-node'), null);
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_ok/extra'), null);
});

test('browser relay parses supported Node paths before semantic authorization', () => {
  const snapshot = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/snapshot?audit_limit=5000',
  ));
  assert.deepEqual(snapshot, {
    nodeId: 'node_test',
    method: 'GET',
    nodePath: '/api/v1/snapshot?audit_limit=5000',
    statusOnly: false,
  });

  const message = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST' },
  ));
  assert.deepEqual(message, {
    nodeId: 'node_test',
    method: 'POST',
    nodePath: '/api/v1/sessions/session-1/messages',
    statusOnly: false,
  });

  assert.deepEqual(browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/status',
  )), {
    nodeId: 'node_test', method: 'GET', nodePath: null, statusOnly: true,
  });
  assert.equal(browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/../capabilities',
    { method: 'POST' },
  )), null);
});

test('browser relay preserves a maximally escaped valid session message', async () => {
  const message = '\0'.repeat(65_536);
  const body = JSON.stringify({ message });
  assert.ok(new TextEncoder().encode(body).byteLength > 96 * 1024);
  let relayedBody = '';
  const relay = {
    idFromName: () => ({}) as DurableObjectId,
    get: () => ({
      fetch: async (request: Request) => {
        const input = await request.json() as { body?: string };
        relayedBody = input.body || '';
        return new Response('{}', { status: 200 });
      },
    }) as unknown as DurableObjectStub,
  } as unknown as DurableObjectNamespace;
  const request = new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST', body },
  );
  const route = browserRelayRoute(request);
  assert.ok(route);

  const response = await proxyBrowserRelay(
    request,
    { DB: {} as D1Database, NODE_RELAY: relay },
    route,
  );

  assert.equal(response.status, 200);
  assert.equal(relayedBody, body);
  assert.equal(JSON.parse(relayedBody).message, message);
});

test('browser relay cancels an oversized streaming body without Content-Length', async () => {
  let cancelled = false;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array(300 * 1024));
      controller.enqueue(new Uint8Array(300 * 1024));
    },
    cancel() {
      cancelled = true;
    },
  });
  const request = new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST', body: stream, duplex: 'half' } as RequestInit & { duplex: 'half' },
  );
  const route = browserRelayRoute(request);
  assert.ok(route);

  const response = await proxyBrowserRelay(
    request,
    { DB: {} as D1Database, NODE_RELAY: {} as DurableObjectNamespace },
    route,
  );

  assert.equal(response.status, 413);
  assert.equal(cancelled, true);
});

test('relay tokens use the same Direct bearer shape', () => {
  assert.equal(validRelayToken('a'.repeat(64)), true);
  assert.equal(validRelayToken('short'), false);
  assert.equal(validRelayToken(`${'a'.repeat(63)}!`), false);
});

test('relay node versions accept release metadata and reject unsafe values', () => {
  assert.equal(validRelayNodeVersion('1.0.23'), true);
  assert.equal(validRelayNodeVersion('1.0.24-rc.1+build'), true);
  assert.equal(validRelayNodeVersion(`1.${'0'.repeat(62)}`), true);
  assert.equal(validRelayNodeVersion(''), false);
  assert.equal(validRelayNodeVersion(' 1.0.23'), false);
  assert.equal(validRelayNodeVersion('1.0.23\r\nX-Injected: yes'), false);
  assert.equal(validRelayNodeVersion(`1.${'0'.repeat(63)}`), false);
});

test('authenticated relay reconnect persists reported version without breaking old Nodes', async () => {
  const token = 'a'.repeat(64);
  const expectedHash = await relayTokenHash(token);
  const updates: unknown[][] = [];
  const db = {
    prepare: (query: string) => ({
      bind: (...values: unknown[]) => ({
        first: async () => ({ relay_token_hash: expectedHash }),
        run: async () => {
          assert.match(query, /version = COALESCE\(\?3, version\)/);
          updates.push(values);
          return { success: true };
        },
      }),
    }),
  } as D1Database;
  const relay = {
    idFromName: () => ({}) as DurableObjectId,
    get: () => ({
      fetch: async () => new Response(null, { status: 200 }),
    }) as unknown as DurableObjectStub,
  } as unknown as DurableObjectNamespace;

  const connect = (version?: string) => connectNodeRelay(new Request(
    'https://controller.example/v1/relay/nodes/node_test',
    { headers: {
      Upgrade: 'websocket', Authorization: `Bearer ${token}`,
      ...(version ? { 'X-AgentSight-Node-Version': version } : {}),
    } },
  ), { DB: db, NODE_RELAY: relay }, 'node_test');

  assert.equal((await connect('1.0.23')).status, 200);
  assert.equal(updates[0][1], 'node_test');
  assert.equal(updates[0][2], '1.0.23');
  assert.equal((await connect()).status, 200);
  assert.equal(updates[1][2], null);
  assert.equal((await connect('invalid version')).status, 400);
  assert.equal(updates.length, 2);
});
