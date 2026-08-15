# AgentSight analysis extension

This extension contains the existing post-capture AgentSight pipeline: protocol analyzers, materialized views, agent/session correlation, SQLite/OTel sinks, and local-session projection.

The native `agentsight-capture` crate owns only the stable capture boundary (`Event`, `EventStream`, `Runner`, `Analyzer`) and platform collectors. Analysis code lives here so it can be composed and migrated to WebAssembly Components without changing eBPF or `/proc` capture.
