// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { controllerUrl, type CloudNode, type LocalConnection } from '@/lib/connection';
import initProtocol, {
  session_message_body as sessionMessageBody,
  session_messages_path as sessionMessagesPath,
  session_path as sessionPath,
  snapshot_path as snapshotPath,
} from '@/generated/agentsight-protocol/agentsight_protocol';
import type { AgentSightSnapshot } from '@/types/event';

const DIRECT_CONNECTIONS_KEY = 'agentsight.direct-connections.v1';
const REQUEST_TIMEOUT_MS = 12_000;
let protocolReady: Promise<unknown> | null = null;

type NodeAddressSpace = 'local' | 'loopback';
type LocalFetchInit = RequestInit & { targetAddressSpace?: NodeAddressSpace };
type NodeRequest = (path: string, init?: RequestInit) => Promise<Response>;

export type NodeTransport = 'direct' | 'relay' | 'embedded';

export interface SessionDetail {
  session_id: string;
  agent_type: string;
  model?: string | null;
  cwd?: string | null;
  events?: {
    prompts?: Array<{ ts_ms?: number | null; preview?: string }>;
    llm_responses?: Array<{ ts_ms?: number | null; preview?: string; response_phase?: string }>;
    tools?: Array<{ ts_ms?: number | null; tool_name?: string; effect?: string; status?: string }>;
  };
}

export interface NodeClient {
  nodeId: string;
  nodeName: string;
  transport: NodeTransport;
  snapshot(): Promise<AgentSightSnapshot>;
  session(sessionId: string): Promise<SessionDetail>;
  submitMessage(sessionId: string, message: string): Promise<void>;
}

export class NodeRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'NodeRequestError';
    this.status = status;
  }
}

async function protocol<T>(read: () => T): Promise<T> {
  if (!protocolReady) protocolReady = initProtocol();
  await protocolReady;
  return read();
}

function expectedNodeAddressSpace(endpoint: URL): NodeAddressSpace {
  const hostname = endpoint.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (hostname === 'localhost' || hostname.endsWith('.localhost')
      || hostname === '::1' || /^127(?:\.|$)/.test(hostname)) {
    return 'loopback';
  }
  return 'local';
}

function mergedHeaders(base?: HeadersInit, extra?: HeadersInit): Headers {
  const headers = new Headers(base);
  new Headers(extra).forEach((value, key) => headers.set(key, value));
  return headers;
}

function normalizeDirectEndpoint(raw: string): string {
  let endpoint: URL;
  try {
    endpoint = new URL(raw.trim());
  } catch {
    throw new NodeRequestError(400, 'Direct URL must be a valid http(s) URL.');
  }
  if (!['http:', 'https:'].includes(endpoint.protocol)
      || !endpoint.hostname || endpoint.username || endpoint.password) {
    throw new NodeRequestError(400, 'Direct URL must be a valid http(s) URL without credentials.');
  }
  endpoint.pathname = '';
  endpoint.search = '';
  endpoint.hash = '';
  return endpoint.toString().replace(/\/$/, '');
}

function validAccessToken(value: string): boolean {
  return /^[A-Za-z0-9_-]{32,256}$/.test(value);
}

async function directFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const endpoint = new URL(input);
  const options: RequestInit = {
    ...init,
    mode: 'cors',
    cache: 'no-store',
    signal: init.signal || AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  };
  if (endpoint.protocol !== 'http:') {
    try {
      return await fetch(input, options);
    } catch (error) {
      if (init.signal?.aborted) throw error;
    }
  }
  const localOptions: LocalFetchInit = { ...options };
  localOptions.targetAddressSpace = expectedNodeAddressSpace(endpoint);
  return fetch(input, localOptions);
}

async function jsonResponse<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: string; detail?: string };
    throw new NodeRequestError(
      response.status,
      body.detail || body.error || `${fallback} (${response.status}).`,
    );
  }
  return response.json() as Promise<T>;
}

