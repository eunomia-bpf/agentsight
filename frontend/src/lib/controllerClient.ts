// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { LocalConnection } from '@/lib/nodeClient';
import { resolveControllerUrl } from '@/lib/controllerOrigin.mjs';

const CLOUD_SESSION_KEY = 'agentsight.cloud-session.v1';
const OAUTH_VERIFIER_KEY = 'agentsight.oauth-verifier.v1';
const REQUEST_TIMEOUT_MS = 8_000;
let cloudCodeExchange: Promise<string> | null = null;

export const controllerUrl = resolveControllerUrl(
  process.env.NEXT_PUBLIC_CONTROLLER_URL,
  process.env.NEXT_PUBLIC_CONTROL_PLANE_URL,
  typeof window === 'undefined' ? undefined : window.location,
);

export interface CloudIdentity {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  provider?: 'github' | 'google';
}

export type OrganizationRole = 'viewer' | 'operator' | 'admin' | 'owner';
export type OrganizationPlan = 'free' | 'pro' | 'team' | 'enterprise';
export type EffectivePlan = OrganizationPlan | 'unlimited';

export interface CloudOrganization {
  id: string;
  name: string;
  kind: 'personal' | 'team';
  role: OrganizationRole;
  plan: OrganizationPlan;
  effectivePlan: EffectivePlan;
  billingInterval: 'monthly' | 'annual' | null;
  billingStatus: 'inactive' | 'trialing' | 'active' | 'past_due' | 'canceled';
  currentPeriodEnd: number | null;
  contributorPro: boolean;
  createdAt: number;
}

export interface CloudNode {
  id: string;
  organizationId: string;
  name: string;
  version: string | null;
  connectionMode: 'direct' | 'relay';
  hasDirectConfig: boolean;
  lastRegisteredAt: number;
  createdAt: number;
}

export type LoginProvider = 'github' | 'google';

export async function fetchLoginProviders(): Promise<LoginProvider[]> {
  const response = await request(`${controllerUrl}/v1/auth/providers`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Controller sign-in status failed (${response.status}).`);
  }
  const body = await response.json().catch(() => null) as { providers?: unknown } | null;
  if (!body || !Array.isArray(body.providers)) {
    throw new Error('The Controller returned an invalid sign-in provider status.');
  }
  return body.providers.filter((provider): provider is LoginProvider => (
    provider === 'github' || provider === 'google'
  ));
}

export class CloudSessionExpiredError extends Error {
  constructor() {
    super('Your AgentSight sign-in has expired.');
    this.name = 'CloudSessionExpiredError';
  }
}

function request(input: string, init: RequestInit = {}) {
  return fetch(input, { ...init, signal: init.signal || AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
}

function base64Url(bytes: Uint8Array): string {
  let binary = '';
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function responseError(response: Response, fallback: string): Promise<never> {
  if (response.status === 401) {
    window.localStorage.removeItem(CLOUD_SESSION_KEY);
    throw new CloudSessionExpiredError();
  }
  const body = await response.json().catch(() => ({})) as { error?: string };
  throw new Error(body.error || `${fallback} (${response.status}).`);
}

function authHeaders(token: string, json = false): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    ...(json ? { 'Content-Type': 'application/json' } : {}),
  };
}

export async function startLogin(provider: 'github' | 'google'): Promise<void> {
  const verifier = base64Url(crypto.getRandomValues(new Uint8Array(32)));
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  window.sessionStorage.setItem(OAUTH_VERIFIER_KEY, verifier);
  const url = new URL(`${controllerUrl}/v1/auth/start/${provider}`);
  url.searchParams.set('return_to', `${window.location.origin}/`);
  url.searchParams.set('code_challenge', base64Url(new Uint8Array(digest)));
  window.location.assign(url.toString());
}

export function exchangeCloudCode(code: string): Promise<string> {
  if (!cloudCodeExchange) cloudCodeExchange = exchangeCloudCodeOnce(code);
  return cloudCodeExchange;
}

async function exchangeCloudCodeOnce(code: string): Promise<string> {
  const verifier = window.sessionStorage.getItem(OAUTH_VERIFIER_KEY);
  if (!verifier) throw new Error('This sign-in was not started in this browser tab.');
  const response = await request(`${controllerUrl}/v1/auth/exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, code_verifier: verifier }),
  });
  window.sessionStorage.removeItem(OAUTH_VERIFIER_KEY);
  if (!response.ok) throw new Error(`Sign-in exchange failed (${response.status}).`);
  const body = await response.json() as { access_token?: string };
  if (!body.access_token) throw new Error('The Controller returned an invalid sign-in response.');
  window.localStorage.setItem(CLOUD_SESSION_KEY, body.access_token);
  return body.access_token;
}

export function loadCloudSession(): string | null {
  return window.localStorage.getItem(CLOUD_SESSION_KEY);
}

export async function signOutCloud(token: string | null): Promise<void> {
  window.localStorage.removeItem(CLOUD_SESSION_KEY);
  if (!token) return;
  await request(`${controllerUrl}/v1/auth/logout`, {
    method: 'POST', headers: authHeaders(token),
  }).catch(() => undefined);
}

export async function fetchCloudIdentity(token: string): Promise<CloudIdentity> {
  const response = await request(`${controllerUrl}/v1/me`, {
    headers: authHeaders(token), cache: 'no-store',
  });
  if (!response.ok) await responseError(response, 'The AgentSight Controller request failed');
  return response.json() as Promise<CloudIdentity>;
}

