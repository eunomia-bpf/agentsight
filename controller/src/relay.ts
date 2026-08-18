// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  createStripeCheckout,
  inspectStripeCheckoutSession,
  reconcileStripeSubscription,
  STRIPE_CHECKOUT_LIFETIME_SECONDS,
  validateStripeCheckoutInput,
  type CheckoutInput,
  type StripeCheckoutSession,
  type StripeEnv,
} from './billing.ts';
import { AccessError } from './access.ts';

const NODE_ID_PATTERN = /^node_[A-Za-z0-9_]{1,123}$/;
const RELAY_TOKEN_PATTERN = /^[A-Za-z0-9_-]{32,256}$/;
const NODE_VERSION_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$/;
export const RELAY_TIMEOUT_MS = 25_000;
export const MAX_PENDING_RELAY_REQUESTS = 64;
// SessionMessageRequest permits 65,536 decoded bytes. JSON escaping can expand
// control bytes to six source bytes, so relay the full public Node contract.
const MAX_BROWSER_BODY_BYTES = 512 * 1024;
const MAX_RELAY_SUFFIX_BYTES = 4 * 1024;
const BILLING_EVENT_PREFIX = 'billing:subscription:';
const BILLING_CHECKOUT_KEY = 'billing:checkout:v2';
const BILLING_EVENT_ID_PATTERN = /^evt_[A-Za-z0-9_]{1,250}$/;
const BILLING_ORGANIZATION_ID_PATTERN = /^org_[A-Za-z0-9_]{1,124}$/;
const BILLING_SUBSCRIPTION_ID_PATTERN = /^sub_[A-Za-z0-9_]{1,250}$/;
export const MAX_PENDING_BILLING_RECONCILIATIONS = 128;
const MAX_BILLING_EVENTS_PER_ALARM = 20;
const BILLING_ALARM_TIME_BUDGET_MS = 60_000;
const MAX_BILLING_RECONCILIATION_ATTEMPTS = 48;
const BILLING_CHECKOUT_EXPIRY_GRACE_MS = 60_000;

export interface RelayEnv {
  DB: D1Database;
  NODE_RELAY: DurableObjectNamespace;
  APP_ORIGIN?: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  STRIPE_PRO_MONTHLY_PRICE_ID?: string;
  STRIPE_PRO_ANNUAL_PRICE_ID?: string;
  STRIPE_PRO_MONTHLY_LEGACY_PRICE_IDS?: string;
  STRIPE_PRO_ANNUAL_LEGACY_PRICE_IDS?: string;
  STRIPE_TEAM_MONTHLY_PRICE_ID?: string;
}

export interface BrowserRelayRoute {
  nodeId: string;
  method: 'GET' | 'POST';
  nodePath: string | null;
  statusOnly: boolean;
}

interface RelayRequestEnvelope {
  type: 'request';
  id: string;
  method: 'GET' | 'POST';
  path: string;
  body?: string;
}

interface RelayResponseEnvelope {
  type: 'response';
  id: string;
  status: number;
  body?: string;
}

interface PendingRequest {
  resolve: (response: Response) => void;
  timer: ReturnType<typeof setTimeout>;
}

interface PendingBillingReconciliation {
  eventId: string;
  organizationId: string;
  subscriptionId: string;
  attempts: number;
  nextAttemptAt: number;
}

interface PendingBillingCheckout {
  version: 2;
  generation: string;
  input: CheckoutInput;
  expiresAt: number;
  priceId: string;
  appOrigin: string;
  session?: StripeCheckoutSession;
}

export function relayNodeSocketId(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/relay\/nodes\/([^/]+)$/);
  if (!match) return null;
  try {
    const nodeId = decodeURIComponent(match[1]);
    return NODE_ID_PATTERN.test(nodeId) ? nodeId : null;
  } catch {
    return null;
  }
}

