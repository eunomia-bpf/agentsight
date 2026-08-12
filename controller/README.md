# AgentSight Controller

Controller is the fully open-source coordination service for AgentSight. It provides OAuth identity, Node ownership/discovery, and an online relay for Nodes that cannot be reached directly from the browser. The community/self-hosted build has the same Controller and relay capabilities as the hosted service; there is no code-level feature gate here.

Node telemetry remains authoritative on the Node. Controller does not persist snapshots, session transcripts, prompts, process data, or relay response bodies. Relay traffic passes through Controller runtime memory only while a request is active.

## Development

```bash
npm ci
npm test
npm run check
npx wrangler deploy --dry-run
```

## Deploy

After configuring the D1/OAuth bindings and Cloudflare credentials, update
`wrangler.jsonc` for the target account, D1 database, and hostname before
deploying. The checked-in account and custom domain are for the hosted
AgentSight deployment and are not defaults for third-party accounts.

```bash
npm run deploy
```

The deploy script first applies pending D1 migrations to the remote `DB` binding and then deploys the Worker. `wrangler.jsonc` provisions the SQLite-backed `NodeRelay` Durable Object used by each Node's outbound WebSocket.

The hosted deployment uses `https://control.agentsight.us`. Keep that custom
domain on the `agentsight-control` Worker so the browser and CLI do not depend
on an account-specific `workers.dev` hostname. The OAuth applications for that
deployment must allow these callback URLs:

- `https://control.agentsight.us/v1/auth/callback/github`
- `https://control.agentsight.us/v1/auth/callback/google`

The old `control-plane` path is retained only as a compatibility symlink for existing scripts; new code and documentation should use `controller`.
