// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::fs;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use tempfile::TempDir;
use tokio::time::{sleep, Duration};

const PROCESS_BINARY: &[u8] = include_bytes!("../../../bpf/process");
const SSLSNIFF_BINARY: &[u8] = include_bytes!("../../../bpf/sslsniff");
const STDIOCAP_BINARY: &[u8] = include_bytes!("../../../bpf/stdiocap");

pub struct BinaryExtractor {
    _temp_dir: TempDir, // Keep alive to prevent cleanup
    pub process_path: PathBuf,
    pub sslsniff_path: PathBuf,
    stdiocap_init_lock: Mutex<()>,
    stdiocap_path: OnceLock<PathBuf>,
}

impl BinaryExtractor {
    pub async fn new() -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        println!("Creating temporary directory...");
        
        let temp_dir = TempDir::new()?;
        let temp_path = temp_dir.path();
        
        println!("Created temporary directory: {}", temp_path.display());
        
        // Extract and setup the process binary
        let process_path = temp_path.join("process");
        Self::extract_binary(&process_path, PROCESS_BINARY, "process").await?;
        
        // Extract and setup the sslsniff binary
        let sslsniff_path = temp_path.join("sslsniff");
        Self::extract_binary(&sslsniff_path, SSLSNIFF_BINARY, "sslsniff").await?;

        // Small delay to ensure files are fully written
        sleep(Duration::from_millis(100)).await;
        
        Ok(Self {
            _temp_dir: temp_dir,
            process_path,
            sslsniff_path,
            stdiocap_init_lock: Mutex::new(()),
            stdiocap_path: OnceLock::new(),
        })
    }
    
    async fn extract_binary(
        path: &Path,
        binary_data: &[u8],
        name: &str,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        {
            let mut file = fs::File::create(path)?;
            file.write_all(binary_data)?;
            file.flush()?;
        } // File is closed here
        
        // Make the binary executable
        let mut perms = fs::metadata(path)?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(path, perms)?;
        
        println!("Extracted {} binary to: {}", name, path.display());
        
        Ok(())
    }
    
    pub fn get_process_path(&self) -> &Path {
        &self.process_path
    }
    
    pub fn get_sslsniff_path(&self) -> &Path {
        &self.sslsniff_path
    }

    pub fn get_stdiocap_path(&self) -> Result<&Path, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(path) = self.stdiocap_path.get() {
            return Ok(path.as_path());
        }

        let _guard = self.stdiocap_init_lock.lock().map_err(|_| {
            std::io::Error::new(
                std::io::ErrorKind::Other,
                "stdiocap extraction lock poisoned",
            )
        })?;

        if let Some(path) = self.stdiocap_path.get() {
            return Ok(path.as_path());
        }

        let stdiocap_path = self._temp_dir.path().join("stdiocap");
        {
            let mut file = fs::File::create(&stdiocap_path)?;
            file.write_all(STDIOCAP_BINARY)?;
            file.flush()?;
        }

        let mut perms = fs::metadata(&stdiocap_path)?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&stdiocap_path, perms)?;
        println!("Extracted stdiocap binary to: {}", stdiocap_path.display());

        self.stdiocap_path.set(stdiocap_path).map_err(|_| {
            std::io::Error::new(
                std::io::ErrorKind::Other,
                "stdiocap path initialized concurrently",
            )
        })?;

        Ok(self
            .stdiocap_path
            .get()
            .expect("stdiocap path should be initialized")
            .as_path())
    }
}
