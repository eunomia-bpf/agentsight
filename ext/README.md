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

- `session`: portable transcript discovery/parsing, session IR, and host-fed
  process correlation; exports a `wasm32-wasip2` Component Model parser entrypoint.
- `analysis`: adapts native capture facts to session semantics, then owns
  materialized views, storage, and sinks.
- `pprof`: semantic agent profiling.
- `vis`: repository-evolution visualization.
- `web`: built-in product presentation components; the trusted frontend shell
  remains in `frontend/`.
- `runtime`: bounded Wasmtime host for Component extensions.

The native `agentsight-capture-core` owns generic process identity and topology
and does not depend on agent/session semantics. Only `session` currently exports
and executes a WebAssembly Component. Analysis, pprof, vis, and web are native or
build-time product boundaries today; runtime discovery, extension-defined CLI
commands, and opaque Controller-to-Node extension routing remain follow-up work.
Published crate and binary names stay stable, while repository source paths under
`ext/` are the canonical cross-platform paths.
