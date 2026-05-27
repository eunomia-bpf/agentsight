// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::analyzers::{Analyzer, AnalyzerError};
use crate::framework::runners::EventStream;
use crate::framework::storage::sqlite::{GenericProjector, SqliteStore};
use async_trait::async_trait;
use futures::stream::StreamExt;
use std::path::Path;
use std::sync::{Arc, Mutex};

pub struct StorageAnalyzer {
    store: Arc<Mutex<SqliteStore>>,
    projector: Arc<Mutex<GenericProjector>>,
}

impl StorageAnalyzer {
    pub fn new(path: impl AsRef<Path>) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        Ok(Self {
            store: Arc::new(Mutex::new(SqliteStore::open(path)?)),
            projector: Arc::new(Mutex::new(GenericProjector::new())),
        })
    }
}

#[async_trait]
impl Analyzer for StorageAnalyzer {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let store = Arc::clone(&self.store);
        let projector = Arc::clone(&self.projector);

        let processed = stream.map(move |event| {
            if let (Ok(mut store), Ok(mut projector)) = (store.lock(), projector.lock())
                && let Err(e) = store.insert_event(&event, &mut projector)
            {
                log::warn!("StorageAnalyzer: failed to store event: {}", e);
            }
            event
        });

        Ok(Box::pin(processed))
    }

    fn name(&self) -> &str {
        "StorageAnalyzer"
    }
}
