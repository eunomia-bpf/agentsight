// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { controllerUrl, type CloudNode } from '@/lib/controllerClient';
export { registerControllerNode, relayOnline } from '@/lib/controllerClient';
import type { AgentSightSnapshot, CodingPlanStep, LiveOverview, TokenUsage } from '@/types/event';

const DIRECT_CONNECTIONS_KEY = 'agentsight.direct-connections.v1';
const DIRECT_SYNC_ENABLED_KEY = 'agentsight.direct-sync-enabled.v1';
const LEGACY_CONNECTION_KEY = 'agentsight.local-connection.v1';
const REQUEST_TIMEOUT_MS = 12_000;
const SESSION_REQUEST_TIMEOUT_MS = 30_000;
const DIRECT_CAPABILITY_TTL_SECONDS = 12 * 60 * 60;
const DIRECT_ACTIONS = ['node.info', 'evidence.read', 'session.read', 'session.message'];
let launchPairing: Promise<DirectProbeResult> | null = null;

type NodeAddressSpace = 'local' | 'loopback';
type LocalFetchInit = RequestInit & { targetAddressSpace?: NodeAddressSpace };
type NodeRequest = (path: string, init?: RequestInit) => Promise<Response>;

const snapshotPath = (limit: number) => `/api/v1/snapshot?audit_limit=${limit}`;
const overviewPath = () => '/api/v1/overview';
const sessionPath = (id: string) => `/api/v1/sessions/${id}`;
const sessionMessagesPath = (id: string) => `${sessionPath(id)}/messages`;

export interface LocalConnection {
  endpoint: string;
  accessToken: string;
  nodeId: string;
  nodeName: string;
  version: string;
}

export type NodeTransport = 'direct' | 'relay' | 'embedded';

export interface SessionDetail {
  session_id: string;
  agent_type: string;
  model?: string | null;
  cwd?: string | null;
  duration_ms?: number;
  usage?: TokenUsage;
  model_usage?: Record<string, TokenUsage>;
  tools?: Record<string, number>;
  files?: Record<string, number>;
  events?: {
    prompts?: Array<{ ts_ms?: number | null; text?: string; preview?: string; task_path?: string[] }>;
    llm_responses?: Array<{
      ts_ms?: number | null; text?: string; preview?: string; response_phase?: string;
      model?: string; input_tokens?: number; output_tokens?: number; cache_tokens?: number;
      total_tokens?: number; task_path?: string[];
    }>;
    tools?: Array<{
      ts_ms?: number | null; tool_name?: string; category?: string; command?: string;
      effect?: string; status?: string; task_path?: string[];
    }>;
    plan?: CodingPlanStep[];
  };
}

export interface NodeClient {
  nodeId: string;
  nodeName: string;
  transport: NodeTransport;
  snapshot(): Promise<AgentSightSnapshot>;
  overview(): Promise<LiveOverview | null>;
  session(sessionId: string): Promise<SessionDetail>;
  submitMessage(sessionId: string, message: string): Promise<void>;
}

export interface DirectProbeResult {
  connection: LocalConnection;
  bootstrapToken: string;
}

export interface EmbeddedServer {
  authorizationRequired: boolean;
  connection: LocalConnection;
}

export class NodeRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'NodeRequestError';
    this.status = status;
  }
}

