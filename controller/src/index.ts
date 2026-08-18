// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import core, {
  allowedBrowserOrigin,
  authenticateUser,
  decryptDirectConfig,
  directConfigNodeIdFromPath,
  encryptDirectConfig,
  HttpError,
  normalizeDirectEndpoint,
} from './core.ts';
import {
  AccessError,
  type Action,
  type BillingStatus,
  type Plan,
  type Role,
  acceptInvite,
  createInvite,
  createOrganization,
  deleteDirectConfig,
  deleteNode,
  ensurePersonalOrganization,
  getConfig,
  getBillingProviderState,
  getDirectConfig,
  getNodeAccess,
  getOrganizationAccess,
  grantLifetimePro,
  listMembers,
  listNodes,
  listOrganizations,
  nodeIdFromPath,
  publicPricing,
  putConfig,
  registerNode,
  relayAction,
  removeMember,
  requireManagedPlan,
  requireOrganizationAction,
  setBilling,
  updateMemberRole,
  validNodeId,
} from './access.ts';
import {
  createStripeCheckout,
  createStripePortal,
  handleStripeWebhook,
  stripeCheckoutAvailability,
  type StripeEnv,
} from './billing.ts';
import {
  NodeRelay,
  browserRelayRoute,
  connectNodeRelay,
  proxyBrowserRelay,
  proxyNodeRequest,
  relayNodeSocketId,
  relayTokenHash,
  validRelayToken,
  type RelayEnv,
} from './relay.ts';

interface Env extends RelayEnv, StripeEnv {
  APP_ORIGIN: string;
  OAUTH_IP_LIMITER: RateLimit;
  OAUTH_LOCATION_LIMITER: RateLimit;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  ADMIN_API_TOKEN?: string;
  DIRECT_CONFIG_KEY?: string;
}

const NODE_CAPABILITY_ACTIONS = new Set<Action>([
  'node.info',
  'evidence.read',
  'session.read',
  'session.message',
]);
const BILLING_STATUSES = new Set<BillingStatus>(['inactive', 'trialing', 'active', 'past_due', 'canceled']);
const PLANS = new Set<Plan>(['free', 'pro', 'team', 'enterprise']);

