// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { validNodeId } from './access.ts';

interface Env {
  DB: D1Database;
  APP_ORIGIN: string;
  OAUTH_IP_LIMITER: RateLimit;
  OAUTH_LOCATION_LIMITER: RateLimit;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  DIRECT_CONFIG_KEY?: string;
}

export type Provider = 'github' | 'google';

interface OAuthProfile {
  provider: Provider;
  providerUserId: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

export interface UserRow {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

interface OAuthStartLimiter {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

const encoder = new TextEncoder();
const STATE_TTL_SECONDS = 10 * 60;
const AUTH_CODE_TTL_SECONDS = 2 * 60;
const SESSION_TTL_SECONDS = 30 * 24 * 60 * 60;
const PKCE_CHALLENGE_PATTERN = /^[A-Za-z0-9_-]{43}$/;
const PKCE_VERIFIER_PATTERN = /^[A-Za-z0-9_-]{43,128}$/;
const DIRECT_CONFIG_VERSION = 1;

interface DirectConfig {
  v: 1;
  endpoint: string;
  accessKey: string;
}

export interface EncryptedDirectConfig {
  ciphertext: string;
  iv: string;
  version: 1;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const requestOrigin = request.headers.get('Origin');
    if (!allowedBrowserOrigin(requestOrigin, env.APP_ORIGIN)) {
      return json({ error: 'origin_not_allowed' }, 403);
    }
    if (request.method === 'OPTIONS') {
      return cors(new Response(null, { status: 204 }), env, requestOrigin);
    }

