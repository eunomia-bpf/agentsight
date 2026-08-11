// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

interface Env {
  DB: D1Database;
  APP_ORIGIN: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
}

type Provider = 'github' | 'google';

interface OAuthProfile {
  provider: Provider;
  providerUserId: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

interface UserRow {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

const encoder = new TextEncoder();
const STATE_TTL_SECONDS = 10 * 60;
const AUTH_CODE_TTL_SECONDS = 2 * 60;
const SESSION_TTL_SECONDS = 30 * 24 * 60 * 60;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return cors(new Response(null, { status: 204 }), env);

    try {
      let response: Response;
      if (request.method === 'GET' && url.pathname === '/v1/health') {
        response = json({ status: 'ok', service: 'agentsight-control' });
      } else if (request.method === 'GET' && url.pathname.startsWith('/v1/auth/start/')) {
        response = await startOAuth(request, env, providerFromPath(url.pathname));
      } else if (request.method === 'GET' && url.pathname.startsWith('/v1/auth/callback/')) {
        response = await finishOAuth(request, env, providerFromPath(url.pathname));
      } else if (request.method === 'POST' && url.pathname === '/v1/auth/exchange') {
        response = await exchangeAuthCode(request, env);
      } else if (request.method === 'GET' && url.pathname === '/v1/me') {
        response = await currentUser(request, env);
      } else if (url.pathname === '/v1/nodes' && request.method === 'GET') {
        response = await listNodes(request, env);
      } else if (url.pathname === '/v1/nodes' && request.method === 'POST') {
        response = await registerNode(request, env);
      } else {
        response = json({ error: 'not_found' }, 404);
      }
      return cors(response, env);
    } catch (error) {
      if (error instanceof HttpError) {
        return cors(json({ error: error.code }, error.status), env);
      }
      console.error(error);
      return cors(json({ error: 'internal_error' }, 500), env);
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
  const config = oauthConfig(provider, env, url.origin);
  if (!config) return authErrorRedirect(returnTo, `${provider}_login_not_configured`);

  const state = randomToken();
  await env.DB.prepare(
    'INSERT INTO oauth_states (state_hash, provider, return_to, expires_at) VALUES (?1, ?2, ?3, ?4)',
  ).bind(await sha256(state), provider, returnTo, nowSeconds() + STATE_TTL_SECONDS).run();

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
    'DELETE FROM oauth_states WHERE state_hash = ?1 AND provider = ?2 AND expires_at >= ?3 RETURNING return_to',
  ).bind(await sha256(state), provider, nowSeconds()).first<{ return_to: string }>();
  if (!stateRow || !code) return authErrorRedirect(env.APP_ORIGIN, 'oauth_state_invalid');