export { NodeRelay };
export {
  allowedBrowserOrigin,
  allowedReturnTo,
  configuredOAuthProviders,
  decryptDirectConfig,
  directConfigNodeIdFromPath,
  encryptDirectConfig,
  githubApiHeaders,
  oauthStartAllowed,
  normalizeDirectEndpoint,
  sha256Base64Url,
} from './core.ts';
export { nodeIdFromPath, publicPricing, roleAllows, validNodeId } from './access.ts';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Node identity is deliberately separate from human identity. A Node
    // authenticates its outbound relay with its local bootstrap credential.
    const relayNodeId = relayNodeSocketId(url.pathname);
    if (relayNodeId && request.method === 'GET') {
      return connectNodeRelay(request, env, relayNodeId);
    }

    const requestOrigin = request.headers.get('Origin');
    if (!allowedBrowserOrigin(requestOrigin, env.APP_ORIGIN)) {
      return json({ error: 'origin_not_allowed' }, 403);
    }
    const respond = (response: Response) => cors(response, env, requestOrigin);
    if (request.method === 'OPTIONS') return respond(new Response(null, { status: 204 }));

    try {
      if (request.method === 'GET' && url.pathname === '/v1/pricing') {
        return respond(json({
          ...publicPricing(),
          checkout: stripeCheckoutAvailability(env),
        }));
      }

      if (isCoreIdentityRoute(url.pathname)) {
        return respond(await core.fetch(request, env));
      }

      if (request.method === 'POST' && url.pathname === '/v1/billing/webhook') {
        return respond(await handleStripeWebhook(request, env));
      }

      if (url.pathname.startsWith('/v1/admin/')) {
        return respond(await handleAdmin(request, env));
      }

      const user = await authenticateUser(request, env.DB);
      await ensurePersonalOrganization(env.DB, user);

      if (request.method === 'GET' && url.pathname === '/v1/organizations') {
        return respond(json({ organizations: await listOrganizations(env.DB, user) }));
      }

      if (request.method === 'POST' && url.pathname === '/v1/organizations') {
        const body = await readJson<{ name?: unknown }>(request);
        if (typeof body.name !== 'string') throw new AccessError(400, 'invalid_organization_name');
        const id = await createOrganization(env.DB, user.id, body.name);
        const organization = await getOrganizationAccess(env.DB, user.id, id);
        return respond(json({ organization }, 201));
      }

      if (request.method === 'POST' && url.pathname === '/v1/invitations/accept') {
        const body = await readJson<{ token?: unknown }>(request);
        if (typeof body.token !== 'string') throw new AccessError(400, 'invalid_invite');
        const organizationId = await acceptInvite(env.DB, user, body.token);
        return respond(json({ organization_id: organizationId, status: 'joined' }));
      }

      const organizationPath = organizationIdFromPath(url.pathname);
      if (organizationPath && !url.pathname.includes('/members')
          && !url.pathname.includes('/config/') && !url.pathname.endsWith('/billing')) {
        if (request.method === 'PATCH') {
          const access = await requireOrganizationAction(
            env.DB, user.id, organizationPath, 'organization.manage',
          );
          const body = await readJson<{ name?: unknown }>(request);
          const name = typeof body.name === 'string' ? body.name.trim() : '';
          if (!name || name.length > 128) throw new AccessError(400, 'invalid_organization_name');
          await env.DB.prepare('UPDATE organizations SET name = ?1, updated_at = ?2 WHERE id = ?3')
            .bind(name, nowSeconds(), access.id).run();
          return respond(json({ status: 'updated' }));
        }
        if (request.method === 'DELETE') {
          const access = await requireOrganizationAction(
            env.DB, user.id, organizationPath, 'organization.manage',
          );
          if (access.kind === 'personal') throw new AccessError(409, 'personal_organization_cannot_be_deleted');
          await env.DB.prepare('DELETE FROM organizations WHERE id = ?1').bind(access.id).run();
          return respond(new Response(null, { status: 204 }));
        }
      }

      const membersPath = organizationMembersPath(url.pathname);
      if (membersPath) {
        if (!membersPath.memberId && request.method === 'GET') {
          return respond(json({ members: await listMembers(env.DB, user.id, membersPath.organizationId) }));
        }
        if (!membersPath.memberId && request.method === 'POST') {
          const body = await readJson<{ email?: unknown; role?: unknown }>(request);
          if (typeof body.email !== 'string' || !isInviteRole(body.role)) {
            throw new AccessError(400, 'invalid_invite');
          }
          const token = await createInvite(
            env.DB, user.id, membersPath.organizationId, body.email, body.role,
          );
          return respond(json({
            status: 'invited',
            invite_url: `${new URL(env.APP_ORIGIN).origin}/#action=invite&token=${encodeURIComponent(token)}`,
            expires_in: 7 * 24 * 60 * 60,
          }, 201));
        }
        if (membersPath.memberId && request.method === 'PATCH') {
          const body = await readJson<{ role?: unknown }>(request);
          if (!isInviteRole(body.role)) throw new AccessError(400, 'invalid_role');
          await updateMemberRole(
            env.DB, user.id, membersPath.organizationId, membersPath.memberId, body.role,
          );
          return respond(json({ status: 'updated' }));
        }
        if (membersPath.memberId && request.method === 'DELETE') {
          await removeMember(env.DB, user.id, membersPath.organizationId, membersPath.memberId);
          return respond(new Response(null, { status: 204 }));
        }
      }

      const configPath = organizationConfigPath(url.pathname);
      if (configPath) {
        if (request.method === 'GET') {
          return respond(json(await getConfig(
            env.DB, user.id, configPath.organizationId, configPath.key,
          )));
        }
        if (request.method === 'PUT') {
          const body = await readJson<{ value?: unknown }>(request);
          await putConfig(env.DB, user.id, configPath.organizationId, configPath.key, body.value);
          return respond(json({ status: 'stored' }));
        }
      }

      const billingOrganizationId = organizationBillingPath(url.pathname);
      if (billingOrganizationId && request.method === 'GET') {
        const access = await requireOrganizationAction(
          env.DB, user.id, billingOrganizationId, 'billing.read',
        );
        return respond(json({
          organization_id: access.id,
          plan: access.plan,
          effective_plan: access.effectivePlan,
          billing_interval: access.billingInterval,
          billing_status: access.billingStatus,
          current_period_end: access.currentPeriodEnd,
          contributor_pro: access.contributorPro,
          price: publicPricing(),
          checkout: stripeCheckoutAvailability(env),
        }));
      }

      const billingAction = organizationBillingActionPath(url.pathname);
      if (billingAction && request.method === 'POST') {
        const rate = await env.OAUTH_IP_LIMITER.limit({ key: `billing:${user.id}` });
        if (!rate.success) throw new AccessError(429, 'billing_rate_limited');
        const provider = await getBillingProviderState(
          env.DB, user.id, billingAction.organizationId,
        );
        if (billingAction.action === 'portal') {
          return respond(json({
            url: await createStripePortal(env, provider.externalCustomerId),
          }));
        }
        const body = await readJson<{ plan?: unknown; interval?: unknown }>(request);
        if ((body.plan !== 'pro' && body.plan !== 'team')
            || (body.interval !== 'monthly' && body.interval !== 'annual')) {
          throw new AccessError(400, 'invalid_billing_checkout');
        }
        return respond(json({
          url: await createStripeCheckout(env, {
            organizationId: provider.access.id,
            organizationKind: provider.access.kind,
            email: user.email,
            plan: body.plan,
            interval: body.interval,
            externalCustomerId: provider.externalCustomerId,
            externalSubscriptionId: provider.externalSubscriptionId,
            billingStatus: provider.access.billingStatus,
          }),
        }));
      }

      if (url.pathname === '/v1/nodes' && request.method === 'GET') {
        const organizationId = url.searchParams.get('organization_id')
          || await ensurePersonalOrganization(env.DB, user);
        return respond(json({ nodes: await listNodes(env.DB, user.id, organizationId) }));
      }

      if (url.pathname === '/v1/nodes' && request.method === 'POST') {
        const body = await readJson<{
          id?: unknown;
          organization_id?: unknown;
          name?: unknown;
          version?: unknown;
          relay_token?: unknown;
          direct_config?: { endpoint?: unknown; access_key?: unknown };
        }>(request);
        if (typeof body.id !== 'string' || !validNodeId(body.id)
            || typeof body.name !== 'string' || !body.name.trim() || body.name.length > 128) {
          throw new AccessError(400, 'invalid_node');
        }
        const organizationId = typeof body.organization_id === 'string' && body.organization_id
          ? body.organization_id
          : await ensurePersonalOrganization(env.DB, user);
        let relayHash: string | null = null;
        if (body.relay_token !== undefined) {
          if (typeof body.relay_token !== 'string' || !validRelayToken(body.relay_token)) {
            throw new AccessError(400, 'invalid_relay_token');
          }
          relayHash = await relayTokenHash(body.relay_token);
        }
        let directConfig;
        if (body.direct_config !== undefined) {
          const endpoint = typeof body.direct_config.endpoint === 'string'
            ? normalizeDirectEndpoint(body.direct_config.endpoint) : null;
          const accessKey = typeof body.direct_config.access_key === 'string'
            ? body.direct_config.access_key : '';
          if (!endpoint || !validRelayToken(accessKey)) {
            throw new AccessError(400, 'invalid_direct_config');
          }
          directConfig = await encryptDirectConfig(requiredDirectConfigKey(env), user.id, body.id, {
            v: 1, endpoint, accessKey,
          });
        }
        await registerNode(env.DB, user.id, organizationId, {
          id: body.id,
          name: body.name.trim(),
          version: typeof body.version === 'string' ? body.version : null,
          relayTokenHash: relayHash,
          directConfig,
        });
        return respond(json({ id: body.id, organization_id: organizationId, status: 'registered' }, 201));
      }

      const directConfigNodeId = directConfigNodeIdFromPath(url.pathname);
      if (directConfigNodeId) {
        const access = await getNodeAccess(env.DB, user.id, directConfigNodeId, 'node.manage');
        requireManagedPlan(access.organization);
        if (request.method === 'GET') {
          const encrypted = await getDirectConfig(env.DB, user.id, directConfigNodeId);
          if (!encrypted) throw new AccessError(404, 'direct_config_not_saved');
          const direct = await decryptDirectConfig(
            requiredDirectConfigKey(env), user.id, directConfigNodeId, encrypted,
          );
          return respond(json({ endpoint: direct.endpoint, access_key: direct.accessKey }));
        }
        if (request.method === 'DELETE') {
          await deleteDirectConfig(env.DB, user.id, directConfigNodeId);
          return respond(new Response(null, { status: 204 }));
        }
      }

      const capabilityNodeId = nodeCapabilityPath(url.pathname);
      if (capabilityNodeId && request.method === 'POST') {
        const body = await readJson<{
          actions?: unknown;
          session_id?: unknown;
          ttl_seconds?: unknown;
        }>(request);
        const requested = Array.isArray(body.actions)
          ? body.actions.filter((value): value is Action => typeof value === 'string')
          : [];
        if (!requested.length || requested.some((action) => !NODE_CAPABILITY_ACTIONS.has(action))) {
          throw new AccessError(400, 'invalid_capability_actions');
        }
        let managedAccess = null;
        for (const action of requested) {
          const access = await getNodeAccess(env.DB, user.id, capabilityNodeId, action);
          managedAccess ||= access.organization;
        }
        if (!managedAccess) throw new AccessError(403, 'permission_denied');
        requireManagedPlan(managedAccess);
        const ttlSeconds = typeof body.ttl_seconds === 'number' && Number.isFinite(body.ttl_seconds)
          ? Math.max(30, Math.min(600, Math.floor(body.ttl_seconds)))
          : 300;
        const nodeResponse = await proxyNodeRequest(
          env,
          capabilityNodeId,
          'POST',
          '/api/v1/capabilities',
          JSON.stringify({
            actions: requested,
            session_id: typeof body.session_id === 'string' ? body.session_id : null,
            ttl_seconds: ttlSeconds,
          }),
        );
        return respond(nodeResponse);
      }

      const deleteNodeId = nodeIdFromPath(url.pathname);
      if (deleteNodeId && request.method === 'DELETE') {
        await deleteNode(env.DB, user.id, deleteNodeId);
        return respond(new Response(null, { status: 204 }));
      }

      const relayRoute = browserRelayRoute(request);
      if (relayRoute) {
        const action = relayAction(relayRoute.method, relayRoute.nodePath, relayRoute.statusOnly);
        const access = await getNodeAccess(env.DB, user.id, relayRoute.nodeId, action);
        requireManagedPlan(access.organization);
        return respond(await proxyBrowserRelay(request, env, relayRoute));
      }

      return respond(json({ error: 'not_found' }, 404));
    } catch (error) {
      if (error instanceof AccessError || error instanceof HttpError) {
        return respond(json({ error: error.code }, error.status));
      }
      console.error(error);
      return respond(json({ error: 'internal_error' }, 500));
    }
  },
} satisfies ExportedHandler<Env>;