export function browserRelayRoute(request: Request): BrowserRelayRoute | null {
  const url = new URL(request.url);
  const match = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay(?:\/(.*))?$/);
  if (!match) return null;
  const nodeId = decodeNodeId(match[1]);
  if (!nodeId) return null;

  const suffix = match[2] || '';
  if (suffix === 'status' && request.method === 'GET' && !url.search) {
    return { nodeId, method: 'GET', nodePath: null, statusOnly: true };
  }
  if ((request.method !== 'GET' && request.method !== 'POST') || !validRelaySuffix(suffix, url.search)) {
    return null;
  }
  return {
    nodeId,
    method: request.method,
    nodePath: `/api/v1/${suffix}${url.search}`,
    statusOnly: false,
  };
}

export function validRelayToken(value: string): boolean {
  return RELAY_TOKEN_PATTERN.test(value);
}

export function validRelayNodeVersion(value: string): boolean {
  return NODE_VERSION_PATTERN.test(value);
}

function relayStub(env: RelayEnv, nodeId: string): DurableObjectStub {
  return env.NODE_RELAY.get(env.NODE_RELAY.idFromName(nodeId));
}

export async function connectNodeRelay(
  request: Request,
  env: RelayEnv,
  nodeId: string,
): Promise<Response> {
  if (request.headers.get('Upgrade')?.toLowerCase() !== 'websocket') {
    return json({ error: 'websocket_upgrade_required' }, 426);
  }
  const token = bearerToken(request);
  if (!token || !validRelayToken(token)) return json({ error: 'node_auth_required' }, 401);
  const reportedVersion = request.headers.get('X-AgentSight-Node-Version');
  if (reportedVersion !== null && !validRelayNodeVersion(reportedVersion)) {
    return json({ error: 'invalid_node_version' }, 400);
  }

  const row = await env.DB.prepare(
    'SELECT relay_token_hash FROM nodes WHERE id = ?1',
  ).bind(nodeId).first<{ relay_token_hash: string | null }>();
  if (!row?.relay_token_hash || row.relay_token_hash !== await relayTokenHash(token)) {
    return json({ error: 'node_auth_invalid' }, 401);
  }

  await env.DB.prepare(
    `UPDATE nodes SET last_seen_at = ?1, connection_mode = 'relay',
       version = COALESCE(?3, version) WHERE id = ?2`,
  ).bind(Math.floor(Date.now() / 1000), nodeId, reportedVersion).run();

  return relayStub(env, nodeId).fetch(request);
}

export async function proxyBrowserRelay(
  request: Request,
  env: RelayEnv,
  route: BrowserRelayRoute,
): Promise<Response> {
  if (route.statusOnly) return relayStatus(env, route.nodeId);
  const body = route.method === 'POST' ? await boundedBody(request) : undefined;
  if (body instanceof Response) return body;
  return proxyNodeRequest(env, route.nodeId, route.method, route.nodePath || '/', body);
}

export async function relayStatus(env: RelayEnv, nodeId: string): Promise<Response> {
  return relayStub(env, nodeId).fetch(new Request('https://relay.internal/status'));
}

export async function proxyNodeRequest(
  env: RelayEnv,
  nodeId: string,
  method: 'GET' | 'POST',
  path: string,
  body?: string,
): Promise<Response> {
  const relayRequest = new Request('https://relay.internal/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method, path, body }),
  });
  return relayStub(env, nodeId).fetch(relayRequest);
}

export class NodeRelay {
  private readonly ctx: DurableObjectState;
  private readonly env: RelayEnv;
  private pending = new Map<string, PendingRequest>();

