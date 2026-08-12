// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import core from './core.ts';
import {
  NodeRelay,
  browserRelayRoute,
  connectNodeRelay,
  proxyBrowserRelay,
  relayNodeSocketId,
  saveRelayCredential,
  validRelayToken,
  type RelayEnv,
} from './relay.ts';

interface Env extends RelayEnv {
  APP_ORIGIN: string;
  APP_PREVIEW_ORIGIN?: string;
  OAUTH_IP_LIMITER: RateLimit;
  OAUTH_LOCATION_LIMITER: RateLimit;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  DIRECT_CONFIG_KEY?: string;
}

export { NodeRelay };
export {
  allowedReturnTo,
  decryptDirectConfig,
  deleteOwnedNode,
  directConfigNodeIdFromPath,
  encryptDirectConfig,
  githubApiHeaders,
  nodeIdFromPath,
  normalizeDirectEndpoint,
  oauthStartAllowed,
  sha256Base64Url,
  validNodeId,
} from './core.ts';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Nodes authenticate with their persistent local bearer and keep one
    // outbound WebSocket. This route is intentionally outside browser CORS.
    const relayNodeId = relayNodeSocketId(url.pathname);
    if (relayNodeId && request.method === 'GET') {
      return connectNodeRelay(request, env, relayNodeId);
    }

    const requestOrigin = request.headers.get('Origin');
    if (requestOrigin && !allowedAppOrigin(requestOrigin, env)) {
      return json({ error: 'origin_not_allowed' }, 403);
    }

    if (request.method === 'GET' && url.pathname === '/v1/health') {
      return cors(json({ status: 'ok', service: 'agentsight-controller' }), env, requestOrigin);
    }

    const relayRoute = browserRelayRoute(request);
    if (relayRoute) {
      const ownerId = await authenticatedUserId(request, env);
      if (!ownerId) return cors(
        json({ error: 'authentication_required' }, 401), env, requestOrigin,
      );
      return cors(await proxyBrowserRelay(request, env, relayRoute, ownerId), env, requestOrigin);
    }

    // Node registration remains the same identity/ownership API. A locally
    // bound browser may additionally enroll the same persistent bearer for
    // relay. Only its SHA-256 hash is retained by Controller.
    let relayEnrollment: { nodeId: string; token: string } | null = null;
    if (request.method === 'POST' && url.pathname === '/v1/nodes') {
      const body = await request.clone().json().catch(() => ({})) as {
        id?: unknown;
        relay_token?: unknown;
      };
      if (body.relay_token !== undefined) {
        if (typeof body.id !== 'string'
            || typeof body.relay_token !== 'string'
            || !validRelayToken(body.relay_token)) {
          return cors(json({ error: 'invalid_relay_token' }, 400), env, requestOrigin);
        }
        relayEnrollment = { nodeId: body.id, token: body.relay_token };
      }
    }

    const response = await core.fetch(request, env);
    if (relayEnrollment && response.ok) {
      const ownerId = await authenticatedUserId(request, env);
      if (!ownerId || !await saveRelayCredential(
        env.DB,
        relayEnrollment.nodeId,
        ownerId,
        relayEnrollment.token,
      )) {
        return cors(json({ error: 'relay_enrollment_failed' }, 400), env, requestOrigin);
      }
    }
    return response;
  },
} satisfies ExportedHandler<Env>;

async function authenticatedUserId(request: Request, env: Env): Promise<string | null> {
  const authorization = request.headers.get('Authorization');
  if (!authorization) return null;
  const url = new URL(request.url);
  url.pathname = '/v1/me';
  url.search = '';
  const response = await core.fetch(new Request(url.toString(), {
    method: 'GET',
    headers: { Authorization: authorization },
  }), env);
  if (!response.ok) return null;
  const body = await response.json().catch(() => ({})) as { id?: unknown };
  return typeof body.id === 'string' ? body.id : null;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

function allowedAppOrigin(origin: string, env: Env): boolean {
  return [env.APP_ORIGIN, env.APP_PREVIEW_ORIGIN]
    .filter((candidate): candidate is string => Boolean(candidate))
    .some((candidate) => new URL(candidate).origin === origin);
}

function cors(response: Response, env: Env, requestOrigin: string | null): Response {
  const headers = new Headers(response.headers);
  const responseOrigin = requestOrigin && allowedAppOrigin(requestOrigin, env)
    ? requestOrigin
    : new URL(env.APP_ORIGIN).origin;
  headers.set('Access-Control-Allow-Origin', responseOrigin);
  headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  headers.set('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Vary', 'Origin');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
