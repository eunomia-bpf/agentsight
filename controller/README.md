# AgentSight Controller

Controller is the fully open-source coordination service for AgentSight. It provides OAuth identity, Node ownership/discovery, and an online relay for Nodes that cannot be reached directly from the browser. The community/self-hosted build has the same Controller and relay capabilities as the hosted service; there is no code-level feature gate here.

Node telemetry remains authoritative on the Node. Controller does not persist snapshots, session transcripts, prompts, process data, or relay response bodies. Relay traffic passes through Controller runtime memory only while a request is active.

Signed-in users may opt to sync a small Direct connection configuration so another browser can reconnect without repeating `agentsight bind`. The endpoint and access key are encrypted together with AES-GCM before D1 storage. A per-user/per-Node key is derived from the `DIRECT_CONFIG_KEY` Worker secret; Node lists expose only whether a saved configuration exists. The Controller can decrypt an owner's configuration at runtime, so this protects a D1-only disclosure but is not end-to-end encryption against a compromised Worker.

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

Create the Direct configuration encryption secret once for each deployment:

```bash
openssl rand -base64 32 | npx wrangler secret put DIRECT_CONFIG_KEY
```

Keep this secret stable across deployments. Rotating it requires re-saving existing Direct configurations.

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