  constructor(ctx: DurableObjectState, env: RelayEnv) {
    this.ctx = ctx;
    this.env = env;
    this.ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('ping', 'pong'));
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    if (request.headers.get('Upgrade')?.toLowerCase() === 'websocket') {
      return this.acceptNodeSocket();
    }
    if (url.pathname === '/status') {
      return json({ online: this.nodeSocket() !== null });
    }
    if (url.pathname === '/request' && request.method === 'POST') {
      return this.forwardRequest(request);
    }
    if (url.pathname === '/billing/enqueue' && request.method === 'POST') {
      return this.enqueueBilling(request);
    }
    if (url.pathname === '/billing/checkout' && request.method === 'POST') {
      return this.checkoutBilling(request);
    }
    return json({ error: 'not_found' }, 404);
  }

  async webSocketMessage(_ws: WebSocket, message: ArrayBuffer | string): Promise<void> {
    if (typeof message !== 'string') return;
    let response: RelayResponseEnvelope;
    try {
      response = JSON.parse(message) as RelayResponseEnvelope;
    } catch {
      return;
    }
    if (response.type !== 'response' || typeof response.id !== 'string') return;
    const pending = this.pending.get(response.id);
    if (!pending) return;
    this.pending.delete(response.id);
    clearTimeout(pending.timer);
    const status = Number.isInteger(response.status) && response.status >= 200 && response.status <= 599
      ? response.status
      : 502;
    pending.resolve(new Response(response.body || '', {
      status,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'X-AgentSight-Transport': 'relay',
      },
    }));
  }

  async webSocketClose(_ws: WebSocket, _code: number, _reason: string): Promise<void> {
    // Cloudflare has already closed the socket when this callback runs.
  }

  async webSocketError(_ws: WebSocket, error: unknown): Promise<void> {
    console.error(JSON.stringify({ event: 'node_relay_websocket_error', error: String(error) }));
  }

  async alarm(): Promise<void> {
    const startedAt = Date.now();
    const entries = await this.ctx.storage.list<PendingBillingReconciliation>({
      prefix: BILLING_EVENT_PREFIX,
      limit: MAX_PENDING_BILLING_RECONCILIATIONS,
    });
    let nextAlarm: number | null = null;
    let processed = 0;
    try {
      for (const [key, pending] of entries) {
        const now = Date.now();
        if (pending.nextAttemptAt > now) {
          nextAlarm = nextAlarm === null
            ? pending.nextAttemptAt : Math.min(nextAlarm, pending.nextAttemptAt);
          continue;
        }
        if (processed >= MAX_BILLING_EVENTS_PER_ALARM
            || now - startedAt >= BILLING_ALARM_TIME_BUDGET_MS) {
          nextAlarm = now;
          break;
        }
        processed += 1;
        try {
          const result = await reconcileStripeSubscription(
            this.env as RelayEnv & StripeEnv, pending.organizationId, pending.subscriptionId,
            fetch,
            async () => { await this.ctx.storage.get('__agentsight_billing_fence'); },
          );
          await this.deleteBillingEventIfCurrent(key, pending.eventId);
          if (result.outcome === 'updated' && result.checkoutGeneration) {
            await this.deleteCheckoutGeneration(result.checkoutGeneration);
          }
        } catch (error) {
          const attempts = pending.attempts + 1;
          if (attempts >= MAX_BILLING_RECONCILIATION_ATTEMPTS) {
            await this.deleteBillingEventIfCurrent(key, pending.eventId);
            console.error(JSON.stringify({
              event: 'billing_reconciliation_dead_letter', eventId: pending.eventId, attempts,
              reason: error instanceof AccessError ? error.code : 'internal_error',
            }));
            continue;
          }
          const retryAt = now + Math.min(60 * 60_000, (2 ** Math.min(attempts, 10)) * 5_000);
          let retryStored = false;
          await this.ctx.storage.transaction(async (transaction) => {
            const stored = await transaction.get<PendingBillingReconciliation>(key);
            if (stored?.eventId !== pending.eventId) return;
            retryStored = true;
            await transaction.put(key, { ...pending, attempts, nextAttemptAt: retryAt });
          });
          if (retryStored) {
            nextAlarm = nextAlarm === null ? retryAt : Math.min(nextAlarm, retryAt);
          }
          console.error(JSON.stringify({
            event: 'billing_reconciliation_retry', eventId: pending.eventId, attempts,
            reason: error instanceof AccessError ? error.code : 'internal_error',
          }));
        }
      }
    } finally {
      const remaining = await this.ctx.storage.list<PendingBillingReconciliation>({
        prefix: BILLING_EVENT_PREFIX,
        limit: MAX_PENDING_BILLING_RECONCILIATIONS,
      });
      if (remaining.size) {
        const earliest = Math.min(...Array.from(remaining.values(), (entry) => entry.nextAttemptAt));
        await this.ctx.storage.setAlarm(nextAlarm === null ? earliest : Math.min(nextAlarm, earliest));
      }
    }
  }

  private async deleteBillingEventIfCurrent(key: string, eventId: string): Promise<void> {
    await this.ctx.storage.transaction(async (transaction) => {
      const stored = await transaction.get<PendingBillingReconciliation>(key);
      if (stored?.eventId === eventId) await transaction.delete(key);
    });
  }

  private async deleteCheckoutGeneration(generation: string): Promise<void> {
    await this.ctx.storage.transaction(async (transaction) => {
      const stored = await transaction.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
      if (stored?.generation === generation) await transaction.delete(BILLING_CHECKOUT_KEY);
    });
  }

  private async rotateCheckoutGenerationIfExpired(
    generation: string,
    now: number,
  ): Promise<boolean> {
    let rotated = false;
    await this.ctx.storage.transaction(async (transaction) => {
      const stored = await transaction.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
      if (stored?.generation !== generation
          || stored.expiresAt + BILLING_CHECKOUT_EXPIRY_GRACE_MS > now) return;
      rotated = true;
      await transaction.delete(BILLING_CHECKOUT_KEY);
    });
    return rotated;
  }

  private async beginCheckoutGeneration(
    generation: string,
  ): Promise<PendingBillingCheckout | null> {
    let active: PendingBillingCheckout | null = null;
    await this.ctx.storage.transaction(async (transaction) => {
      const stored = await transaction.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
      if (stored?.generation !== generation) return;
      active = stored;
      if (stored.session) return;
      active = {
        ...stored,
        // A response can be lost after Stripe accepted the request. Keep this
        // generation until every Session that this attempt could have created
        // has reached Stripe's default 24-hour expiry.
        expiresAt: Date.now() + STRIPE_CHECKOUT_LIFETIME_SECONDS * 1_000,
      };
      await transaction.put(BILLING_CHECKOUT_KEY, active);
    });
    return active;
  }

  private acceptNodeSocket(): Response {
    for (const socket of this.ctx.getWebSockets('node')) {
      try { socket.close(1012, 'replaced by a newer Node connection'); } catch { /* best effort */ }
    }
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.serializeAttachment({ kind: 'node' });
    this.ctx.acceptWebSocket(server, ['node']);
    return new Response(null, { status: 101, webSocket: client });
  }

  private nodeSocket(): WebSocket | null {
    return this.ctx.getWebSockets('node').find((socket) => socket.readyState === WebSocket.OPEN) || null;
  }

  private async forwardRequest(request: Request): Promise<Response> {
    const node = this.nodeSocket();
    if (!node) return json({ error: 'node_offline' }, 503);

    const input = await request.json() as {
      method?: unknown;
      path?: unknown;
      body?: unknown;
    };
    if ((input.method !== 'GET' && input.method !== 'POST')
      || typeof input.path !== 'string'
      || (input.body !== undefined && typeof input.body !== 'string')) {
      return json({ error: 'invalid_relay_request' }, 400);
    }
    // Durable Object requests can interleave at await points. Reserve the slot only
    // after parsing, with no await between this check and pending.set below.
    if (this.pending.size >= MAX_PENDING_RELAY_REQUESTS) {
      return json({ error: 'relay_busy' }, 429);
    }

    const id = crypto.randomUUID();
    const envelope: RelayRequestEnvelope = {
      type: 'request',
      id,
      method: input.method,
      path: input.path,
      ...(typeof input.body === 'string' ? { body: input.body } : {}),
    };

    return new Promise<Response>((resolve) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        resolve(json({ error: 'node_timeout' }, 504));
      }, RELAY_TIMEOUT_MS);
      this.pending.set(id, { resolve, timer });
      try {
        node.send(JSON.stringify(envelope));
      } catch {
        clearTimeout(timer);
        this.pending.delete(id);
        resolve(json({ error: 'node_offline' }, 503));
      }
    });
  }

  private async enqueueBilling(request: Request): Promise<Response> {
    let input: { eventId?: unknown; organizationId?: unknown; subscriptionId?: unknown };
    try {
      input = await request.json() as typeof input;
    } catch {
      return json({ error: 'stripe_event_invalid' }, 400);
    }
    if (typeof input.eventId !== 'string' || !BILLING_EVENT_ID_PATTERN.test(input.eventId)
        || typeof input.organizationId !== 'string'
        || !BILLING_ORGANIZATION_ID_PATTERN.test(input.organizationId)
        || typeof input.subscriptionId !== 'string'
        || !BILLING_SUBSCRIPTION_ID_PATTERN.test(input.subscriptionId)) {
      return json({ error: 'stripe_event_invalid' }, 400);
    }
    const pending: PendingBillingReconciliation = {
      eventId: input.eventId,
      organizationId: input.organizationId,
      subscriptionId: input.subscriptionId,
      attempts: 0,
      nextAttemptAt: Date.now(),
    };
    const key = `${BILLING_EVENT_PREFIX}${input.subscriptionId}`;
    let queueFull = false;
    await this.ctx.storage.transaction(async (transaction) => {
      const existing = await transaction.get<PendingBillingReconciliation>(key);
      if (!existing) {
        const queued = await transaction.list({
          prefix: BILLING_EVENT_PREFIX,
          limit: MAX_PENDING_BILLING_RECONCILIATIONS,
        });
        if (queued.size >= MAX_PENDING_BILLING_RECONCILIATIONS) {
          queueFull = true;
          return;
        }
      }
      await transaction.put(key, pending);
      const scheduled = await transaction.getAlarm();
      if (scheduled === null || scheduled > pending.nextAttemptAt) {
        await transaction.setAlarm(pending.nextAttemptAt);
      }
    });
    if (queueFull) return json({ error: 'billing_reconciliation_queue_full' }, 503);
    return json({ queued: true }, 202);
  }

  private async checkoutBilling(request: Request): Promise<Response> {
    let input: CheckoutInput;
    try {
      input = await request.json() as CheckoutInput;
      const persisted = await this.ctx.storage.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
      const persistedAttempt = persisted?.version === 2
          && persisted.input.plan === input.plan && persisted.input.interval === input.interval
        ? {
          generation: persisted.generation,
          expiresAtSeconds: Math.floor(persisted.expiresAt / 1_000),
          priceId: persisted.priceId,
          appOrigin: persisted.appOrigin,
        }
        : undefined;
      validateStripeCheckoutInput(this.env as StripeEnv, input, persistedAttempt);
    } catch (error) {
      if (error instanceof AccessError) return json({ error: error.code }, error.status);
      return json({ error: 'invalid_billing_checkout' }, 400);
    }

    const reserve = () => this.ctx.storage.transaction(async (transaction) => {
      const existing = await transaction.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
      if (existing) return existing;
      const parameters = validateStripeCheckoutInput(this.env as StripeEnv, input);
      const now = Date.now();
      const reserved: PendingBillingCheckout = {
        version: 2,
        generation: crypto.randomUUID(),
        input,
        expiresAt: now + STRIPE_CHECKOUT_LIFETIME_SECONDS * 1_000,
        priceId: parameters.price,
        appOrigin: parameters.origin,
      };
      await transaction.put(BILLING_CHECKOUT_KEY, reserved);
      return reserved;
    });
    let checkout: PendingBillingCheckout;
    try {
      checkout = await reserve();
    } catch (error) {
      if (error instanceof AccessError) return json({ error: error.code }, error.status);
      return json({ error: 'billing_checkout_unavailable' }, 503);
    }
    if (checkout.version !== 2 || !Number.isSafeInteger(checkout.expiresAt)
        || typeof checkout.generation !== 'string'
        || typeof checkout.priceId !== 'string' || typeof checkout.appOrigin !== 'string') {
      return json({ error: 'billing_checkout_unavailable' }, 503);
    }
    if (checkout.expiresAt + BILLING_CHECKOUT_EXPIRY_GRACE_MS <= Date.now()) {
      try {
        if (checkout.session) {
          const status = await inspectStripeCheckoutSession(
            this.env as StripeEnv,
            checkout.input.organizationId,
            checkout.session.id,
            fetch,
          );
          if (status === 'complete') {
            return json({ error: 'billing_subscription_already_exists' }, 409);
          }
          if (status === 'open') return json({ url: checkout.session.url });
        }
        const rotated = await this.rotateCheckoutGenerationIfExpired(
          checkout.generation, Date.now(),
        );
        checkout = rotated
          ? await reserve()
          : await this.ctx.storage.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY)
            || await reserve();
      } catch (error) {
        if (error instanceof AccessError) return json({ error: error.code }, error.status);
        return json({ error: 'billing_provider_failed' }, 502);
      }
    }
    if (checkout.input.plan !== input.plan || checkout.input.interval !== input.interval) {
      return json({ error: 'billing_checkout_in_progress' }, 409);
    }
    if (checkout.session) return json({ url: checkout.session.url });

    const activeCheckout = await this.beginCheckoutGeneration(checkout.generation);
    if (!activeCheckout) return json({ error: 'billing_checkout_in_progress' }, 409);
    checkout = activeCheckout;
    if (checkout.input.plan !== input.plan || checkout.input.interval !== input.interval) {
      return json({ error: 'billing_checkout_in_progress' }, 409);
    }
    if (checkout.session) return json({ url: checkout.session.url });

    try {
      const session = await createStripeCheckout(
        this.env as StripeEnv,
        checkout.input,
        fetch,
        {
          generation: checkout.generation,
          expiresAtSeconds: Math.floor(checkout.expiresAt / 1_000),
          priceId: checkout.priceId,
          appOrigin: checkout.appOrigin,
        },
      );
      let current = true;
      await this.ctx.storage.transaction(async (transaction) => {
        const stored = await transaction.get<PendingBillingCheckout>(BILLING_CHECKOUT_KEY);
        if (!stored || stored.generation !== checkout?.generation) {
          current = false;
          return;
        }
        await transaction.put(BILLING_CHECKOUT_KEY, {
          ...stored, expiresAt: session.expiresAt, session,
        });
      });
      if (!current) return json({ error: 'billing_checkout_in_progress' }, 409);
      return json({ url: session.url });
    } catch (error) {
      if (error instanceof AccessError) return json({ error: error.code }, error.status);
      console.error(JSON.stringify({ event: 'billing_checkout_failed', reason: 'internal_error' }));
      return json({ error: 'billing_provider_failed' }, 502);
    }
  }
}