    try {
      let response: Response;
      if (request.method === 'GET' && url.pathname === '/v1/health') {
        response = json({ status: 'ok', service: 'agentsight-controller' });
      } else if (request.method === 'GET' && url.pathname === '/v1/auth/providers') {
        response = json({ providers: configuredOAuthProviders(env) });
      } else if (request.method === 'GET' && url.pathname.startsWith('/v1/auth/start/')) {
        response = await startOAuth(request, env, providerFromPath(url.pathname));
      } else if (request.method === 'GET' && url.pathname.startsWith('/v1/auth/callback/')) {
        response = await finishOAuth(request, env, providerFromPath(url.pathname));
      } else if (request.method === 'POST' && url.pathname === '/v1/auth/exchange') {
        response = await exchangeAuthCode(request, env);
      } else if (request.method === 'POST' && url.pathname === '/v1/auth/logout') {
        response = await logout(request, env);
      } else if (request.method === 'GET' && url.pathname === '/v1/me') {
        response = await currentUser(request, env);
      } else {
        response = json({ error: 'not_found' }, 404);
      }
      return cors(response, env, requestOrigin);
    } catch (error) {
      if (error instanceof HttpError) {
        return cors(json({ error: error.code }, error.status), env, requestOrigin);
      }
      console.error(error);
      return cors(json({ error: 'internal_error' }, 500), env, requestOrigin);
    }
  },
} satisfies ExportedHandler<Env>;

function providerFromPath(pathname: string): Provider {
  const provider = pathname.split('/').pop();
  if (provider !== 'github' && provider !== 'google') throw new HttpError(404, 'unknown_provider');
  return provider;
}

async function startOAuth(request: Request, env: Env, provider: Provider): Promise<Response> {
  const url = new URL(request.url);
  const returnTo = allowedReturnTo(url.searchParams.get('return_to'), env.APP_ORIGIN);
  const codeChallenge = url.searchParams.get('code_challenge') || '';
  if (!PKCE_CHALLENGE_PATTERN.test(codeChallenge)) {
    return authErrorRedirect(returnTo, 'pkce_required');
  }
  const config = oauthConfig(provider, env, url.origin);
  if (!config) return authErrorRedirect(returnTo, `${provider}_login_not_configured`);

  const clientKey = request.headers.get('CF-Connecting-IP') || 'unknown';
  if (!await oauthStartAllowed(env.OAUTH_IP_LIMITER, env.OAUTH_LOCATION_LIMITER, clientKey)) {
    return authErrorRedirect(returnTo, 'rate_limited');
  }

  await deleteExpiredRows(env.DB);
  const state = randomToken();
  await env.DB.prepare(
    `INSERT INTO oauth_states (state_hash, provider, return_to, code_challenge, expires_at)
     VALUES (?1, ?2, ?3, ?4, ?5)`,
  ).bind(
    await sha256(state), provider, returnTo, codeChallenge, nowSeconds() + STATE_TTL_SECONDS,
  ).run();

  const authorize = new URL(config.authorizeUrl);
  authorize.searchParams.set('client_id', config.clientId);
  authorize.searchParams.set('redirect_uri', config.redirectUri);
  authorize.searchParams.set('response_type', 'code');
  authorize.searchParams.set('scope', config.scope);
  authorize.searchParams.set('state', state);
  if (provider === 'google') {
    authorize.searchParams.set('access_type', 'online');
    authorize.searchParams.set('prompt', 'select_account');
  }
  return Response.redirect(authorize.toString(), 302);
}

async function finishOAuth(request: Request, env: Env, provider: Provider): Promise<Response> {
  const url = new URL(request.url);
  const state = url.searchParams.get('state') || '';
  const code = url.searchParams.get('code') || '';
  const stateRow = await env.DB.prepare(
    `DELETE FROM oauth_states WHERE state_hash = ?1 AND provider = ?2 AND expires_at >= ?3
     RETURNING return_to, code_challenge`,
  ).bind(await sha256(state), provider, nowSeconds())
    .first<{ return_to: string; code_challenge: string | null }>();
  if (!stateRow) return authErrorRedirect(env.APP_ORIGIN, 'oauth_state_invalid');
  if (!code) return authErrorRedirect(stateRow.return_to, 'oauth_denied');
  if (!stateRow.code_challenge) return authErrorRedirect(stateRow.return_to, 'pkce_required');

  const config = oauthConfig(provider, env, url.origin);
  if (!config) return authErrorRedirect(stateRow.return_to, `${provider}_login_not_configured`);
  try {
    const profile = await fetchOAuthProfile(provider, code, config);
    const user = await upsertUser(env.DB, profile);
    const appCode = randomToken();
    await env.DB.prepare(
      `INSERT INTO auth_codes (code_hash, user_id, provider, code_challenge, expires_at)
       VALUES (?1, ?2, ?3, ?4, ?5)`,
    ).bind(
      await sha256(appCode), user.id, provider, stateRow.code_challenge,
      nowSeconds() + AUTH_CODE_TTL_SECONDS,
    ).run();
    return Response.redirect(`${stateRow.return_to}#action=auth&code=${encodeURIComponent(appCode)}`, 302);
  } catch (error) {
    const reason = error instanceof HttpError ? error.code : 'oauth_failed';
    console.error(JSON.stringify({ event: 'oauth_callback_failed', provider, reason }));
    return authErrorRedirect(stateRow.return_to, reason);
  }
}

async function exchangeAuthCode(request: Request, env: Env): Promise<Response> {
  const body = await readJson<{ code?: string; code_verifier?: string }>(request);
  if (!body.code || !body.code_verifier) return json({ error: 'code_and_verifier_required' }, 400);
  if (!PKCE_VERIFIER_PATTERN.test(body.code_verifier)) {
    return json({ error: 'code_verifier_invalid' }, 400);
  }
  const codeChallenge = await sha256Base64Url(body.code_verifier);
  const row = await env.DB.prepare(
    `UPDATE auth_codes SET consumed_at = ?1
     WHERE code_hash = ?2 AND code_challenge = ?3
       AND consumed_at IS NULL AND expires_at >= ?1
     RETURNING user_id`,
  ).bind(nowSeconds(), await sha256(body.code), codeChallenge).first<{ user_id: string }>();
  if (!row) return json({ error: 'code_invalid_or_expired' }, 401);

  const token = randomToken();
  const now = nowSeconds();
  await env.DB.prepare(
    'INSERT INTO sessions (token_hash, user_id, expires_at, created_at, last_seen_at) VALUES (?1, ?2, ?3, ?4, ?4)',
  ).bind(await sha256(token), row.user_id, now + SESSION_TTL_SECONDS, now).run();
  return json({ access_token: token, token_type: 'Bearer', expires_in: SESSION_TTL_SECONDS });
}

async function currentUser(request: Request, env: Env): Promise<Response> {
  const user = await authenticateUser(request, env.DB);
  return json(publicUser(user));
}

async function logout(request: Request, env: Env): Promise<Response> {
  const token = request.headers.get('Authorization')?.match(/^Bearer (.+)$/)?.[1];
  if (token) {
    await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?1')
      .bind(await sha256(token)).run();
  }
  return new Response(null, { status: 204 });
}

export async function authenticateUser(request: Request, db: D1Database): Promise<UserRow> {
  const token = request.headers.get('Authorization')?.match(/^Bearer (.+)$/)?.[1];
  if (!token) throw new HttpError(401, 'authentication_required');
  const now = nowSeconds();
  const user = await db.prepare(
    `SELECT u.id, u.email, u.name, u.avatar_url
     FROM sessions s JOIN users u ON u.id = s.user_id
     WHERE s.token_hash = ?1 AND s.expires_at >= ?2`,
  ).bind(await sha256(token), now).first<UserRow>();
  if (!user) throw new HttpError(401, 'session_invalid_or_expired');
  await db.prepare('UPDATE sessions SET last_seen_at = ?1 WHERE token_hash = ?2')
    .bind(now, await sha256(token)).run();
  return user;
}

async function fetchOAuthProfile(
  provider: Provider,
  code: string,
  config: NonNullable<ReturnType<typeof oauthConfig>>,
): Promise<OAuthProfile> {
  const tokenResponse = await fetch(config.tokenUrl, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      ...(provider === 'github' ? { 'User-Agent': 'AgentSight-Control' } : {}),
    },
    body: new URLSearchParams({
      client_id: config.clientId,
      client_secret: config.clientSecret,
      code,
      redirect_uri: config.redirectUri,
      grant_type: 'authorization_code',
    }),
  });
  const token = await tokenResponse.json() as { access_token?: string };
  if (!tokenResponse.ok || !token.access_token) throw new HttpError(401, 'oauth_token_exchange_failed');
  return provider === 'github'
    ? githubProfile(token.access_token)
    : googleProfile(token.access_token);
}

