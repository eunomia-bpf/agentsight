// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use rust_embed::RustEmbed;
use std::borrow::Cow;
use std::path::{Path, PathBuf};
use std::fs;
use mime_guess::from_path;

#[derive(RustEmbed)]
#[folder = "../frontend/dist/"]
pub struct FrontendDist;

pub struct FrontendAssets {
    serve_dir: PathBuf,
    /// Whether we own the directory (temp extraction) and should clean it up on drop.
    owned: bool,
}

impl FrontendAssets {
    pub fn new() -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        // Dev mode: serve directly from a disk directory if env var is set
        if let Ok(dist_path) = std::env::var("AGENTSIGHT_FRONTEND_DIST") {
            let dir = PathBuf::from(&dist_path);
            if !dir.join("index.html").exists() {
                return Err(format!(
                    "AGENTSIGHT_FRONTEND_DIST={} does not contain index.html",
                    dist_path
                ).into());
            }
            log::info!("📁 Dev mode: serving frontend from disk: {}", dir.display());
            return Ok(Self { serve_dir: dir, owned: false });
        }

        let temp_dir = std::env::temp_dir().join(format!("agentsight-frontend-{}", uuid::Uuid::new_v4()));
        fs::create_dir_all(&temp_dir)?;

        // Extract all embedded assets to temp directory
        for file_path in FrontendDist::iter() {
            if let Some(content) = FrontendDist::get(&file_path) {
                let full_path = temp_dir.join(&*file_path);
                if let Some(parent) = full_path.parent() {
                    fs::create_dir_all(parent)?;
                }
                fs::write(&full_path, &content.data)?;
            }
        }

        log::info!("📁 Extracted frontend assets to: {}", temp_dir.display());
        Ok(Self { serve_dir: temp_dir, owned: true })
    }
    
    /// Get any asset by path from the serve directory
    pub fn get(&self, path: &str) -> Option<Cow<'static, [u8]>> {
        // Handle root path
        let file_path = if path == "/" || path == "/index.html" {
            self.serve_dir.join("index.html")
        } else {
            // Remove leading slash for file lookup
            let normalized_path = path.strip_prefix('/').unwrap_or(path);
            self.serve_dir.join(normalized_path)
        };
        
        // Try to read from serve directory
        if let Ok(content) = fs::read(&file_path) {
            Some(Cow::Owned(content))
        } else {
            None
        }
    }
    
    
    /// Get MIME type for a file path
    pub fn get_content_type(&self, path: &str) -> String {
        // Handle root path - should serve as HTML
        let file_path = if path == "/" || path == "/index.html" {
            "index.html"
        } else {
            // Remove leading slash for proper MIME detection
            path.strip_prefix('/').unwrap_or(path)
        };
        
        from_path(file_path).first_or_octet_stream().to_string()
    }
    
    /// List all available assets
    pub fn list_all_assets(&self) -> Vec<String> {
        if self.owned {
            // Embedded mode: use RustEmbed iterator
            FrontendDist::iter().map(|s| s.to_string()).collect()
        } else {
            // Dev mode: walk the disk directory
            let mut files = Vec::new();
            if let Ok(entries) = walkdir(&self.serve_dir, &self.serve_dir) {
                files = entries;
            }
            files
        }
    }
}

impl Drop for FrontendAssets {
    fn drop(&mut self) {
        if !self.owned {
            return;
        }
        if self.serve_dir.exists() {
            if let Err(e) = fs::remove_dir_all(&self.serve_dir) {
                log::warn!("Failed to cleanup temp directory {}: {}", self.serve_dir.display(), e);
            } else {
                log::info!("🧹 Cleaned up temp directory: {}", self.serve_dir.display());
            }
        }
    }
}

/// Recursively list files under `dir`, returning paths relative to `root`.
fn walkdir(dir: &Path, root: &Path) -> std::io::Result<Vec<String>> {
    let mut result = Vec::new();
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            result.extend(walkdir(&path, root)?);
        } else if let Ok(rel) = path.strip_prefix(root) {
            result.push(rel.to_string_lossy().into_owned());
        }
    }
    Ok(result)
}