function decodeNodeId(value: string): string | null {
  try {
    const decoded = decodeURIComponent(value);
    return NODE_ID_PATTERN.test(decoded) ? decoded : null;
  } catch {
    return null;
  }
}

function validRelaySuffix(suffix: string, search: string): boolean {
  if (!suffix || suffix.length + search.length > MAX_RELAY_SUFFIX_BYTES) return false;
  if (suffix.startsWith('/') || suffix.includes('\\')) return false;
  return !suffix.split('/').some((segment) => segment === '' || segment === '.' || segment === '..');
}

function bearerToken(request: Request): string | null {
  return request.headers.get('Authorization')?.match(/^Bearer ([A-Za-z0-9_-]{32,256})$/)?.[1] || null;
}

async function boundedBody(request: Request): Promise<string | Response> {
  const declared = Number(request.headers.get('Content-Length') || '0');
  if (declared > MAX_BROWSER_BODY_BYTES) return json({ error: 'request_too_large' }, 413);
  if (!request.body) return '';
  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  const chunks: string[] = [];
  let received = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      received += value.byteLength;
      if (received > MAX_BROWSER_BODY_BYTES) {
        await reader.cancel('request too large');
        return json({ error: 'request_too_large' }, 413);
      }
      chunks.push(decoder.decode(value, { stream: true }));
    }
    chunks.push(decoder.decode());
    return chunks.join('');
  } catch {
    return json({ error: 'invalid_request_body' }, 400);
  }
}

export async function relayTokenHash(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
