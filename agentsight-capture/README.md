# agentsight-capture

`agentsight-capture` is the reusable collection and analysis library behind the
[`agentsight`](https://crates.io/crates/agentsight) command-line tool. It
provides the embedded eBPF probe runners, agent-native and `/proc` sources,
HTTP/SSE analyzers, normalized event and snapshot models, and SQLite and
OpenTelemetry sinks.

The eBPF runners are Linux-only at runtime and require root or suitable BPF
capabilities. AgentSight keeps the probes in isolated child processes; linking
this crate does not link libbpf into the caller.

```rust,no_run
use agentsight_capture::{
    BinaryExtractor,
    runners::{AgentRunner, BinaryRunner, Runner},
};

# async fn example() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
let probes = BinaryExtractor::new().await?;
let ssl = BinaryRunner::ssl(probes.get_sslsniff_path())
    .with_args(["--pid", "1234"]);
let mut capture = AgentRunner::new().add_runner(Box::new(ssl));
let _events = capture.run().await?;
# Ok(())
# }
```

The `agentsight` binary is the primary consumer of this API. It adds command
parsing, terminal and web views, session orchestration, and reports.
