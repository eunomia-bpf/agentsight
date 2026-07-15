# AgentSight npm package

AgentSight publishes `@eunomia-bpf/agentsight` as the official npm entrypoint
for the Web viewer and command dispatcher.

The npm `agentsight` command has two responsibilities:

- `agentsight web`, `agentsight serve`, and `agentsight open` serve the bundled
  Web UI for exported snapshots.
- `agentsight record`, `agentsight top`, `agentsight monitor`,
  `agentsight stat`, and `agentsight report` delegate to a real Rust AgentSight
  collector binary when one is available.

The npm package does not run privileged commands, download hidden binaries, or
execute a `postinstall` installer.

## Build locally

```bash
npm ci --prefix frontend
node frontend/scripts/prepare-sample.mjs
npm run build --prefix frontend
node script/npm/sync-version.mjs
node script/npm/prepare-agentsight.mjs
```

## Validate locally

```bash
cd package/npm/agentsight
npm test
npm pack --dry-run
```

## Publish

Publishing is handled by `.github/workflows/npm-publish.yml` on
`workflow_dispatch`, GitHub Release publish, or `v*` tag push. The workflow uses
npm Trusted Publishing with GitHub Actions OIDC and skips versions that already
exist.

Configure npm Trusted Publishing for:

- Package: `@eunomia-bpf/agentsight`
- Publisher: GitHub Actions
- GitHub organization/user: `eunomia-bpf`
- Repository: `agentsight`
- Workflow filename: `npm-publish.yml`
- Allowed action: `npm publish`

Manual local publishing is equivalent to:

```bash
cd package/npm/agentsight
npm publish --access public
```
