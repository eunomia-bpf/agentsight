# AgentSight Control Plane

This Cloudflare Worker is the optional coordination plane for the hosted
AgentSight app. It stores users, OAuth identities, short-lived authorization
codes, sessions, and allowlisted Node metadata in D1. It does not ingest or
store AgentSight snapshots, prompts, process details, or other Node data.

The SPA itself is published by this repository's GitHub Pages workflow at
`https://app.agentsight.us`; it is not served by this Worker.

The deployed API is `https://agentsight-control.yusen356.workers.dev`.
Both sides remain configurable for self-hosting: build the SPA with
`NEXT_PUBLIC_CONTROL_PLANE_URL` pointing at your Worker, and set that Worker's
`APP_ORIGIN` variable to the SPA origin. `agentsight bind --app-url` selects the
same presentation origin for a Node connection.

## Authentication

GitHub and Google use OAuth authorization-code callbacks. The callback creates
a single-use, two-minute application code and returns it in the
`app.agentsight.us` URL fragment. The SPA exchanges that code for a session;
provider access tokens and long-lived AgentSight sessions never appear in the
URL. A per-tab PKCE verifier binds the application code to the browser that
started sign-in. Workers Rate Limiting bindings apply per-client and
per-Cloudflare-location caps to anonymous OAuth starts, and expired
OAuth/session rows are cleaned before new state is written.

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
npm test
npm run check
npx wrangler d1 migrations apply agentsight-control --remote
npx wrangler deploy
```

The tracked files in `migrations/` initialize a new database and upgrade an
existing one before the Worker starts using the new schema. `schema.sql` is the
current consolidated schema for reference. `wrangler.jsonc` contains the public
D1 database identifier and rate limiting configuration; OAuth secrets remain
in Cloudflare.

Workers and D1 both have free tiers suitable for an initial private beta. See
the current [Cloudflare Workers and D1 pricing](https://developers.cloudflare.com/workers/platform/pricing/)
before enabling paid capacity or adding a relay.
