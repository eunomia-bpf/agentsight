// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export type Role = 'viewer' | 'operator' | 'admin' | 'owner';
export type Plan = 'free' | 'pro' | 'team' | 'enterprise';
export type EffectivePlan = Plan | 'unlimited';
export type OrganizationKind = 'personal' | 'team';
export type BillingStatus = 'inactive' | 'trialing' | 'active' | 'past_due' | 'canceled';

// Billing is modeled now, but is intentionally not enforced during the hosted
// preview. Keep persisted billing plans truthful while granting all registered
// users the complete currently implemented feature set.
export const HOSTED_PREVIEW_UNLIMITED = true;

export type Action =
  | 'organization.read'
  | 'organization.manage'
  | 'member.read'
  | 'member.manage'
  | 'node.read'
  | 'node.manage'
  | 'node.info'
  | 'evidence.read'
  | 'session.read'
  | 'session.message'
  | 'config.read'
  | 'config.write'
  | 'billing.read'
  | 'billing.manage';

export interface PlanDefinition {
  id: Plan;
  name: string;
  monthly_cents: number | null;
  annual_cents: number | null;
  per_seat: boolean;
  managed_connectivity: boolean;
  multi_member: boolean;
  custom: boolean;
}

export const PLAN_CATALOG: Record<Plan, PlanDefinition> = {
  free: {
    id: 'free',
    name: 'Free',
    monthly_cents: 0,
    annual_cents: 0,
    per_seat: false,
    managed_connectivity: false,
    multi_member: false,
    custom: false,
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    monthly_cents: 500,
    annual_cents: 4900,
    per_seat: false,
    managed_connectivity: true,
    multi_member: false,
    custom: false,
  },
  team: {
    id: 'team',
    name: 'Team',
    monthly_cents: 1000,
    annual_cents: null,
    per_seat: true,
    managed_connectivity: true,
    multi_member: true,
    custom: false,
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    monthly_cents: null,
    annual_cents: null,
    per_seat: false,
    managed_connectivity: true,
    multi_member: true,
    custom: true,
  },
};

const VIEWER_ACTIONS: Action[] = [
  'organization.read',
  'member.read',
  'node.read',
  'node.info',
  'evidence.read',
  'session.read',
  'config.read',
  'billing.read',
];
const OPERATOR_ACTIONS: Action[] = [...VIEWER_ACTIONS, 'session.message'];
const ADMIN_ACTIONS: Action[] = [
  ...OPERATOR_ACTIONS,
  'member.manage',
  'node.manage',
  'config.write',
];
const ROLE_ACTIONS: Record<Role, ReadonlySet<Action>> = {
  viewer: new Set(VIEWER_ACTIONS),
  operator: new Set(OPERATOR_ACTIONS),
  admin: new Set(ADMIN_ACTIONS),
  owner: new Set([...ADMIN_ACTIONS, 'organization.manage', 'billing.manage']),
};

