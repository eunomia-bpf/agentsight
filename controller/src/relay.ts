// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

const NODE_ID_PATTERN = /^node_[A-Za-z0-9_]{1,123}$/;
const RELAY_TOKEN_PATTERN = /^[A-Za-z0-9_-]{32,256}$/;
const RELAY_TIMEOUT_MS = 12_000;
const MAX_BROWSER_BODY_BYTES = 96 * 1024;

export interface RelayEnv {
  DB: D1Database;
  NODE_RELAY: DurableObjectNamespace;
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
  const status = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay\/status$/);
  if (status && request.method === 'GET') {
    const nodeId = decodeNodeId(status[1]);
    return nodeId ? { nodeId, method: 'GET', nodePath: null, statusOnly: true } : null;
  }

  const snapshot = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay\/snapshot$/);
  if (snapshot && request.method === 'GET') {
    const nodeId = decodeNodeId(snapshot[1]);
    if (!nodeId) return null;
    const auditLimit = url.searchParams.get('audit_limit');
    const query = auditLimit && /^\d{1,6}$/.test(auditLimit)
      ? `?audit_limit=${encodeURIComponent(auditLimit)}`
      : '';
    return {
      nodeId,
      method: 'GET',
      nodePath: `/api/v1/snapshot${query}`,
      statusOnly: false,
    };
  }

  const overview = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay\/overview$/);
  if (overview && request.method === 'GET') {
    const nodeId = decodeNodeId(overview[1]);
    return nodeId ? {
      nodeId,
      method: 'GET',
      nodePath: '/api/v1/overview',
      statusOnly: false,
    } : null;
  }

  const nebula = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay\/nebula$/);
  if (nebula && request.method === 'GET') {
    const nodeId = decodeNodeId(nebula[1]);
    return nodeId ? {
      nodeId,
      method: 'GET',
      nodePath: '/api/v1/nebula',
      statusOnly: false,
    } : null;
  }

  const message = url.pathname.match(
    /^\/v1\/nodes\/([^/]+)\/relay\/sessions\/([^/]+)\/messages$/,
  );
  if (message && request.method === 'POST') {
    const nodeId = decodeNodeId(message[1]);
    const sessionId = decodeSessionId(message[2]);
    if (!nodeId || !sessionId) return null;
    return {
      nodeId,
      method: 'POST',
      nodePath: `/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`,
      statusOnly: false,
    };
  }

  const session = url.pathname.match(/^\/v1\/nodes\/([^/]+)\/relay\/sessions\/([^/]+)$/);
  if (session && request.method === 'GET') {
    const nodeId = decodeNodeId(session[1]);
    const sessionId = decodeSessionId(session[2]);
    if (!nodeId || !sessionId) return null;
    return {
      nodeId,
      method: 'GET',
      nodePath: `/api/v1/sessions/${encodeURIComponent(sessionId)}`,
      statusOnly: false,
    };
  }

  return null;
}

export function validRelayToken(value: string): boolean {
  return RELAY_TOKEN_PATTERN.test(value);
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

  const row = await env.DB.prepare(
    'SELECT relay_token_hash FROM nodes WHERE id = ?1',
  ).bind(nodeId).first<{ relay_token_hash: string | null }>();
  if (!row?.relay_token_hash || row.relay_token_hash !== await relayTokenHash(token)) {
    return json({ error: 'node_auth_invalid' }, 401);
  }

  await env.DB.prepare(
    `UPDATE nodes SET last_seen_at = ?1, connection_mode = 'relay' WHERE id = ?2`,
  ).bind(Math.floor(Date.now() / 1000), nodeId).run();

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
  private pending = new Map<string, PendingRequest>();

  constructor(ctx: DurableObjectState, _env: RelayEnv) {
    this.ctx = ctx;
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
}

function decodeNodeId(value: string): string | null {
  try {
    const decoded = decodeURIComponent(value);
    return NODE_ID_PATTERN.test(decoded) ? decoded : null;
  } catch {
    return null;
  }
}

function decodeSessionId(value: string): string | null {
  try {
    const decoded = decodeURIComponent(value);
    if (!decoded || decoded.length > 256 || decoded.includes('/') || decoded.includes('\\')) return null;
    return decoded;
  } catch {
    return null;
  }
}

function bearerToken(request: Request): string | null {
  return request.headers.get('Authorization')?.match(/^Bearer ([A-Za-z0-9_-]{32,256})$/)?.[1] || null;
}

async function boundedBody(request: Request): Promise<string | Response> {
  const declared = Number(request.headers.get('Content-Length') || '0');
  if (declared > MAX_BROWSER_BODY_BYTES) return json({ error: 'request_too_large' }, 413);
  const body = await request.text();
  if (new TextEncoder().encode(body).byteLength > MAX_BROWSER_BODY_BYTES) {
    return json({ error: 'request_too_large' }, 413);
  }
  return body;
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
