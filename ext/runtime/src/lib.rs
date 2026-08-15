// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use wasmtime::component::{Component, Linker};
use wasmtime::{Config, Engine, Store, StoreLimits, StoreLimitsBuilder};

const DEFAULT_MEMORY_BYTES: usize = 16 * 1024 * 1024;
const DEFAULT_FUEL: u64 = 10_000_000;

struct ExtStore {
    limits: StoreLimits,
}

/// Bounded in-process host for capability-free WebAssembly Components.
///
/// The linker starts empty: filesystem, network, process, and AgentSight
/// authority only exist when a caller explicitly wires a capability-bearing
/// component interface.
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
        let mut store = Store::new(
            &self.engine,
            ExtStore {
                limits: StoreLimitsBuilder::new()
                    .memory_size(DEFAULT_MEMORY_BYTES)
                    .instances(1)
                    .memories(2)
                    .tables(4)
                    .build(),
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
        let linker = Linker::<ExtStore>::new(&self.engine);
        let mut store = self.store()?;
        let instance = linker.instantiate(&mut store, &component)?;
        let parse = instance.get_typed_func::<
            (String, String, u64, String),
            (Option<String>,),
        >(&mut store, "parse")?;
        Ok(parse.call(
            &mut store,
            (agent.to_owned(), path.to_owned(), updated_ms, content.to_owned()),
        )?.0)
    }
}