async function handleAdmin(request: Request, env: Env): Promise<Response> {
  const configured = env.ADMIN_API_TOKEN;
  const supplied = request.headers.get('Authorization')?.match(/^Bearer (.+)$/)?.[1];
  if (!configured || !supplied || supplied !== configured) return json({ error: 'admin_auth_required' }, 401);
  const url = new URL(request.url);

  const billing = url.pathname.match(/^\/v1\/admin\/organizations\/([^/]+)\/billing$/);
  if (billing && request.method === 'POST') {
    const organizationId = decodeURIComponent(billing[1]);
    const body = await readJson<{
      plan?: unknown;
      interval?: unknown;
      status?: unknown;
      external_customer_id?: unknown;
      external_subscription_id?: unknown;
      current_period_end?: unknown;
    }>(request);
    if (typeof body.plan !== 'string' || !PLANS.has(body.plan as Plan)
        || typeof body.status !== 'string' || !BILLING_STATUSES.has(body.status as BillingStatus)
        || (body.interval !== undefined && body.interval !== null
          && body.interval !== 'monthly' && body.interval !== 'annual')) {
      throw new AccessError(400, 'invalid_billing_state');
    }
    await setBilling(env.DB, organizationId, {
      plan: body.plan as Plan,
      interval: body.interval as 'monthly' | 'annual' | null | undefined,
      status: body.status as BillingStatus,
      externalCustomerId: typeof body.external_customer_id === 'string' ? body.external_customer_id : null,
      externalSubscriptionId: typeof body.external_subscription_id === 'string' ? body.external_subscription_id : null,
      currentPeriodEnd: typeof body.current_period_end === 'number' ? body.current_period_end : null,
    });
    return json({ status: 'updated' });
  }

  if (url.pathname === '/v1/admin/entitlements/pro-lifetime' && request.method === 'POST') {
    const body = await readJson<{ email?: unknown; source?: unknown; source_ref?: unknown }>(request);
    if (typeof body.email !== 'string') throw new AccessError(400, 'invalid_email');
    const id = await grantLifetimePro(
      env.DB,
      body.email,
      typeof body.source === 'string' ? body.source : 'contributor',
      typeof body.source_ref === 'string' ? body.source_ref : null,
    );
    return json({ id, entitlement: 'pro_lifetime', status: 'active' }, 201);
  }

  return json({ error: 'not_found' }, 404);
}

