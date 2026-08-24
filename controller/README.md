# AgentSight Controller

Controller is the fully open-source coordination service for AgentSight. It is deliberately not AgentSight's telemetry data plane.

Controller stores and coordinates:

- GitHub/Google OAuth identity;
- organizations and user memberships;
- built-in roles and organization configuration;
- plan, billing-provider metadata, and entitlements;
- Node registration, relay credentials, presence, and optional encrypted Direct connection configs;
- the authorization decision used before Controller relays a Node operation.

Detailed runtime evidence remains authoritative on the Node. Controller does not persist snapshots, session transcripts, prompts, process data, or relay response bodies. Relay traffic passes through Controller runtime memory only while a request is active.

By default, Direct configuration stays only in the current browser. A signed-in user may explicitly opt in to save a compact Direct endpoint and bootstrap key for another browser. Controller encrypts that value with AES-256-GCM using a per-user/per-Node key derived from `DIRECT_CONFIG_KEY`; D1 never stores the plaintext. The account copy can be removed independently of the local browser capability.

## Authorization model

Human login and Node authorization are separate concerns.

```text
OAuth user
  -> organization membership
  -> viewer / operator / admin / owner
  -> semantic action
  -> Direct or Controller relay
  -> Node capability enforcement
```

A Node never needs a user, owner, membership, role, or billing record. Its persistent local credential is a bootstrap/relay identity. Normal Node Protocol operations use Node-local scoped capabilities such as `evidence.read`, `session.read`, and `session.message`.

Controller's Node registry is organization-scoped rather than user-owned. A user may belong to multiple organizations. Every account has a personal organization; team organizations use the same data model.

Built-in roles intentionally remain small:

- `viewer`: inspect organization metadata, Nodes, evidence, sessions, config, and billing state;
- `operator`: viewer plus `session.message`;
- `admin`: operator plus Node/member/config management;
- `owner`: admin plus organization and billing management.

## Plans

The Controller exposes the canonical future billing catalog at `GET /v1/pricing`:

- Free: $0; local/direct open-source use;
- Pro: $5/month or $49/year; managed connectivity for a personal organization;
- Team: $10/user/month; shared organization/fleet and team roles;
- Enterprise: custom.

During the current hosted preview, every registered user receives `effectivePlan: "unlimited"`. The switch is `HOSTED_PREVIEW_UNLIMITED` in `src/access.ts`; it bypasses managed-connectivity and multi-member plan gates without rewriting the organization's persisted billing plan or billing status. This keeps future Free/Pro/Team/Enterprise billing data independent from today's preview access.

A `pro_lifetime` entitlement remains the durable contributor benefit after preview billing is enabled; it applies to personal Pro and does not waive Team or Enterprise billing.

## Organization API

```text
GET/POST          /v1/organizations
PATCH/DELETE      /v1/organizations/{organization_id}
GET/POST          /v1/organizations/{organization_id}/members
PATCH/DELETE      /v1/organizations/{organization_id}/members/{user_id}
GET/PUT           /v1/organizations/{organization_id}/config/{key}
GET               /v1/organizations/{organization_id}/billing
POST              /v1/invitations/accept
GET/POST          /v1/nodes?organization_id=...
DELETE            /v1/nodes/{node_id}
GET/DELETE        /v1/nodes/{node_id}/direct
POST              /v1/nodes/{node_id}/capabilities
```

Privileged deployment automation may use `ADMIN_API_TOKEN` for provider-neutral billing state and contributor entitlement updates. Do not expose that token to browsers.

## Development

```bash
npm ci
npm test
npm run check
cd ..
./controller/node_modules/.bin/wrangler deploy --dry-run --config wrangler.jsonc
```

## Deployment

Hosted deployment is automatic through Cloudflare Workers Builds. The repository is connected directly to the `agentsight` Worker; no Cloudflare API token is stored in GitHub.

The OAuth runtime bindings such as `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are only used when a person chooses **Sign in with GitHub**. Configure the client ID as a Worker variable or secret and the client secret as a Worker secret. They are not Git repository credentials, Cloudflare deployment credentials, or GitHub Actions secrets. Both Wrangler configs set `keep_vars` so an automatic code deployment preserves these Dashboard-managed bindings.

One Worker deployment contains both surfaces from the same repository revision:

- `app.agentsight.us` serves the frontend and static assets;
- `control.agentsight.us` serves the Controller API and relay;
- one D1 database stores Controller metadata;
- one Durable Object namespace carries live relay traffic.

Cloudflare Builds uses two Worker connections to the same repository. This is required because a Git-connected build always deploys the Worker it is connected to, even when a Wrangler environment specifies another name. Both connections use `/` as the root directory and `master` as the production branch.

The production `agentsight` connection disables builds for non-production branches and uses `wrangler.jsonc`:

Production deploy command:

```bash
npm --prefix controller ci && ./controller/node_modules/.bin/wrangler deploy --config wrangler.jsonc
```

The isolated `agentsight-preview` connection enables builds for non-production branches. Both its deploy and version commands use `wrangler.preview.jsonc`:

```bash
npm --prefix controller ci && ./controller/node_modules/.bin/wrangler d1 migrations apply DB --remote --config wrangler.preview.jsonc && ./controller/node_modules/.bin/wrangler deploy --config wrangler.preview.jsonc
```

Cloudflare does not generate native version preview URLs for Workers that implement Durable Objects. Non-production builds therefore perform a full deploy to the stable, isolated `agentsight-preview` Worker. That staging Worker has its own workers.dev URL, D1 database, Durable Object namespace, rate-limit namespaces, and Build connection; it never receives production secrets or production data. Each new non-production build replaces the previous staging revision.

Production code deployment never applies D1 migrations implicitly. An operator must review and run `npm --prefix controller run migrate:remote` as a separate, explicit maintenance action before deploying a revision that genuinely requires a schema change. This keeps ordinary automatic frontend/API deployments database-compatible and prevents a code merge from mutating production data. Staging remains isolated and may apply its own preview-database migrations before deployment. `npm run deploy` remains available for production recovery/debugging, but it deploys code only and is not the normal production path.

The old `control-plane` path is retained only as a compatibility symlink for existing scripts; new code and documentation should use `controller`.
