# AgentSight extensions

`ext/` contains product functionality that is independently composable from the
native capture substrate. An extension may contain Rust compiled as a WebAssembly
Component, frontend components, command entrypoints, or several cooperating
components.

The native host keeps platform capture (eBPF, `/proc`, SSL/stdio/system runners),
identity/capability enforcement, transport, and component execution. Existing
feature boundaries are preserved rather than replaced with a new query or event
abstraction.

Current extensions:

- `session`: portable agent-session parsing and correlation; exports a
  `wasm32-wasip2` Component Model entrypoint for one host-supplied transcript
  through WIT. Native discovery retains filesystem and Cursor subagent
  aggregation responsibilities.
- `pprof`: semantic agent profiling.
- `vis`: repository-evolution visualization.
- `web`: built-in product presentation components; the trusted frontend shell
  remains in `frontend/`.

Only `session` currently exports and executes a WebAssembly Component. The
analysis, pprof, vis, and web directories establish native or build-time product
boundaries; runtime discovery, extension-defined CLI commands, and opaque
Controller-to-Node extension routing remain follow-up work. Published crate and
binary names stay stable, while repository source paths under `ext/` are the
canonical cross-platform paths (root symlink aliases are intentionally avoided).