async function githubProfile(accessToken: string): Promise<OAuthProfile> {
  const headers = githubApiHeaders(accessToken);
  const [userResponse, emailResponse] = await Promise.all([
    fetch('https://api.github.com/user', { headers }),
    fetch('https://api.github.com/user/emails', { headers }),
  ]);
  const user = await userResponse.json() as { id?: number; login?: string; name?: string; avatar_url?: string };
  const emails = await emailResponse.json() as unknown;
  if (!userResponse.ok || !emailResponse.ok || !Array.isArray(emails) || !user.id) {
    throw new HttpError(401, 'github_profile_unavailable');
  }
  const verifiedEmails = emails as Array<{ email: string; primary: boolean; verified: boolean }>;
  const email = verifiedEmails.find((item) => item.primary && item.verified)?.email
    || verifiedEmails.find((item) => item.verified)?.email;
  if (!email) throw new HttpError(401, 'github_profile_unavailable');
  return {
    provider: 'github',
    providerUserId: String(user.id),
    email,
    name: user.name || user.login || email,
    avatarUrl: user.avatar_url,
  };
}

async function googleProfile(accessToken: string): Promise<OAuthProfile> {
  const response = await fetch('https://openidconnect.googleapis.com/v1/userinfo', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const user = await response.json() as {
    sub?: string;
    email?: string;
    email_verified?: boolean;
    name?: string;
    picture?: string;
  };
  if (!response.ok || !user.sub || !user.email || !user.email_verified) {
    throw new HttpError(401, 'google_profile_unavailable');
  }
  return {
    provider: 'google',
    providerUserId: user.sub,
    email: user.email,
    name: user.name || user.email,
    avatarUrl: user.picture,
  };
}

async function upsertUser(db: D1Database, profile: OAuthProfile): Promise<UserRow> {
  const account = await db.prepare(
    `SELECT u.id, u.email, u.name, u.avatar_url FROM oauth_accounts a
     JOIN users u ON u.id = a.user_id WHERE a.provider = ?1 AND a.provider_user_id = ?2`,
  ).bind(profile.provider, profile.providerUserId).first<UserRow>();
  const byEmail = account || await db.prepare(
    'SELECT id, email, name, avatar_url FROM users WHERE email = ?1',
  ).bind(profile.email).first<UserRow>();
  const id = byEmail?.id || crypto.randomUUID();
  const now = nowSeconds();
  await db.batch([
    db.prepare(
      `INSERT INTO users (id, email, name, avatar_url, created_at, updated_at)
       VALUES (?1, ?2, ?3, ?4, ?5, ?5)
       ON CONFLICT(id) DO UPDATE SET email = excluded.email, name = excluded.name,
       avatar_url = excluded.avatar_url, updated_at = excluded.updated_at`,
    ).bind(id, profile.email, profile.name, profile.avatarUrl || null, now),
    db.prepare(
      `INSERT INTO oauth_accounts (provider, provider_user_id, user_id) VALUES (?1, ?2, ?3)
       ON CONFLICT(provider, provider_user_id) DO UPDATE SET user_id = excluded.user_id`,
    ).bind(profile.provider, profile.providerUserId, id),
  ]);
  return { id, email: profile.email, name: profile.name, avatar_url: profile.avatarUrl || null };
}

function oauthConfig(provider: Provider, env: Env, origin: string) {
  if (provider === 'github' && env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET) {
    return {
      clientId: env.GITHUB_CLIENT_ID,
      clientSecret: env.GITHUB_CLIENT_SECRET,
      authorizeUrl: 'https://github.com/login/oauth/authorize',
      tokenUrl: 'https://github.com/login/oauth/access_token',
      scope: 'read:user user:email',
      redirectUri: `${origin}/v1/auth/callback/github`,
    };
  }
  if (provider === 'google' && env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET) {
    return {
      clientId: env.GOOGLE_CLIENT_ID,
      clientSecret: env.GOOGLE_CLIENT_SECRET,
      authorizeUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
      tokenUrl: 'https://oauth2.googleapis.com/token',
      scope: 'openid email profile',
      redirectUri: `${origin}/v1/auth/callback/google`,
    };
  }
  return null;
}

export function allowedBrowserOrigin(
  value: string | null,
  appOrigin: string,
): boolean {
  if (!value) return true;
  try {
    return new URL(value).origin === new URL(appOrigin).origin;
  } catch {
    return false;
  }
}

export function configuredOAuthProviders(
  env: Pick<Env, 'GITHUB_CLIENT_ID' | 'GITHUB_CLIENT_SECRET' | 'GOOGLE_CLIENT_ID' | 'GOOGLE_CLIENT_SECRET'>,
): Provider[] {
  const providers: Provider[] = [];
  if (env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET) providers.push('github');
  if (env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET) providers.push('google');
  return providers;
}

export function directConfigNodeIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/v1\/nodes\/([^/]+)\/direct$/);
  if (!match) return null;
  try {
    const nodeId = decodeURIComponent(match[1]);
    return validNodeId(nodeId) ? nodeId : null;
  } catch {
    return null;
  }
}

