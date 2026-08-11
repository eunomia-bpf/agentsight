// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { AgentSightSnapshot } from '@/types/event';

const LOCAL_CONNECTION_KEY = 'agentsight.local-connection.v1';
const CLOUD_SESSION_KEY = 'agentsight.cloud-session.v1';
const OAUTH_VERIFIER_KEY = 'agentsight.oauth-verifier.v1';
const CLOUD_TIMEOUT_MS = 8_000;
const LOCAL_TIMEOUT_MS = 8_000;
let cachedLaunchFragment: URLSearchParams | null | undefined;
let localPairingExchange: Promise<LocalConnection> | null = null;
let cloudCodeExchange: Promise<string> | null = null;

export const controlPlaneUrl = (
  process.env.NEXT_PUBLIC_CONTROL_PLANE_URL
  || 'https://agentsight-control.yusen356.workers.dev'
).replace(/\/$/, '');

export interface LocalConnection {
  endpoint: string;
  accessToken: string;
  nodeId: string;
  nodeName: string;
  version: string;
}

export interface CloudIdentity {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  provider?: 'github' | 'google';
}

export class CloudSessionExpiredError extends Error {
  constructor() {
    super('Your AgentSight sign-in has expired.');
    this.name = 'CloudSessionExpiredError';
  }
}

export interface CloudNode {
  id: string;
  name: string;
  version: string | null;
  connectionMode: 'direct';
  lastRegisteredAt: number;
  createdAt: number;
}

type NodeAddressSpace = 'local' | 'loopback';
type LocalFetchInit = RequestInit & { targetAddressSpace?: NodeAddressSpace };

function expectedNodeAddressSpace(endpoint: URL): NodeAddressSpace {
  const hostname = endpoint.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (hostname === 'localhost' || hostname.endsWith('.localhost')
    || hostname === '::1' || /^127(?:\.|$)/.test(hostname)) {
    return 'loopback';
  }
  return 'local';
}

function localFetch(input: string, init: RequestInit = {}, targetAddressSpace: NodeAddressSpace = 'local') {
  const options: LocalFetchInit = {
    ...init,
    mode: 'cors',
    cache: 'no-store',
    signal: init.signal || AbortSignal.timeout(LOCAL_TIMEOUT_MS),
  };
  options.targetAddressSpace = targetAddressSpace;
  return fetch(input, options);
}

async function nodeFetch(input: string, init: RequestInit = {}) {
  const endpoint = new URL(input);
  if (endpoint.protocol === 'http:') {
    // A hosted HTTPS app needs Local Network Access permission before it can
    // reach an HTTP Node. Declaring the target up front makes Chromium show
    // the permission prompt instead of leaving the ordinary fetch pending.
    return localFetch(input, init, expectedNodeAddressSpace(endpoint));
  }

  const options: RequestInit = {
    ...init,
    mode: 'cors',
    cache: 'no-store',
    signal: init.signal || AbortSignal.timeout(LOCAL_TIMEOUT_MS),
  };
  try {
    // Public HTTPS Direct Nodes must not be declared as local address-space
    // targets. Modern browsers can perform ordinary CORS fetches to them.
    return await fetch(input, options);
  } catch (error) {
    if (init.signal?.aborted) throw error;
    // Loopback/private targets may require an explicit Local Network Access
    // request and browser permission. Retry only after the ordinary path fails.
    try {
      return await localFetch(input, init, expectedNodeAddressSpace(endpoint));
    } catch {
      throw error;
    }
  }
}

function cloudFetch(input: string, init: RequestInit = {}) {
  return fetch(input, { ...init, signal: init.signal || AbortSignal.timeout(CLOUD_TIMEOUT_MS) });
}

