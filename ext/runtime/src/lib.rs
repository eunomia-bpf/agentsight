// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::Deserialize;
use wasmtime::component::{Component, Linker, ResourceTable};
use wasmtime::{Config, Engine, Store, StoreLimits, StoreLimitsBuilder};
use wasmtime_wasi::{WasiCtx, WasiCtxView, WasiView};

pub const PROTOCOL_VERSION: u32 = 1;
pub const PRODUCT: &str = "agentsight";

#[derive(Debug, Deserialize)]
pub struct SessionMessageRequest {
    pub message: String,
}

impl SessionMessageRequest {
    pub fn validate(self) -> Result<String, &'static str> {
        let message = self.message.trim();
        if message.is_empty() {
            return Err("message_required");
        }
        if message.len() > 16 * 1024 {
            return Err("message_too_large");
        }
        Ok(message.to_string())
    }
}

pub fn session_detail_id(path: &str) -> Option<&str> {
    let value = path.strip_prefix("/api/v1/sessions/")?;
    (!value.is_empty() && !value.ends_with("/messages") && !value.contains('/')).then_some(value)
}

pub fn session_message_id(path: &str) -> Option<&str> {
    let value = path.strip_prefix("/api/v1/sessions/")?.strip_suffix("/messages")?;
    (!value.is_empty() && !value.contains('/')).then_some(value)
}

const DEFAULT_MEMORY_BYTES: usize = 16 * 1024 * 1024;
const DEFAULT_FUEL: u64 = 10_000_000;
const MAX_CORE_INSTANCES: usize = 16;
const MAX_MEMORIES: usize = 4;
const MAX_TABLES: usize = 8;

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
pub struct ExtRuntime {
    engine: Engine,
}

impl ExtRuntime {
    pub fn new() -> Result<Self, wasmtime::Error> {
        let mut config = Config::new();
        config.consume_fuel(true);
        Ok(Self { engine: Engine::new(&config)? })
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
        let component = Component::from_binary(&self.engine, component_bytes)?;
        let mut linker = Linker::<ExtStore>::new(&self.engine);
        wasmtime_wasi::p2::add_to_linker_sync(&mut linker)?;
        let mut store = self.store()?;
        let instance = linker.instantiate(&mut store, &component)?;
        let parse = instance.get_typed_func::<(String, String, u64, String), (Option<String>,)>(
            &mut store,
            "parse",
        )?;
        Ok(parse.call(
            &mut store,
            (agent.to_owned(), path.to_owned(), updated_ms, content.to_owned()),
        )?.0)
    }
}