export function normalizeDirectEndpoint(value: string): string | null {
  try {
    const endpoint = new URL(value.trim());
    if (!['http:', 'https:'].includes(endpoint.protocol)
        || !endpoint.hostname || endpoint.username || endpoint.password) return null;
    endpoint.pathname = '';
    endpoint.search = '';
    endpoint.hash = '';
    return endpoint.toString().replace(/\/$/, '');
  } catch {
    return null;
  }
}

export async function encryptDirectConfig(
  masterSecret: string,
  userId: string,
  nodeId: string,
  config: DirectConfig,
): Promise<EncryptedDirectConfig> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveDirectConfigKey(masterSecret, userId, nodeId, ['encrypt']);
  const ciphertext = await crypto.subtle.encrypt({
    name: 'AES-GCM', iv: bufferSource(iv), additionalData: directConfigAad(userId, nodeId),
  }, key, encoder.encode(JSON.stringify(config)));
  return { ciphertext: base64UrlEncode(new Uint8Array(ciphertext)), iv: base64UrlEncode(iv), version: 1 };
}

export async function decryptDirectConfig(
  masterSecret: string,
  userId: string,
  nodeId: string,
  encrypted: EncryptedDirectConfig,
): Promise<DirectConfig> {
  if (encrypted.version !== DIRECT_CONFIG_VERSION) throw new Error('unsupported direct config');
  const key = await deriveDirectConfigKey(masterSecret, userId, nodeId, ['decrypt']);
  const plaintext = await crypto.subtle.decrypt({
    name: 'AES-GCM',
    iv: bufferSource(base64UrlDecode(encrypted.iv)),
    additionalData: directConfigAad(userId, nodeId),
  }, key, bufferSource(base64UrlDecode(encrypted.ciphertext)));
  const config = JSON.parse(new TextDecoder().decode(plaintext)) as DirectConfig;
  const endpoint = normalizeDirectEndpoint(config.endpoint);
  if (config.v !== DIRECT_CONFIG_VERSION || !endpoint || !/^[A-Za-z0-9_-]{32,256}$/.test(config.accessKey)) {
    throw new Error('invalid direct config');
  }
  return { ...config, endpoint };
}