function base64Url(bytes: Uint8Array): string {
  let binary = '';
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function normalizeNodeEndpoint(raw: string): string {
  const endpoint = new URL(raw);
  if (!['http:', 'https:'].includes(endpoint.protocol)
    || !endpoint.hostname || endpoint.username || endpoint.password) {
    throw new Error('The binding URL does not contain a valid AgentSight Node endpoint.');
  }
  endpoint.pathname = '';
  endpoint.search = '';
  endpoint.hash = '';
  return endpoint.toString().replace(/\/$/, '');
}

export interface EmbeddedServer {
  authorizationRequired: boolean;
  connection: LocalConnection;
}

export async function detectEmbeddedServer(): Promise<EmbeddedServer | null> {
  try {
    const endpoint = window.location.origin;
    const response = await fetch(`${endpoint}/api/v1/info`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(2_000),
    });
    if (!response.ok) return null;
    const body = await response.json() as {
      protocol_version?: number;
      product?: string;
      authorization_required?: boolean;
      pairing_required?: boolean;
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

export function consumeLaunchFragment(): URLSearchParams | null {
  if (cachedLaunchFragment !== undefined) return cachedLaunchFragment;
  if (!window.location.hash) return null;
  const params = new URLSearchParams(window.location.hash.slice(1));
  if (!params.get('action')) return null;
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
  cachedLaunchFragment = params;
  return cachedLaunchFragment;
}

export function exchangeLocalPairing(params: URLSearchParams): Promise<LocalConnection> {
  if (!localPairingExchange) localPairingExchange = exchangeLocalPairingOnce(params);
  return localPairingExchange;
}

async function exchangeLocalPairingOnce(params: URLSearchParams): Promise<LocalConnection> {
  if (params.get('action') !== 'bind' || params.get('v') !== '1') {
    throw new Error('Unsupported AgentSight binding link.');
  }
  const accessToken = params.get('token');
  const endpoint = normalizeNodeEndpoint(params.get('endpoint') || '');
  if (!accessToken || !/^[A-Za-z0-9_-]{32,256}$/.test(accessToken)) {
    throw new Error('The binding link is missing a valid access key.');
  }

  let response: Response;
  try {
    response = await nodeFetch(`${endpoint}/api/v1/info`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch {
    throw new Error(
      'Could not reach the AgentSight Node. Check its endpoint and browser network permission, then run agentsight bind again.',
    );
  }
  if (!response.ok) {
    throw new Error(`AgentSight binding failed (${response.status}).`);
  }
  const body = await response.json() as {
    node?: { id?: string; name?: string; version?: string };
  };
  if (!body.node?.id || !body.node.name) {
    throw new Error('AgentSight returned an invalid binding response.');
  }
  return {
    endpoint,
    accessToken,
    nodeId: body.node.id,
    nodeName: body.node.name,
    version: body.node.version || 'unknown',
  };
}

export async function fetchLocalSnapshot(connection: LocalConnection): Promise<AgentSightSnapshot> {
  const headers: HeadersInit = {};
  if (connection.accessToken) headers.Authorization = `Bearer ${connection.accessToken}`;
  const input = `${connection.endpoint}/api/v1/snapshot?audit_limit=50000`;
  const response = connection.accessToken
    ? await nodeFetch(input, { headers })
    : await fetch(input, { headers, cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 401) clearLocalConnection();
    throw new Error(`AgentSight Node returned ${response.status}.`);
  }
  return response.json() as Promise<AgentSightSnapshot>;
}

export function saveLocalConnection(connection: LocalConnection) {
  window.localStorage.setItem(LOCAL_CONNECTION_KEY, JSON.stringify(connection));
}

export function loadLocalConnection(): LocalConnection | null {
  try {
    const value = window.localStorage.getItem(LOCAL_CONNECTION_KEY);
    if (!value) return null;
    const parsed = JSON.parse(value) as Partial<LocalConnection>;
    if (typeof parsed.endpoint !== 'string'
      || typeof parsed.accessToken !== 'string'
      || typeof parsed.nodeId !== 'string'
      || typeof parsed.nodeName !== 'string'
      || typeof parsed.version !== 'string'
      || !/^[A-Za-z0-9_-]{32,256}$/.test(parsed.accessToken)) {
      throw new Error('invalid saved local connection');
    }
    return { ...parsed, endpoint: normalizeNodeEndpoint(parsed.endpoint) } as LocalConnection;
  } catch {
    clearLocalConnection();
    return null;
  }
}

export function clearLocalConnection() {
  window.localStorage.removeItem(LOCAL_CONNECTION_KEY);
}

export async function startLogin(provider: 'github' | 'google'): Promise<void> {
  const verifier = base64Url(crypto.getRandomValues(new Uint8Array(32)));
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  const challenge = base64Url(new Uint8Array(digest));
  window.sessionStorage.setItem(OAUTH_VERIFIER_KEY, verifier);
  const returnTo = `${window.location.origin}/`;
  const url = new URL(`${controlPlaneUrl}/v1/auth/start/${provider}`);
  url.searchParams.set('return_to', returnTo);
  url.searchParams.set('code_challenge', challenge);
  window.location.assign(url.toString());
}

export function exchangeCloudCode(code: string): Promise<string> {
  if (!cloudCodeExchange) cloudCodeExchange = exchangeCloudCodeOnce(code);
  return cloudCodeExchange;
}

async function exchangeCloudCodeOnce(code: string): Promise<string> {
  const verifier = window.sessionStorage.getItem(OAUTH_VERIFIER_KEY);
  if (!verifier) throw new Error('This sign-in was not started in this browser tab.');
  const response = await cloudFetch(`${controlPlaneUrl}/v1/auth/exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, code_verifier: verifier }),
  });
  window.sessionStorage.removeItem(OAUTH_VERIFIER_KEY);
  if (!response.ok) throw new Error(`Sign-in exchange failed (${response.status}).`);
  const body = await response.json() as { access_token?: string };
  if (!body.access_token) throw new Error('The control plane returned an invalid sign-in response.');
  window.localStorage.setItem(CLOUD_SESSION_KEY, body.access_token);
  return body.access_token;
}

export function loadCloudSession(): string | null {
  return window.localStorage.getItem(CLOUD_SESSION_KEY);
}

function throwCloudResponseError(response: Response, message: string): never {
  if (response.status === 401) {
    window.localStorage.removeItem(CLOUD_SESSION_KEY);
    throw new CloudSessionExpiredError();
  }
  throw new Error(`${message} (${response.status}).`);
}

export async function signOutCloud(token: string | null): Promise<void> {
  window.localStorage.removeItem(CLOUD_SESSION_KEY);
  if (!token) return;
  await cloudFetch(`${controlPlaneUrl}/v1/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => undefined);
}

export async function fetchCloudIdentity(token: string): Promise<CloudIdentity> {
  const response = await cloudFetch(`${controlPlaneUrl}/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: 'no-store',
  });
  if (!response.ok) {
    throwCloudResponseError(response, 'The AgentSight control plane request failed');
  }
  return response.json() as Promise<CloudIdentity>;
}

export async function registerCloudNode(token: string, connection: LocalConnection): Promise<void> {
  const response = await cloudFetch(`${controlPlaneUrl}/v1/nodes`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id: connection.nodeId,
      name: connection.nodeName,
      version: connection.version,
    }),
  });
  if (!response.ok) throwCloudResponseError(response, 'Could not register this Node');
}

export async function fetchCloudNodes(token: string): Promise<CloudNode[]> {
  const response = await cloudFetch(`${controlPlaneUrl}/v1/nodes`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: 'no-store',
  });
  if (!response.ok) throwCloudResponseError(response, 'Could not load your Nodes');
  const body = await response.json() as {
    nodes?: Array<{
      id?: string;
      name?: string;
      version?: string | null;
      connection_mode?: string;
      last_seen_at?: number;
      created_at?: number;
    }>;
  };
  if (!Array.isArray(body.nodes)) throw new Error('The control plane returned an invalid Node list.');
  return body.nodes
    .filter((node) => typeof node.id === 'string' && typeof node.name === 'string')
    .map((node) => ({
      id: node.id!,
      name: node.name!,
      version: typeof node.version === 'string' ? node.version : null,
      connectionMode: 'direct',
      lastRegisteredAt: typeof node.last_seen_at === 'number' ? node.last_seen_at : 0,
      createdAt: typeof node.created_at === 'number' ? node.created_at : 0,
    }));
}

export async function forgetCloudNode(token: string, nodeId: string): Promise<void> {
  const response = await cloudFetch(`${controlPlaneUrl}/v1/nodes/${encodeURIComponent(nodeId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throwCloudResponseError(response, 'Could not remove this Node');
}