function expectedNodeAddressSpace(endpoint: URL): NodeAddressSpace {
  const hostname = endpoint.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  return hostname === 'localhost' || hostname.endsWith('.localhost')
      || hostname === '::1' || /^127(?:\.|$)/.test(hostname) ? 'loopback' : 'local';
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

function validCredential(value: string): boolean {
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
  const localOptions: LocalFetchInit = { ...options, targetAddressSpace: expectedNodeAddressSpace(endpoint) };
  return fetch(input, localOptions);
}

async function jsonResponse<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { error?: string; detail?: string };
    throw new NodeRequestError(response.status, body.detail || body.error || `${fallback} (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

async function mintNodeCapability(endpoint: string, bootstrapToken: string): Promise<string> {
  const body = await jsonResponse<{ access_token?: unknown }>(
    await directFetch(`${endpoint}/api/v1/capabilities`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${bootstrapToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ actions: DIRECT_ACTIONS, session_id: null, ttl_seconds: DIRECT_CAPABILITY_TTL_SECONDS }),
    }),
    'AgentSight capability exchange failed',
  );
  if (typeof body.access_token !== 'string' || !validCredential(body.access_token)) {
    throw new NodeRequestError(502, 'AgentSight returned an invalid capability.');
  }
  return body.access_token;
}

export async function pairDirectNode(rawEndpoint: string, bootstrapToken: string): Promise<DirectProbeResult> {
  const endpoint = normalizeDirectEndpoint(rawEndpoint);
  const token = bootstrapToken.trim();
  if (!validCredential(token)) {
    throw new NodeRequestError(400, 'Bootstrap key must be a valid AgentSight Node credential.');
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
  const body = await jsonResponse<{ node?: { id?: string; name?: string; version?: string } }>(
    response,
    'Direct Node probe failed',
  );
  if (!body.node?.id || !body.node.name) {
    throw new NodeRequestError(502, 'The Direct URL did not return valid AgentSight Node metadata.');
  }

  let accessToken: string;
  try {
    accessToken = await mintNodeCapability(endpoint, token);
  } catch (cause) {
    throw new NodeRequestError(
      cause instanceof NodeRequestError ? cause.status : 401,
      'That credential cannot mint Direct capabilities. Use the Node bootstrap key from agentsight bind.',
    );
  }
  return {
    bootstrapToken: token,
    connection: {
      endpoint,
      accessToken,
      nodeId: body.node.id,
      nodeName: body.node.name,
      version: body.node.version || 'unknown',
    },
  };
}

export function pairDirectNodeFromFragment(params: URLSearchParams): Promise<DirectProbeResult> {
  if (params.get('action') !== 'bind' || params.get('v') !== '1') {
    return Promise.reject(new NodeRequestError(400, 'Unsupported AgentSight binding link.'));
  }
  if (!launchPairing) {
    launchPairing = pairDirectNode(params.get('endpoint') || '', params.get('token') || '');
  }
  return launchPairing;
}

export async function detectEmbeddedServer(): Promise<EmbeddedServer | null> {
  try {
    const endpoint = window.location.origin;
    const response = await fetch(`${endpoint}/api/v1/info`, {
      cache: 'no-store', signal: AbortSignal.timeout(2_000),
    });
    if (!response.ok) return null;
    const body = await response.json() as {
      protocol_version?: number; product?: string; authorization_required?: boolean; pairing_required?: boolean;
    };
    if (body.product !== 'agentsight' || body.protocol_version !== 1) return null;
    return {
      authorizationRequired: body.authorization_required === true || body.pairing_required === true,
      connection: {
        endpoint,
        accessToken: '',
        nodeId: 'local-embedded',
        nodeName: 'Local AgentSight',
        version: 'embedded',
      },
    };
  } catch {
    return null;
  }
}

function nodeClient(nodeId: string, nodeName: string, transport: NodeTransport, request: NodeRequest): NodeClient {
  return {
    nodeId,
    nodeName,
    transport,
    async snapshot() {
      return jsonResponse<AgentSightSnapshot>(
        await request(snapshotPath(50_000)), 'AgentSight Node snapshot failed',
      );
    },
    async overview() {
      const response = await request(overviewPath());
      if (response.status === 404 || response.status === 409) return null;
      return jsonResponse<LiveOverview>(response, 'AgentSight Node overview failed');
    },
    async session(sessionId) {
      return jsonResponse<SessionDetail>(
        await request(sessionPath(encodeURIComponent(sessionId)), {
          signal: AbortSignal.timeout(SESSION_REQUEST_TIMEOUT_MS),
        }), 'Session request failed',
      );
    },
    async submitMessage(sessionId, message) {
      await jsonResponse<unknown>(await request(
        sessionMessagesPath(encodeURIComponent(sessionId)),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
          signal: AbortSignal.timeout(SESSION_REQUEST_TIMEOUT_MS),
        },
      ), 'Message submit failed');
    },
  };
}

export function directNodeClient(connection: LocalConnection): NodeClient {
  const authorization = connection.accessToken ? { Authorization: `Bearer ${connection.accessToken}` } : undefined;
  return nodeClient(
    connection.nodeId,
    connection.nodeName,
    connection.accessToken ? 'direct' : 'embedded',
    (path, init = {}) => directFetch(`${connection.endpoint}${path}`, {
      ...init, headers: mergedHeaders(authorization, init.headers),
    }),
  );
}

function relayFetch(token: string, nodeId: string, suffix: string, init: RequestInit = {}) {
  const headers = mergedHeaders(init.headers, { Authorization: `Bearer ${token}` });
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

export function directCloudSyncEnabled(nodeId: string): boolean {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DIRECT_SYNC_ENABLED_KEY) || '[]') as unknown;
    return Array.isArray(parsed) && parsed.includes(nodeId);
  } catch {
    return false;
  }
}

export function setDirectCloudSync(nodeId: string, enabled: boolean): void {
  let enabledNodeIds: string[] = [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DIRECT_SYNC_ENABLED_KEY) || '[]') as unknown;
    if (Array.isArray(parsed)) enabledNodeIds = parsed.filter((value): value is string => typeof value === 'string');
  } catch { /* replace invalid preference state */ }
  const next = enabled
    ? Array.from(new Set([...enabledNodeIds, nodeId]))
    : enabledNodeIds.filter((value) => value !== nodeId);
  window.localStorage.setItem(DIRECT_SYNC_ENABLED_KEY, JSON.stringify(next));
}

function parseConnection(value: unknown): LocalConnection | null {
  if (!value || typeof value !== 'object') return null;
  const connection = value as Partial<LocalConnection>;
  if (typeof connection.endpoint !== 'string'
      || typeof connection.accessToken !== 'string' || !validCredential(connection.accessToken)
      || typeof connection.nodeId !== 'string' || typeof connection.nodeName !== 'string'
      || typeof connection.version !== 'string') return null;
  try {
    return { ...connection, endpoint: normalizeDirectEndpoint(connection.endpoint) } as LocalConnection;
  } catch {
    return null;
  }
}

function persistDirectConnections(connections: Record<string, LocalConnection>): void {
  window.localStorage.setItem(DIRECT_CONNECTIONS_KEY, JSON.stringify(connections));
}

export function loadDirectConnections(): Record<string, LocalConnection> {
  const result: Record<string, LocalConnection> = {};
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DIRECT_CONNECTIONS_KEY) || '{}') as Record<string, unknown>;
    for (const [nodeId, value] of Object.entries(parsed)) {
      const connection = parseConnection(value);
      if (connection?.nodeId === nodeId) result[nodeId] = connection;
    }
  } catch {
    // Ignore malformed browser state and rebuild it from valid entries.
  }

  // One-way compatibility migration from the pre-fleet single-Node key.
  try {
    const legacyRaw = window.localStorage.getItem(LEGACY_CONNECTION_KEY);
    const legacy = legacyRaw ? parseConnection(JSON.parse(legacyRaw)) : null;
    if (legacy && !result[legacy.nodeId]) result[legacy.nodeId] = legacy;
  } catch {
    // Invalid legacy state is simply discarded.
  }
  if (window.localStorage.getItem(LEGACY_CONNECTION_KEY) !== null) {
    window.localStorage.removeItem(LEGACY_CONNECTION_KEY);
    persistDirectConnections(result);
  }
  return result;
}

export function saveDirectConnection(connection: LocalConnection): void {
  persistDirectConnections({ ...loadDirectConnections(), [connection.nodeId]: connection });
}

export function forgetDirectConnection(nodeId: string): void {
  const connections = loadDirectConnections();
  delete connections[nodeId];
  persistDirectConnections(connections);
}