async function deriveDirectConfigKey(
  masterSecret: string,
  userId: string,
  nodeId: string,
  usages: KeyUsage[],
): Promise<CryptoKey> {
  const master = base64UrlDecode(masterSecret);
  if (master.byteLength !== 32) throw new Error('DIRECT_CONFIG_KEY must contain 32 bytes');
  const material = await crypto.subtle.importKey('raw', bufferSource(master), 'HKDF', false, ['deriveKey']);
  return crypto.subtle.deriveKey({
    name: 'HKDF', hash: 'SHA-256', salt: encoder.encode('agentsight-direct-config-v1'),
    info: encoder.encode(`${userId}\0${nodeId}`),
  }, material, { name: 'AES-GCM', length: 256 }, false, usages);
}

function directConfigAad(userId: string, nodeId: string): ArrayBuffer {
  return bufferSource(encoder.encode(`agentsight-direct-config-v1\0${userId}\0${nodeId}`));
}

function bufferSource(value: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(value.byteLength);
  copy.set(value);
  return copy.buffer;
}

function base64UrlEncode(value: Uint8Array): string {
  return btoa(String.fromCharCode(...value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(value: string): Uint8Array {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
}

export function allowedReturnTo(
  value: string | null,
  appOrigin: string,
): string {
  if (!value) return `${appOrigin.replace(/\/$/, '')}/`;
  try {
    const candidate = new URL(value);
    if (allowedBrowserOrigin(candidate.origin, appOrigin)) {
      return `${candidate.origin}/`;
    }
  } catch { /* fall through */ }
  return `${appOrigin.replace(/\/$/, '')}/`;
}

function authErrorRedirect(returnTo: string, error: string): Response {
  return Response.redirect(`${returnTo}#action=auth-error&error=${encodeURIComponent(error)}`, 302);
}

function publicUser(user: UserRow) {
  return {
    id: user.id,
    email: user.email,
    name: user.name,
    avatarUrl: user.avatar_url || undefined,
  };
}

async function readJson<T>(request: Request): Promise<T> {
  const length = Number(request.headers.get('Content-Length') || '0');
  if (length > 16_384) throw new HttpError(413, 'request_too_large');
  const text = await request.text();
  if (encoder.encode(text).byteLength > 16_384) throw new HttpError(413, 'request_too_large');
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new HttpError(400, 'invalid_json');
  }
}

function randomToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function sha256Base64Url(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(value));
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function githubApiHeaders(accessToken: string): Record<string, string> {
  return {
    Authorization: `Bearer ${accessToken}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'AgentSight-Control',
  };
}

export async function oauthStartAllowed(
  clientLimiter: OAuthStartLimiter,
  locationLimiter: OAuthStartLimiter,
  clientKey: string,
): Promise<boolean> {
  const clientLimit = await clientLimiter.limit({ key: clientKey });
  if (!clientLimit.success) return false;
  return (await locationLimiter.limit({ key: 'oauth-start' })).success;
}

async function deleteExpiredRows(db: D1Database): Promise<void> {
  const now = nowSeconds();
  await db.batch([
    db.prepare('DELETE FROM oauth_states WHERE expires_at < ?1').bind(now),
    db.prepare('DELETE FROM auth_codes WHERE expires_at < ?1 OR consumed_at IS NOT NULL').bind(now),
    db.prepare('DELETE FROM sessions WHERE expires_at < ?1').bind(now),
    db.prepare('DELETE FROM organization_invites WHERE expires_at < ?1 OR consumed_at IS NOT NULL').bind(now),
  ]);
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
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export class HttpError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string) {
    super(code);
    this.status = status;
    this.code = code;
  }
}
