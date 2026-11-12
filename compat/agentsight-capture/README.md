# agentsight-capture

`agentsight-capture` preserves the public capture-and-analysis API used by
existing integrations. The implementation is split into the native
`agentsight-capture-core` substrate and the composable `agentsight-analysis`
extension; this crate re-exports that combined API without copying it.

New capture-only integrations may depend directly on
`agentsight-capture-core`. Existing `agentsight_capture` imports continue to
work unchanged.