export interface UserIdentity {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

interface OrganizationRow {
  id: string;
  name: string;
  kind: OrganizationKind;
  plan: Plan;
  billing_interval: 'monthly' | 'annual' | null;
  billing_status: BillingStatus;
  current_period_end: number | null;
  role: Role;
  contributor_pro: number;
  created_at: number;
}

export interface OrganizationAccess {
  id: string;
  name: string;
  kind: OrganizationKind;
  role: Role;
  plan: Plan;
  effectivePlan: EffectivePlan;
  billingInterval: 'monthly' | 'annual' | null;
  billingStatus: BillingStatus;
  currentPeriodEnd: number | null;
  contributorPro: boolean;
  createdAt: number;
}

export interface NodeAccess {
  organization: OrganizationAccess;
  nodeId: string;
}

export interface NodeRow {
  id: string;
  organization_id: string;
  name: string;
  version: string | null;
  connection_mode: string;
  last_seen_at: number;
  created_at: number;
  has_direct_config: number;
}

export interface DirectConfigRow {
  ciphertext: string;
  iv: string;
  version: 1;
}

const ACTIVE_BILLING = new Set<BillingStatus>(['active', 'trialing']);
const MANAGED_PLANS = new Set<EffectivePlan>(['pro', 'team', 'enterprise', 'unlimited']);
const TEAM_PLANS = new Set<EffectivePlan>(['team', 'enterprise', 'unlimited']);
const VALID_CONFIG_KEY = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$/;

export function roleAllows(role: Role, action: Action): boolean {
  return ROLE_ACTIONS[role]?.has(action) === true;
}

export function planAllowsManagedConnectivity(plan: EffectivePlan): boolean {
  return MANAGED_PLANS.has(plan);
}

export function planAllowsMultipleMembers(plan: EffectivePlan): boolean {
  return TEAM_PLANS.has(plan);
}

export function publicPricing() {
  return {
    currency: 'USD',
    plans: [PLAN_CATALOG.free, PLAN_CATALOG.pro, PLAN_CATALOG.team, PLAN_CATALOG.enterprise],
    preview: {
      unlimited: HOSTED_PREVIEW_UNLIMITED,
      description: 'All registered users currently receive unlimited hosted preview access.',
    },
    contributor_benefit: {
      entitlement: 'pro_lifetime',
      description: 'Meaningful AgentSight contributors receive personal Pro for life.',
      includes_team: false,
    },
  };
}

function resolveEffectivePlan(
  kind: OrganizationKind,
  plan: Plan,
  billingStatus: BillingStatus,
  contributorPro = false,
): EffectivePlan {
  if (HOSTED_PREVIEW_UNLIMITED) return 'unlimited';
  if (kind === 'personal' && contributorPro) return 'pro';
  if (plan === 'free') return 'free';
  return ACTIVE_BILLING.has(billingStatus) ? plan : 'free';
}

function organizationFromRow(row: OrganizationRow): OrganizationAccess {
  return {
    id: row.id,
    name: row.name,
    kind: row.kind,
    role: row.role,
    plan: row.plan,
    effectivePlan: resolveEffectivePlan(
      row.kind,
      row.plan,
      row.billing_status,
      Boolean(row.contributor_pro),
    ),
    billingInterval: row.billing_interval,
    billingStatus: row.billing_status,
    currentPeriodEnd: row.current_period_end,
    contributorPro: Boolean(row.contributor_pro),
    createdAt: row.created_at,
  };
}

export function personalOrganizationId(userId: string): string {
  return `org_personal_${userId.replaceAll('-', '')}`;
}

export async function ensurePersonalOrganization(
  db: D1Database,
  user: Pick<UserIdentity, 'id'>,
): Promise<string> {
  const id = personalOrganizationId(user.id);
  const now = nowSeconds();
  await db.batch([
    db.prepare(
      `INSERT OR IGNORE INTO organizations
       (id, name, kind, plan, billing_status, created_by_user_id, created_at, updated_at)
       VALUES (?1, 'Personal', 'personal', 'free', 'inactive', ?2, ?3, ?3)`,
    ).bind(id, user.id, now),
    db.prepare(
      `INSERT OR IGNORE INTO memberships
       (organization_id, user_id, role, created_at, updated_at)
       VALUES (?1, ?2, 'owner', ?3, ?3)`,
    ).bind(id, user.id, now),
  ]);
  return id;
}

const ORGANIZATION_SELECT = `
  SELECT o.id, o.name, o.kind, o.plan, o.billing_interval, o.billing_status,
         o.current_period_end, o.created_at, m.role,
         EXISTS(
           SELECT 1 FROM entitlements e
           WHERE e.user_id = m.user_id
             AND e.kind = 'pro_lifetime'
             AND e.revoked_at IS NULL
             AND (e.expires_at IS NULL OR e.expires_at >= ?2)
         ) AS contributor_pro
  FROM organizations o
  JOIN memberships m ON m.organization_id = o.id
  WHERE m.user_id = ?1`;

export async function listOrganizations(db: D1Database, user: UserIdentity): Promise<OrganizationAccess[]> {
  await ensurePersonalOrganization(db, user);
  const result = await db.prepare(`${ORGANIZATION_SELECT} ORDER BY o.kind ASC, o.created_at ASC`)
    .bind(user.id, nowSeconds()).all<OrganizationRow>();
  return result.results.map(organizationFromRow);
}

export async function getOrganizationAccess(
  db: D1Database,
  userId: string,
  organizationId: string,
): Promise<OrganizationAccess | null> {
  const row = await db.prepare(`${ORGANIZATION_SELECT} AND o.id = ?3 LIMIT 1`)
    .bind(userId, nowSeconds(), organizationId).first<OrganizationRow>();
  return row ? organizationFromRow(row) : null;
}

export async function createOrganization(
  db: D1Database,
  userId: string,
  name: string,
): Promise<string> {
  const normalized = name.trim();
  if (!normalized || normalized.length > 128) throw new AccessError(400, 'invalid_organization_name');
  const id = `org_${crypto.randomUUID().replaceAll('-', '')}`;
  const now = nowSeconds();
  await db.batch([
    db.prepare(
      `INSERT INTO organizations
       (id, name, kind, plan, billing_status, created_by_user_id, created_at, updated_at)
       VALUES (?1, ?2, 'team', 'free', 'inactive', ?3, ?4, ?4)`,
    ).bind(id, normalized, userId, now),
    db.prepare(
      `INSERT INTO memberships
       (organization_id, user_id, role, created_at, updated_at)
       VALUES (?1, ?2, 'owner', ?3, ?3)`,
    ).bind(id, userId, now),
  ]);
  return id;
}

export async function requireOrganizationAction(
  db: D1Database,
  userId: string,
  organizationId: string,
  action: Action,
): Promise<OrganizationAccess> {
  const access = await getOrganizationAccess(db, userId, organizationId);
  if (!access) throw new AccessError(404, 'organization_not_found');
  if (!roleAllows(access.role, action)) throw new AccessError(403, 'permission_denied');
  return access;
}

export async function getNodeAccess(
  db: D1Database,
  userId: string,
  nodeId: string,
  action: Action,
): Promise<NodeAccess> {
  const row = await db.prepare('SELECT organization_id FROM nodes WHERE id = ?1')
    .bind(nodeId).first<{ organization_id: string }>();
  if (!row) throw new AccessError(404, 'node_not_found');
  const organization = await requireOrganizationAction(db, userId, row.organization_id, action);
  return { organization, nodeId };
}

export function requireManagedPlan(access: OrganizationAccess): void {
  if (!planAllowsManagedConnectivity(access.effectivePlan)) {
    throw new AccessError(402, 'plan_upgrade_required');
  }
}

export function requireTeamPlan(access: OrganizationAccess): void {
  if (!planAllowsMultipleMembers(access.effectivePlan)) {
    throw new AccessError(402, 'team_plan_required');
  }
}

export async function listNodes(
  db: D1Database,
  userId: string,
  organizationId: string,
): Promise<NodeRow[]> {
  await requireOrganizationAction(db, userId, organizationId, 'node.read');
  const result = await db.prepare(
    `SELECT n.id, n.organization_id, n.name, n.version, n.connection_mode,
            n.last_seen_at, n.created_at,
            EXISTS(
              SELECT 1 FROM node_direct_configs d
              WHERE d.node_id = n.id AND d.owner_user_id = ?2
            ) AS has_direct_config
     FROM nodes n WHERE n.organization_id = ?1
     ORDER BY n.last_seen_at DESC LIMIT 500`,
  ).bind(organizationId, userId).all<NodeRow>();
  return result.results;
}

export async function registerNode(
  db: D1Database,
  userId: string,
  organizationId: string,
  node: {
    id: string;
    name: string;
    version?: string | null;
    relayTokenHash?: string | null;
    directConfig?: DirectConfigRow;
  },
): Promise<OrganizationAccess> {
  const access = await requireOrganizationAction(db, userId, organizationId, 'node.manage');
  requireManagedPlan(access);
  const existing = await db.prepare('SELECT organization_id FROM nodes WHERE id = ?1')
    .bind(node.id).first<{ organization_id: string }>();
  if (existing && existing.organization_id !== organizationId) {
    throw new AccessError(409, 'node_registered_to_another_organization');
  }
  const now = nowSeconds();
  const statements = [db.prepare(
    `INSERT INTO nodes
     (id, organization_id, name, version, public_key, relay_token_hash, connection_mode, last_seen_at, created_at)
     VALUES (?1, ?2, ?3, ?4, NULL, ?5, CASE WHEN ?5 IS NULL THEN 'direct' ELSE 'relay' END, ?6, ?6)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       version = excluded.version,
       relay_token_hash = COALESCE(excluded.relay_token_hash, nodes.relay_token_hash),
       connection_mode = CASE WHEN excluded.relay_token_hash IS NULL
         THEN nodes.connection_mode ELSE 'relay' END,
       last_seen_at = excluded.last_seen_at
     WHERE nodes.organization_id = excluded.organization_id`,
  ).bind(node.id, organizationId, node.name, node.version || null, node.relayTokenHash || null, now)];
  if (node.directConfig) {
    statements.push(db.prepare(
      `INSERT INTO node_direct_configs
       (node_id, owner_user_id, ciphertext, iv, version, created_at, updated_at)
       SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?6
       WHERE EXISTS (SELECT 1 FROM nodes WHERE id = ?1 AND organization_id = ?7)
       ON CONFLICT(node_id, owner_user_id) DO UPDATE SET
         ciphertext = excluded.ciphertext, iv = excluded.iv,
         version = excluded.version, updated_at = excluded.updated_at`,
    ).bind(
      node.id, userId, node.directConfig.ciphertext, node.directConfig.iv,
      node.directConfig.version, now, organizationId,
    ));
  }
  const [result] = await db.batch(statements);
  if (!result.meta.changes) throw new AccessError(409, 'node_registered_to_another_organization');
  return access;
}

export async function deleteNode(
  db: D1Database,
  userId: string,
  nodeId: string,
): Promise<void> {
  const access = await getNodeAccess(db, userId, nodeId, 'node.manage');
  await db.prepare('DELETE FROM nodes WHERE id = ?1 AND organization_id = ?2')
    .bind(nodeId, access.organization.id).run();
}

export async function getDirectConfig(
  db: D1Database,
  userId: string,
  nodeId: string,
): Promise<DirectConfigRow | null> {
  return db.prepare(
    `SELECT ciphertext, iv, version FROM node_direct_configs
     WHERE node_id = ?1 AND owner_user_id = ?2`,
  ).bind(nodeId, userId).first<DirectConfigRow>();
}

export async function deleteDirectConfig(db: D1Database, userId: string, nodeId: string): Promise<void> {
  await db.prepare('DELETE FROM node_direct_configs WHERE node_id = ?1 AND owner_user_id = ?2')
    .bind(nodeId, userId).run();
}

export async function listMembers(
  db: D1Database,
  userId: string,
  organizationId: string,
) {
  await requireOrganizationAction(db, userId, organizationId, 'member.read');
  const result = await db.prepare(
    `SELECT u.id, u.email, u.name, u.avatar_url, m.role, m.created_at
     FROM memberships m JOIN users u ON u.id = m.user_id
     WHERE m.organization_id = ?1
     ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 WHEN 'operator' THEN 2 ELSE 3 END,
              m.created_at ASC`,
  ).bind(organizationId).all();
  return result.results;
}

export async function createInvite(
  db: D1Database,
  userId: string,
  organizationId: string,
  email: string,
  role: Role,
): Promise<string> {
  const access = await requireOrganizationAction(db, userId, organizationId, 'member.manage');
  requireTeamPlan(access);
  if (access.kind !== 'team') throw new AccessError(400, 'personal_organization_cannot_invite');
  if (!['viewer', 'operator', 'admin'].includes(role)) throw new AccessError(400, 'invalid_role');
  const normalizedEmail = email.trim().toLowerCase();
  if (!normalizedEmail || normalizedEmail.length > 320 || !normalizedEmail.includes('@')) {
    throw new AccessError(400, 'invalid_email');
  }
  const token = randomToken();
  const now = nowSeconds();
  await db.prepare(
    `INSERT INTO organization_invites
     (token_hash, organization_id, email, role, invited_by_user_id, expires_at, consumed_at, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, NULL, ?7)`,
  ).bind(await sha256(token), organizationId, normalizedEmail, role, userId, now + 7 * 24 * 60 * 60, now).run();
  return token;
}

export async function acceptInvite(
  db: D1Database,
  user: UserIdentity,
  token: string,
): Promise<string> {
  if (!token || token.length > 512) throw new AccessError(400, 'invalid_invite');
  const now = nowSeconds();
  const tokenHash = await sha256(token);
  const candidate = await db.prepare(
    `SELECT organization_id, role FROM organization_invites
     WHERE token_hash = ?1 AND lower(email) = lower(?2)
       AND consumed_at IS NULL AND expires_at >= ?3`,
  ).bind(tokenHash, user.email, now).first<{ organization_id: string; role: Role }>();
  if (!candidate) throw new AccessError(400, 'invite_invalid_or_expired');

  const organization = await db.prepare(
    `SELECT id, kind, plan, billing_status FROM organizations WHERE id = ?1`,
  ).bind(candidate.organization_id)
    .first<{ id: string; kind: OrganizationKind; plan: Plan; billing_status: BillingStatus }>();
  if (!organization || organization.kind !== 'team') throw new AccessError(400, 'invite_invalid');
  if (!planAllowsMultipleMembers(resolveEffectivePlan(
    organization.kind,
    organization.plan,
    organization.billing_status,
  ))) {
    throw new AccessError(402, 'team_plan_required');
  }

  const consumed = await db.prepare(
    `UPDATE organization_invites SET consumed_at = ?1
     WHERE token_hash = ?2 AND lower(email) = lower(?3)
       AND consumed_at IS NULL AND expires_at >= ?1
     RETURNING organization_id, role`,
  ).bind(now, tokenHash, user.email).first<{ organization_id: string; role: Role }>();
  if (!consumed) throw new AccessError(400, 'invite_invalid_or_expired');

  await db.prepare(
    `INSERT INTO memberships (organization_id, user_id, role, created_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?4)
     ON CONFLICT(organization_id, user_id) DO UPDATE SET role = excluded.role, updated_at = excluded.updated_at`,
  ).bind(consumed.organization_id, user.id, consumed.role, now).run();
  return consumed.organization_id;
}

export async function updateMemberRole(
  db: D1Database,
  actorUserId: string,
  organizationId: string,
  memberUserId: string,
  role: Role,
): Promise<void> {
  const access = await requireOrganizationAction(db, actorUserId, organizationId, 'member.manage');
  requireTeamPlan(access);
  if (!['viewer', 'operator', 'admin'].includes(role)) throw new AccessError(400, 'invalid_role');
  const existing = await db.prepare(
    'SELECT role FROM memberships WHERE organization_id = ?1 AND user_id = ?2',
  ).bind(organizationId, memberUserId).first<{ role: Role }>();
  if (!existing) throw new AccessError(404, 'member_not_found');
  if (existing.role === 'owner') throw new AccessError(409, 'owner_role_is_immutable');
  await db.prepare(
    `UPDATE memberships SET role = ?1, updated_at = ?2 WHERE organization_id = ?3 AND user_id = ?4`,
  ).bind(role, nowSeconds(), organizationId, memberUserId).run();
}

export async function removeMember(
  db: D1Database,
  actorUserId: string,
  organizationId: string,
  memberUserId: string,
): Promise<void> {
  const access = await requireOrganizationAction(db, actorUserId, organizationId, 'member.manage');
  requireTeamPlan(access);
  const existing = await db.prepare(
    'SELECT role FROM memberships WHERE organization_id = ?1 AND user_id = ?2',
  ).bind(organizationId, memberUserId).first<{ role: Role }>();
  if (!existing) return;
  if (existing.role === 'owner') throw new AccessError(409, 'owner_cannot_be_removed');
  await db.prepare('DELETE FROM memberships WHERE organization_id = ?1 AND user_id = ?2')
    .bind(organizationId, memberUserId).run();
}

export async function getConfig(
  db: D1Database,
  userId: string,
  organizationId: string,
  key: string,
) {
  await requireOrganizationAction(db, userId, organizationId, 'config.read');
  validateConfigKey(key);
  const row = await db.prepare(
    'SELECT value_json, updated_by, updated_at FROM organization_configs WHERE organization_id = ?1 AND key = ?2',
  ).bind(organizationId, key).first<{ value_json: string; updated_by: string; updated_at: number }>();
  if (!row) throw new AccessError(404, 'config_not_found');
  return { key, value: JSON.parse(row.value_json), updated_by: row.updated_by, updated_at: row.updated_at };
}

export async function putConfig(
  db: D1Database,
  userId: string,
  organizationId: string,
  key: string,
  value: unknown,
): Promise<void> {
  await requireOrganizationAction(db, userId, organizationId, 'config.write');
  validateConfigKey(key);
  const encoded = JSON.stringify(value);
  if (encoded === undefined) throw new AccessError(400, 'invalid_config_value');
  if (new TextEncoder().encode(encoded).byteLength > 64 * 1024) throw new AccessError(413, 'config_too_large');
  const now = nowSeconds();
  await db.prepare(
    `INSERT INTO organization_configs (organization_id, key, value_json, updated_by, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?5)
     ON CONFLICT(organization_id, key) DO UPDATE SET
       value_json = excluded.value_json, updated_by = excluded.updated_by, updated_at = excluded.updated_at`,
  ).bind(organizationId, key, encoded, `user:${userId}`, now).run();
}

export async function setBilling(
  db: D1Database,
  organizationId: string,
  input: {
    plan: Plan;
    interval?: 'monthly' | 'annual' | null;
    status: BillingStatus;
    externalCustomerId?: string | null;
    externalSubscriptionId?: string | null;
    currentPeriodEnd?: number | null;
  },
): Promise<void> {
  if (!Object.hasOwn(PLAN_CATALOG, input.plan)) throw new AccessError(400, 'invalid_plan');
  const result = await db.prepare(
    `UPDATE organizations SET
       plan = ?1, billing_interval = ?2, billing_status = ?3,
       external_customer_id = ?4, external_subscription_id = ?5,
       current_period_end = ?6, updated_at = ?7
     WHERE id = ?8`,
  ).bind(
    input.plan,
    input.interval || null,
    input.status,
    input.externalCustomerId || null,
    input.externalSubscriptionId || null,
    input.currentPeriodEnd || null,
    nowSeconds(),
    organizationId,
  ).run();
  if (!result.meta.changes) throw new AccessError(404, 'organization_not_found');
}

export async function grantLifetimePro(
  db: D1Database,
  email: string,
  source: string,
  sourceRef?: string | null,
): Promise<string> {
  const user = await db.prepare('SELECT id FROM users WHERE lower(email) = lower(?1)')
    .bind(email.trim()).first<{ id: string }>();
  if (!user) throw new AccessError(404, 'user_not_found');
  const existing = await db.prepare(
    `SELECT id FROM entitlements
     WHERE user_id = ?1 AND kind = 'pro_lifetime' AND revoked_at IS NULL LIMIT 1`,
  ).bind(user.id).first<{ id: string }>();
  if (existing) return existing.id;
  const id = `ent_${crypto.randomUUID().replaceAll('-', '')}`;
  await db.prepare(
    `INSERT INTO entitlements
     (id, user_id, organization_id, kind, source, source_ref, expires_at, revoked_at, created_at)
     VALUES (?1, ?2, NULL, 'pro_lifetime', ?3, ?4, NULL, NULL, ?5)`,
  ).bind(id, user.id, source || 'contributor', sourceRef || null, nowSeconds()).run();
  return id;
}

export function relayAction(method: 'GET' | 'POST', nodePath: string | null, statusOnly: boolean): Action {
  if (statusOnly) return 'node.read';
  if (method === 'GET'
    && (nodePath?.startsWith('/api/v1/snapshot') || nodePath === '/api/v1/overview')) {
    return 'evidence.read';
  }
  if (method === 'GET' && nodePath?.startsWith('/api/v1/sessions/')) return 'session.read';
  if (method === 'POST' && nodePath?.endsWith('/messages')) return 'session.message';
  throw new AccessError(403, 'permission_denied');
}

export function validNodeId(value: string): boolean {
  return /^node_[A-Za-z0-9_]{1,123}$/.test(value);
}

export function nodeIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/nodes\/([^/]+)$/);
  if (!match) return null;
  try {
    const nodeId = decodeURIComponent(match[1]);
    return validNodeId(nodeId) ? nodeId : null;
  } catch {
    return null;
  }
}

export class AccessError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super(code);
    this.status = status;
    this.code = code;
  }
}

function validateConfigKey(key: string): void {
  if (!VALID_CONFIG_KEY.test(key)) throw new AccessError(400, 'invalid_config_key');
}

function randomToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return base64Url(bytes);
}

function base64Url(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}
