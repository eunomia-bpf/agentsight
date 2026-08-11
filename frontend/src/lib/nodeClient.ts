// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { controlPlaneUrl, type CloudNode, type LocalConnection } from '@/lib/connection';
import type { AgentSightSnapshot } from '@/types/event';

const DIRECT_CONNECTIONS_KEY = 'agentsight.direct-connections.v1';
const REQUEST_TIMEOUT_MS = 12_000;

type NodeAddressSpace = 'local' | 'loopback';
type LocalFetchInit = RequestInit & { targetAddressSpace?: NodeAddressSpace };

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

function expectedNodeAddressSpace(endpoint: URL): NodeAddressSpace {
  const hostname = endpoint.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (hostname === 'localhost' || hostname.endsWith('.localhost')
      || hostname === '::1' || /^127(?:\.|$)/.test(hostname)) {
    return 'loopback';
  }
  return 'local';
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
    throw new Error(body.detail || body.error || `${fallback} (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export function directNodeClient(connection: LocalConnection): NodeClient {
  const headers = connection.accessToken
    ? { Authorization: `Bearer ${connection.accessToken}` }
    : {};
  const request = (path: string, init: RequestInit = {}) => directFetch(
    `${connection.endpoint}${path}`,
    {
      ...init,
      headers: { ...headers, ...(init.headers || {}) },
    },
  );
  return {
    nodeId: connection.nodeId,
    nodeName: connection.nodeName,
    transport: connection.accessToken ? 'direct' : 'embedded',
    async snapshot() {
      return jsonResponse<AgentSightSnapshot>(
        await request('/api/v1/snapshot?audit_limit=50000'),
        'AgentSight Node snapshot failed',
      );
    },
    async session(sessionId) {
      return jsonResponse<SessionDetail>(
        await request(`/api/v1/sessions/${encodeURIComponent(sessionId)}`),
        'Session request failed',
      );
    },
    async submitMessage(sessionId, message) {
      await jsonResponse<unknown>(await request(
        `/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        },
      ), 'Message submit failed');
    },
  };
}

function relayFetch(token: string, nodeId: string, suffix: string, init: RequestInit = {}) {
  return fetch(`${controlPlaneUrl}/v1/nodes/${encodeURIComponent(nodeId)}/relay${suffix}`, {
    ...init,
    cache: 'no-store',
    signal: init.signal || AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.headers || {}),
    },
  });
}

export function relayNodeClient(node: CloudNode, token: string): NodeClient {
  return {
    nodeId: node.id,
    nodeName: node.name,
    transport: 'relay',
    async snapshot() {
      return jsonResponse<AgentSightSnapshot>(
        await relayFetch(token, node.id, '/snapshot?audit_limit=50000'),
        'Controller relay snapshot failed',
      );
    },
    async session(sessionId) {
      return jsonResponse<SessionDetail>(
        await relayFetch(token, node.id, `/sessions/${encodeURIComponent(sessionId)}`),
        'Controller relay session failed',
      );
    },
    async submitMessage(sessionId, message) {
      await jsonResponse<unknown>(await relayFetch(
        token,
        node.id,
        `/sessions/${encodeURIComponent(sessionId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        },
      ), 'Controller relay message submit failed');
    },
  };
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
  const response = await fetch(`${controlPlaneUrl}/v1/nodes`, {
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
    throw new Error(body.error || `Could not register this Node (${response.status}).`);
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
