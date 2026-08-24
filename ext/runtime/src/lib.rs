// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use wasmtime::component::{Component, Linker, ResourceTable};
use wasmtime::{Config, Engine, Store, StoreLimits, StoreLimitsBuilder};
use wasmtime_wasi::{WasiCtx, WasiCtxView, WasiView};

const DEFAULT_MEMORY_BYTES: usize = 64 * 1024 * 1024;
const DEFAULT_FUEL: u64 = 10_000_000;
const MAX_CORE_INSTANCES: usize = 16;
const MAX_MEMORIES: usize = 4;
const MAX_TABLES: usize = 8;
const MAX_COMPONENT_BYTES: usize = 16 * 1024 * 1024;
const MAX_CONTENT_BYTES: usize = 16 * 1024 * 1024;
const MAX_METADATA_BYTES: usize = 64 * 1024;

struct ExtStore {
    limits: StoreLimits,
    table: ResourceTable,
    wasi: WasiCtx,
}

impl WasiView for ExtStore {
    fn ctx(&mut self) -> WasiCtxView<'_> {
        WasiCtxView {
            ctx: &mut self.wasi,
            table: &mut self.table,
        }
    }
}

/// Bounded in-process host for WebAssembly Components.
///
/// WASI P2 is linked for ABI compatibility, but the default context inherits
/// no arguments, environment, stdio, directories, or network access. TCP/UDP
/// are disabled outright. AgentSight-specific authority must be linked by an
/// explicit capability-bearing host interface.
///
/// Component compilation is only exposed for trusted components shipped with
/// AgentSight. This type is not an upload boundary for arbitrary user-supplied
/// Wasm. Execution and input sizes are bounded independently.
pub struct ExtRuntime {
    engine: Engine,
}

impl ExtRuntime {
    pub fn new() -> Result<Self, wasmtime::Error> {
        let mut config = Config::new();
        config.consume_fuel(true);
        Ok(Self {
            engine: Engine::new(&config)?,
        })
    }

    fn store(&self) -> Result<Store<ExtStore>, wasmtime::Error> {
        let mut wasi = WasiCtx::builder();
        wasi.allow_tcp(false).allow_udp(false);
        let mut store = Store::new(
            &self.engine,
            ExtStore {
                limits: StoreLimitsBuilder::new()
                    .memory_size(DEFAULT_MEMORY_BYTES)
                    .instances(MAX_CORE_INSTANCES)
                    .memories(MAX_MEMORIES)
                    .tables(MAX_TABLES)
                    .build(),
                table: ResourceTable::new(),
                wasi: wasi.build(),
            },
        );
        store.limiter(|state| &mut state.limits);
        store.set_fuel(DEFAULT_FUEL)?;
        Ok(store)
    }

    pub fn session_parse(
        &self,
        component_bytes: &[u8],
        agent: &str,
        path: &str,
        updated_ms: u64,
        content: &str,
    ) -> Result<Option<String>, wasmtime::Error> {
        validate_session_input(component_bytes, agent, path, content)?;
        let component = Component::from_binary(&self.engine, component_bytes)?;
        let mut linker = Linker::<ExtStore>::new(&self.engine);
        wasmtime_wasi::p2::add_to_linker_sync(&mut linker)?;
        let mut store = self.store()?;
        let instance = linker.instantiate(&mut store, &component)?;
        let parse = instance.get_typed_func::<(String, String, u64, String), (Option<String>,)>(
            &mut store, "parse",
        )?;
        Ok(parse
            .call(
                &mut store,
                (
                    agent.to_owned(),
                    path.to_owned(),
                    updated_ms,
                    content.to_owned(),
                ),
            )?
            .0)
    }
}

fn validate_session_input(
    component_bytes: &[u8],
    agent: &str,
    path: &str,
    content: &str,
) -> Result<(), wasmtime::Error> {
    if component_bytes.len() > MAX_COMPONENT_BYTES {
        return Err(wasmtime::Error::msg("extension component exceeds 16 MiB"));
    }
    if content.len() > MAX_CONTENT_BYTES {
        return Err(wasmtime::Error::msg("session content exceeds 16 MiB"));
    }
    if agent.len().saturating_add(path.len()) > MAX_METADATA_BYTES {
        return Err(wasmtime::Error::msg("session metadata exceeds 64 KiB"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_oversized_component_content_and_metadata() {
        assert!(
            validate_session_input(&vec![0; MAX_COMPONENT_BYTES + 1], "codex", "x", "x").is_err()
        );
        assert!(
            validate_session_input(&[], "codex", "x", &"x".repeat(MAX_CONTENT_BYTES + 1)).is_err()
        );
        assert!(validate_session_input(&[], &"a".repeat(MAX_METADATA_BYTES), "x", "x").is_err());
    }
}