function isCoreIdentityRoute(pathname: string): boolean {
  return pathname === '/v1/health'
    || pathname === '/v1/auth/providers'
    || pathname === '/v1/me'
    || pathname === '/v1/auth/exchange'
    || pathname === '/v1/auth/logout'
    || pathname.startsWith('/v1/auth/link/')
    || pathname.startsWith('/v1/auth/start/')
    || pathname.startsWith('/v1/auth/callback/');
}

function organizationIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/organizations\/([^/]+)$/);
  if (!match) return null;
  try { return decodeURIComponent(match[1]); } catch { return null; }
}

function organizationMembersPath(pathname: string): { organizationId: string; memberId: string | null } | null {
  const match = pathname.match(/^\/v1\/organizations\/([^/]+)\/members(?:\/([^/]+))?$/);
  if (!match) return null;
  try {
    return {
      organizationId: decodeURIComponent(match[1]),
      memberId: match[2] ? decodeURIComponent(match[2]) : null,
    };
  } catch {
    return null;
  }
}

function organizationConfigPath(pathname: string): { organizationId: string; key: string } | null {
  const match = pathname.match(/^\/v1\/organizations\/([^/]+)\/config\/([^/]+)$/);
  if (!match) return null;
  try {
    return { organizationId: decodeURIComponent(match[1]), key: decodeURIComponent(match[2]) };
  } catch {
    return null;
  }
}