export async function fetchOrganizations(token: string): Promise<CloudOrganization[]> {
  const response = await request(`${controllerUrl}/v1/organizations`, {
    headers: authHeaders(token), cache: 'no-store',
  });
  if (!response.ok) await responseError(response, 'Could not load organizations');
  const body = await response.json() as { organizations?: CloudOrganization[] };
  if (!Array.isArray(body.organizations)) throw new Error('The Controller returned an invalid organization list.');
  return body.organizations;
}

export async function createOrganization(token: string, name: string): Promise<CloudOrganization> {
  const response = await request(`${controllerUrl}/v1/organizations`, {
    method: 'POST', headers: authHeaders(token, true), body: JSON.stringify({ name }),
  });
  if (!response.ok) await responseError(response, 'Could not create organization');
  const body = await response.json() as { organization?: CloudOrganization };
  if (!body.organization) throw new Error('The Controller returned an invalid organization.');
  return body.organization;
}

export async function acceptOrganizationInvite(token: string, inviteToken: string): Promise<string> {
  const response = await request(`${controllerUrl}/v1/invitations/accept`, {
    method: 'POST', headers: authHeaders(token, true), body: JSON.stringify({ token: inviteToken }),
  });
  if (!response.ok) await responseError(response, 'Could not accept invitation');
  const body = await response.json() as { organization_id?: unknown };
  if (typeof body.organization_id !== 'string') throw new Error('The Controller returned an invalid invitation response.');
  return body.organization_id;
}

export async function fetchCloudNodes(token: string, organizationId: string): Promise<CloudNode[]> {
  const url = new URL(`${controllerUrl}/v1/nodes`);
  url.searchParams.set('organization_id', organizationId);
  const response = await request(url.toString(), { headers: authHeaders(token), cache: 'no-store' });
  if (!response.ok) await responseError(response, 'Could not load Nodes');
  const body = await response.json() as {
    nodes?: Array<{
      id?: string; organization_id?: string; name?: string; version?: string | null;
      connection_mode?: string; has_direct_config?: boolean | number;
      last_seen_at?: number; created_at?: number;
    }>;
  };
  if (!Array.isArray(body.nodes)) throw new Error('The Controller returned an invalid Node list.');
  return body.nodes
    .filter((node) => typeof node.id === 'string' && typeof node.name === 'string')
    .map((node) => ({
      id: node.id!,
      organizationId: typeof node.organization_id === 'string' ? node.organization_id : organizationId,
      name: node.name!,
      version: typeof node.version === 'string' ? node.version : null,
      connectionMode: node.connection_mode === 'relay' ? 'relay' : 'direct',
      hasDirectConfig: node.has_direct_config === true || node.has_direct_config === 1,
      lastRegisteredAt: typeof node.last_seen_at === 'number' ? node.last_seen_at : 0,
      createdAt: typeof node.created_at === 'number' ? node.created_at : 0,
    }));
}

export async function forgetCloudNode(token: string, nodeId: string): Promise<void> {
  const response = await request(`${controllerUrl}/v1/nodes/${encodeURIComponent(nodeId)}`, {
    method: 'DELETE', headers: authHeaders(token),
  });
  if (!response.ok) await responseError(response, 'Could not remove this Node');
}

export async function registerControllerNode(
  token: string,
  organizationId: string,
  connection: LocalConnection,
  bootstrapToken: string,
  saveDirect = false,
): Promise<void> {
  const response = await request(`${controllerUrl}/v1/nodes`, {
    method: 'POST',
    headers: authHeaders(token, true),
    body: JSON.stringify({
      id: connection.nodeId,
      organization_id: organizationId,
      name: connection.nodeName,
      version: connection.version,
      relay_token: bootstrapToken,
      ...(saveDirect ? {
        direct_config: { endpoint: connection.endpoint, access_key: bootstrapToken },
      } : {}),
    }),
  });
  if (!response.ok) await responseError(response, 'Could not register this Node');
}

export async function fetchControllerDirectConfig(
  token: string,
  node: CloudNode,
): Promise<{ endpoint: string; bootstrapToken: string }> {
  const response = await request(`${controllerUrl}/v1/nodes/${encodeURIComponent(node.id)}/direct`, {
    headers: authHeaders(token), cache: 'no-store',
  });
  if (!response.ok) await responseError(response, 'Could not load saved Direct config');
  const body = await response.json() as { endpoint?: unknown; access_key?: unknown };
  if (typeof body.endpoint !== 'string' || typeof body.access_key !== 'string') {
    throw new Error('The Controller returned an invalid Direct config.');
  }
  return { endpoint: body.endpoint, bootstrapToken: body.access_key };
}

export async function forgetControllerDirectConfig(token: string, nodeId: string): Promise<void> {
  const response = await request(`${controllerUrl}/v1/nodes/${encodeURIComponent(nodeId)}/direct`, {
    method: 'DELETE', headers: authHeaders(token),
  });
  if (!response.ok) await responseError(response, 'Could not remove saved Direct config');
}

export async function relayOnline(token: string, nodeId: string): Promise<boolean> {
  const response = await request(`${controllerUrl}/v1/nodes/${encodeURIComponent(nodeId)}/relay/status`, {
    headers: authHeaders(token), cache: 'no-store',
  });
  if (response.status === 401) await responseError(response, 'Could not check relay status');
  if (!response.ok) return false;
  const body = await response.json().catch(() => ({})) as { online?: unknown };
  return body.online === true;
}
