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
  `wasm32-wasip2` Component Model entrypoint through WIT.
- `pprof`: semantic agent profiling.
- `vis`: repository-evolution visualization.
- `web`: built-in product presentation components; the trusted frontend shell
  remains in `frontend/`.