function organizationBillingPath(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/organizations\/([^/]+)\/billing$/);
  if (!match) return null;
  try { return decodeURIComponent(match[1]); } catch { return null; }
}

function organizationBillingActionPath(
  pathname: string,
): { organizationId: string; action: 'checkout' | 'portal' } | null {
  const match = pathname.match(/^\/v1\/organizations\/([^/]+)\/billing\/(checkout|portal)$/);
  if (!match) return null;
  try {
    return {
      organizationId: decodeURIComponent(match[1]),
      action: match[2] as 'checkout' | 'portal',
    };
  } catch {
    return null;
  }
}

function nodeCapabilityPath(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/nodes\/([^/]+)\/capabilities$/);
  if (!match) return null;
  try {
    const id = decodeURIComponent(match[1]);
    return validNodeId(id) ? id : null;
  } catch {
    return null;
  }
}

function requiredDirectConfigKey(env: Env): string {
  if (!env.DIRECT_CONFIG_KEY) throw new AccessError(503, 'direct_config_unavailable');
  return env.DIRECT_CONFIG_KEY;
}

function isInviteRole(value: unknown): value is Exclude<Role, 'owner'> {
  return value === 'viewer' || value === 'operator' || value === 'admin';
}

export async function readJson<T>(request: Request): Promise<T> {
  const maxBytes = 96 * 1024;
  const declared = Number(request.headers.get('Content-Length') || '0');
  if (declared > maxBytes) throw new AccessError(413, 'request_too_large');
  if (!request.body) throw new AccessError(400, 'invalid_json');
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > maxBytes) {
        await reader.cancel('request too large');
        throw new AccessError(413, 'request_too_large');
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const joined = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    joined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  const text = new TextDecoder().decode(joined);
  try { return JSON.parse(text) as T; } catch { throw new AccessError(400, 'invalid_json'); }
}

function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

function cors(response: Response, env: Env, requestOrigin: string | null): Response {
  const headers = new Headers(response.headers);
  const responseOrigin = allowedBrowserOrigin(requestOrigin, env.APP_ORIGIN) && requestOrigin
    ? new URL(requestOrigin).origin
    : new URL(env.APP_ORIGIN).origin;
  headers.set('Access-Control-Allow-Origin', responseOrigin);
  headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Vary', 'Origin');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
