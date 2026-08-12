# AgentSight Controller

Controller is the fully open-source coordination service for AgentSight. It is deliberately not AgentSight's telemetry data plane.

Controller stores and coordinates:

- GitHub/Google OAuth identity;
- organizations and user memberships;
- built-in roles and organization configuration;
- plan, billing-provider metadata, and entitlements;
- Node registration, relay credentials, and presence;
- the authorization decision used before Controller relays a Node operation.

Detailed runtime evidence remains authoritative on the Node. Controller does not persist snapshots, session transcripts, prompts, process data, or relay response bodies. Relay traffic passes through Controller runtime memory only while a request is active.

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

The Controller exposes the canonical catalog at `GET /v1/pricing`:

- Free: $0; local/direct open-source use;
- Pro: $5/month or $49/year; managed connectivity for a personal organization;
- Team: $10/user/month; shared organization/fleet and team roles;
- Enterprise: custom.

A `pro_lifetime` entitlement gives a contributor's personal organization effective Pro access without changing Team or Enterprise billing. The admin adapter can record provider-neutral billing state and contributor entitlements; payment-provider checkout/webhook code is intentionally kept outside the authorization model.

Plan enforcement happens at the Controller boundary: Free remains usable locally/directly, Pro enables managed registration/relay for a personal organization, and Team/Enterprise enable multi-member organization operations.

## Organization API

The main coordination surfaces are:

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
POST              /v1/nodes/{node_id}/capabilities
```

Privileged deployment automation may use `ADMIN_API_TOKEN` for provider-neutral billing state and contributor entitlement updates. Do not expose that token to browsers.

## Development

```bash
npm ci
npm test
npm run check
npx wrangler deploy --dry-run
```

## Deploy

After configuring the existing D1/OAuth bindings and Cloudflare credentials:

```bash
npm run deploy
```

The deploy script first applies pending D1 migrations to the remote `DB` binding and then deploys the Worker. `wrangler.jsonc` provisions the SQLite-backed `NodeRelay` Durable Object used by each Node's outbound WebSocket.

The old `control-plane` path is retained only as a compatibility symlink for existing scripts; new code and documentation should use `controller`.
