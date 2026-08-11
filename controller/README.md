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

After configuring the existing D1/OAuth bindings and Cloudflare credentials:

```bash
npm run deploy
```

The deploy script first applies pending D1 migrations to the remote `DB` binding and then deploys the Worker. `wrangler.jsonc` provisions the SQLite-backed `NodeRelay` Durable Object used by each Node's outbound WebSocket.

The old `control-plane` path is retained only as a compatibility symlink for existing scripts; new code and documentation should use `controller`.
