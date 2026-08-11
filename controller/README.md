# AgentSight Controller

Controller is the open-source hosted coordination service for AgentSight. It provides OAuth identity, Node ownership/discovery, and an online relay for Nodes that cannot be reached directly from the browser.

Node telemetry remains authoritative on the Node. Controller does not persist snapshots, session transcripts, prompts, process data, or relay response bodies. Relay traffic passes through Controller runtime memory only while a request is active.

## Development

```bash
npm ci
npm test
npm run check
npx wrangler deploy --dry-run
```

Apply D1 migrations before deployment. `wrangler.jsonc` also provisions the `NodeRelay` Durable Object used by the outbound Node WebSocket.

The old `control-plane` path is retained only as a compatibility symlink for existing scripts; new code and documentation should use `controller`.