export async function probeDirectConnection(
  rawEndpoint: string,
  accessToken: string,
): Promise<LocalConnection> {
  const endpoint = normalizeDirectEndpoint(rawEndpoint);
  const token = accessToken.trim();
  if (!validAccessToken(token)) {
    throw new NodeRequestError(400, 'Access key must be the persistent AgentSight Node access key.');
  }

  let response: Response;
  try {
    response = await directFetch(`${endpoint}/api/v1/info`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new NodeRequestError(
      0,
      'Could not reach that Direct URL. Check the IP/hostname, Node listen address, and browser local-network permission.',
    );
  }
  const body = await jsonResponse<{
    node?: { id?: string; name?: string; version?: string };
  }>(response, 'Direct Node probe failed');
  if (!body.node?.id || !body.node.name) {
    throw new NodeRequestError(502, 'The Direct URL did not return valid AgentSight Node metadata.');
  }
  return {
    endpoint,
    accessToken: token,
    nodeId: body.node.id,
    nodeName: body.node.name,
    version: body.node.version || 'unknown',
  };
}

function nodeClient(
  nodeId: string,
  nodeName: string,
  transport: NodeTransport,
  request: NodeRequest,
): NodeClient {
  return {
    nodeId,
    nodeName,
    transport,
    async snapshot() {
      return jsonResponse<AgentSightSnapshot>(
        await request(await protocol(() => snapshotPath(50_000))),
        'AgentSight Node snapshot failed',
      );
    },
    async session(sessionId) {
      return jsonResponse<SessionDetail>(
        await request(await protocol(() => sessionPath(encodeURIComponent(sessionId)))),
        'Session request failed',
      );
    },
    async submitMessage(sessionId, message) {
      await jsonResponse<unknown>(await request(
        await protocol(() => sessionMessagesPath(encodeURIComponent(sessionId))),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: await protocol(() => sessionMessageBody(message)),
        },
      ), 'Message submit failed');
    },
  };
}

export function directNodeClient(connection: LocalConnection): NodeClient {
  const authorization = connection.accessToken
    ? { Authorization: `Bearer ${connection.accessToken}` }
    : undefined;
  return nodeClient(
    connection.nodeId,
    connection.nodeName,
    connection.accessToken ? 'direct' : 'embedded',
    (path, init = {}) => directFetch(`${connection.endpoint}${path}`, {
      ...init,
      headers: mergedHeaders(authorization, init.headers),
    }),
  );
}

function relayFetch(token: string, nodeId: string, suffix: string, init: RequestInit = {}) {
  const headers = mergedHeaders(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  return fetch(`${controllerUrl}/v1/nodes/${encodeURIComponent(nodeId)}/relay${suffix}`, {
    ...init,
    cache: 'no-store',
    signal: init.signal || AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    headers,
  });
}

export function relayNodeClient(node: CloudNode, token: string): NodeClient {
  return nodeClient(
    node.id,
    node.name,
    'relay',
    (path, init = {}) => relayFetch(token, node.id, path.replace(/^\/api\/v1/, ''), init),
  );
}

export async function relayOnline(token: string, nodeId: string): Promise<boolean> {
  const response = await relayFetch(token, nodeId, '/status');
  if (!response.ok) return false;
  const body = await response.json().catch(() => ({})) as { online?: unknown };
  return body.online === true;
}

export async function registerControllerNode(
  token: string,
  connection: LocalConnection,
): Promise<void> {
  const response = await fetch(`${controllerUrl}/v1/nodes`, {
    method: 'POST',
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id: connection.nodeId,
      name: connection.nodeName,
      version: connection.version,
      ...(connection.accessToken ? { relay_token: connection.accessToken } : {}),
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: string };
    throw new NodeRequestError(
      response.status,
      body.error || `Could not register this Node (${response.status}).`,
    );
  }
}

export function loadDirectConnections(): Record<string, LocalConnection> {
  try {
    const raw = window.localStorage.getItem(DIRECT_CONNECTIONS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, LocalConnection>;
    const result: Record<string, LocalConnection> = {};
    for (const [nodeId, connection] of Object.entries(parsed)) {
      if (connection && connection.nodeId === nodeId
          && typeof connection.endpoint === 'string'
          && typeof connection.accessToken === 'string'
          && typeof connection.nodeName === 'string'
          && typeof connection.version === 'string') {
        result[nodeId] = connection;
      }
    }
    return result;
  } catch {
    return {};
  }
}

export function saveDirectConnection(connection: LocalConnection): void {
  const connections = loadDirectConnections();
  connections[connection.nodeId] = connection;
  window.localStorage.setItem(DIRECT_CONNECTIONS_KEY, JSON.stringify(connections));
}

export function forgetDirectConnection(nodeId: string): void {
  const connections = loadDirectConnections();
  delete connections[nodeId];
  window.localStorage.setItem(DIRECT_CONNECTIONS_KEY, JSON.stringify(connections));
}
