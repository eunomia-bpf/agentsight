use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(&manifest_dir);
    let source_dir = repo_root.join("bpf");
    let vendor_dir = manifest_dir.join("vendor/bpf");

    for name in ["process", "sslsniff", "stdiocap"] {
        let source = source_dir.join(name);
        let vendor = vendor_dir.join(name);
        if env_flag("AGENTSIGHT_SYNC_VENDOR") {
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

    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=AGENTSIGHT_SYNC_VENDOR");
}

fn env_flag(name: &str) -> bool {
    env::var(name)
        .map(|value| matches!(value.as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

fn copy_file(source: &Path, destination: &Path) -> io::Result<()> {
    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::copy(source, destination)?;
    Ok(())
}