  const config = oauthConfig(provider, env, url.origin);
  if (!config) return authErrorRedirect(stateRow.return_to, `${provider}_login_not_configured`);
  const profile = await fetchOAuthProfile(provider, code, config);
  const user = await upsertUser(env.DB, profile);
  const appCode = randomToken();
  await env.DB.prepare(
    'INSERT INTO auth_codes (code_hash, user_id, provider, expires_at) VALUES (?1, ?2, ?3, ?4)',
  ).bind(await sha256(appCode), user.id, provider, nowSeconds() + AUTH_CODE_TTL_SECONDS).run();
  return Response.redirect(`${stateRow.return_to}#action=auth&code=${encodeURIComponent(appCode)}`, 302);
}

async function exchangeAuthCode(request: Request, env: Env): Promise<Response> {
  const body = await readJson<{ code?: string }>(request);
  if (!body.code) return json({ error: 'code_required' }, 400);
  const row = await env.DB.prepare(
    `UPDATE auth_codes SET consumed_at = ?1
     WHERE code_hash = ?2 AND consumed_at IS NULL AND expires_at >= ?1
     RETURNING user_id`,
  ).bind(nowSeconds(), await sha256(body.code)).first<{ user_id: string }>();
  if (!row) return json({ error: 'code_invalid_or_expired' }, 401);

  const token = randomToken();
  const now = nowSeconds();
  await env.DB.prepare(
    'INSERT INTO sessions (token_hash, user_id, expires_at, created_at, last_seen_at) VALUES (?1, ?2, ?3, ?4, ?4)',
  ).bind(await sha256(token), row.user_id, now + SESSION_TTL_SECONDS, now).run();
  return json({ access_token: token, token_type: 'Bearer', expires_in: SESSION_TTL_SECONDS });
}

async function currentUser(request: Request, env: Env): Promise<Response> {
  const user = await requireUser(request, env.DB);
  return json(publicUser(user));
}

async function listNodes(request: Request, env: Env): Promise<Response> {
  const user = await requireUser(request, env.DB);
  const result = await env.DB.prepare(
    `SELECT id, name, version, connection_mode, last_seen_at, created_at
     FROM nodes WHERE owner_user_id = ?1 ORDER BY last_seen_at DESC LIMIT 200`,
  ).bind(user.id).all();
  return json({ nodes: result.results });
}

async function registerNode(request: Request, env: Env): Promise<Response> {
  const user = await requireUser(request, env.DB);
  const body = await readJson<{
    id?: string;
    name?: string;
    version?: string;
    public_key?: string;
    connection_mode?: string;
  }>(request);
  if (!body.id || !body.name || body.id.length > 128 || body.name.length > 128) {
    return json({ error: 'invalid_node' }, 400);
  }
  const mode = body.connection_mode === 'managed' ? 'managed' : 'direct';
  const now = nowSeconds();
  const result = await env.DB.prepare(
    `INSERT INTO nodes (id, owner_user_id, name, version, public_key, connection_mode, last_seen_at, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?7)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name, version = excluded.version, public_key = excluded.public_key,
       connection_mode = excluded.connection_mode, last_seen_at = excluded.last_seen_at
     WHERE nodes.owner_user_id = excluded.owner_user_id`,
  ).bind(body.id, user.id, body.name, body.version || null, body.public_key || null, mode, now).run();
  if (!result.meta.changes) return json({ error: 'node_owned_by_another_user' }, 409);
  return json({ id: body.id, status: 'registered' }, 201);
}

async function requireUser(request: Request, db: D1Database): Promise<UserRow> {
  const token = request.headers.get('Authorization')?.match(/^Bearer (.+)$/)?.[1];
  if (!token) throw new HttpError(401, 'authentication_required');
  const now = nowSeconds();
  const user = await db.prepare(
    `SELECT u.id, u.email, u.name, u.avatar_url
     FROM sessions s JOIN users u ON u.id = s.user_id
     WHERE s.token_hash = ?1 AND s.expires_at >= ?2`,
  ).bind(await sha256(token), now).first<UserRow>();
  if (!user) throw new HttpError(401, 'session_invalid_or_expired');
  return user;
}

async function fetchOAuthProfile(
  provider: Provider,
  code: string,
  config: NonNullable<ReturnType<typeof oauthConfig>>,
): Promise<OAuthProfile> {
  const tokenResponse = await fetch(config.tokenUrl, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' },
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
  const headers = { Authorization: `Bearer ${accessToken}`, Accept: 'application/vnd.github+json' };
  const [userResponse, emailResponse] = await Promise.all([
    fetch('https://api.github.com/user', { headers }),
    fetch('https://api.github.com/user/emails', { headers }),
  ]);
  const user = await userResponse.json() as { id?: number; login?: string; name?: string; avatar_url?: string };
  const emails = await emailResponse.json() as Array<{ email: string; primary: boolean; verified: boolean }>;
  const email = emails.find((item) => item.primary && item.verified)?.email
    || emails.find((item) => item.verified)?.email;
  if (!userResponse.ok || !email || !user.id) throw new HttpError(401, 'github_profile_unavailable');
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

function allowedReturnTo(value: string | null, appOrigin: string): string {
  if (!value) return `${appOrigin.replace(/\/$/, '')}/`;
  try {
    const candidate = new URL(value);
    if (candidate.origin === new URL(appOrigin).origin) return `${candidate.origin}/`;
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
  return request.json() as Promise<T>;
}

function randomToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
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

function cors(response: Response, env: Env): Response {
  const headers = new Headers(response.headers);
  headers.set('Access-Control-Allow-Origin', env.APP_ORIGIN);
  headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  headers.set('Vary', 'Origin');
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

class HttpError extends Error {
  constructor(readonly status: number, readonly code: string) {
    super(code);
  }
}
