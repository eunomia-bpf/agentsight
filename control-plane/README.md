# AgentSight Control Plane

This Cloudflare Worker is the optional coordination plane for the hosted
AgentSight app. It stores users, OAuth identities, short-lived authorization
codes, sessions, and allowlisted Node metadata in D1. It does not ingest or
store AgentSight snapshots, prompts, process details, or other Node data.

The deployed API is `https://agentsight-control.yusen356.workers.dev`.

## Authentication

GitHub and Google use OAuth authorization-code callbacks. The callback creates
a single-use, two-minute application code and returns it in the
`app.agentsight.us` URL fragment. The SPA exchanges that code for a session;
provider access tokens and long-lived AgentSight sessions never appear in the
URL.

Configure these Worker secrets outside the repository:

```text
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

Provider callback URLs:

```text
https://agentsight-control.yusen356.workers.dev/v1/auth/callback/github
https://agentsight-control.yusen356.workers.dev/v1/auth/callback/google
```

## Deploy

```bash
cd control-plane
npm ci
npm run check
npx wrangler d1 execute agentsight-control --remote --file schema.sql
npx wrangler deploy
```

The schema is additive and safe to reapply. `wrangler.jsonc` contains the
public D1 database identifier; OAuth secrets remain in Cloudflare.

Workers and D1 both have free tiers suitable for an initial private beta. See
the current [Cloudflare Workers and D1 pricing](https://developers.cloudflare.com/workers/platform/pricing/)
before enabling paid capacity or adding a relay.
