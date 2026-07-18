use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(&manifest_dir);
    let sync_vendor = env_flag("AGENTSIGHT_SYNC_VENDOR");

    sync_bpf(&manifest_dir, repo_root, sync_vendor);
    sync_frontend(&manifest_dir, repo_root, sync_vendor);

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=AGENTSIGHT_SYNC_VENDOR");
}

fn env_flag(name: &str) -> bool {
    env::var(name)
        .map(|value| matches!(value.as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

fn sync_bpf(manifest_dir: &Path, repo_root: &Path, sync_vendor: bool) {
    let source_dir = repo_root.join("bpf");
    let vendor_dir = manifest_dir.join("vendor/bpf");
    for name in ["process", "sslsniff", "stdiocap"] {
        let source = source_dir.join(name);
        let vendor = vendor_dir.join(name);
        if sync_vendor {
            if !source.exists() {
                panic!(
                    "missing BPF loader {}. Run `make -C ../bpf` before packaging.",
                    source.display()
                );
            }
            println!("cargo:rerun-if-changed={}", source.display());
            copy_file(&source, &vendor).unwrap_or_else(|err| {
                panic!(
                    "failed to vendor {} into {}: {err}",
                    source.display(),
                    vendor.display()
                )
            });
        }
        if !vendor.exists() {
            panic!(
                "missing bundled BPF loader {}. Run `make build` before packaging.",
                vendor.display()
            );
        }
        println!("cargo:rerun-if-changed={}", vendor.display());
    }
}

fn sync_frontend(manifest_dir: &Path, repo_root: &Path, sync_vendor: bool) {
    let source_dir = repo_root.join("frontend/dist");
    let vendor_dir = manifest_dir.join("vendor/frontend/dist");
    if sync_vendor {
        if !source_dir.join("index.html").exists() {
            panic!(
                "missing frontend build {}. Run `npm run build` in ../frontend before packaging.",
                source_dir.display()
            );
        }
        println!("cargo:rerun-if-changed={}", source_dir.display());
        if vendor_dir.exists() {
            fs::remove_dir_all(&vendor_dir)
                .unwrap_or_else(|err| panic!("failed to clear {}: {err}", vendor_dir.display()));
        }
        copy_dir(&source_dir, &vendor_dir).unwrap_or_else(|err| {
            panic!(
                "failed to vendor frontend {} into {}: {err}",
                source_dir.display(),
                vendor_dir.display()
            )
        });
    }
    if !vendor_dir.join("index.html").exists() {
        panic!(
            "missing bundled frontend {}. Run `make build` before packaging.",
            vendor_dir.display()
        );
    }
    println!("cargo:rerun-if-changed={}", vendor_dir.display());
}

fn copy_file(source: &Path, destination: &Path) -> io::Result<()> {
    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::copy(source, destination)?;
    Ok(())
}

fn copy_dir(source: &Path, destination: &Path) -> io::Result<()> {
    fs::create_dir_all(destination)?;
    for entry in fs::read_dir(source)? {
        let entry = entry?;
        let source_path = entry.path();
        let destination_path = destination.join(entry.file_name());
        if source_path.is_dir() {
            copy_dir(&source_path, &destination_path)?;
        } else if source_path
            .file_name()
            .is_some_and(|name| name == "sample-trace.log")
        {
            continue;
        } else {
            copy_file(&source_path, &destination_path)?;
        }
    }
    Ok(())
}
