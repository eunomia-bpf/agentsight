//! TCP port detection for a given PID via /proc filesystem
//!
//! Discovers which TCP ports a process is listening on by:
//! 1. Enumerating socket inodes from `/proc/[pid]/fd/`
//! 2. Matching them against `/proc/net/tcp` and `/proc/net/tcp6` entries
//!    that are in the LISTEN state.

use std::collections::HashSet;
use std::fs;
use std::path::Path;

/// Detect all TCP ports on which the given PID is listening.
///
/// Returns an empty `Vec` if the process has no listening sockets or if
/// we cannot read the required `/proc` entries (e.g. process exited).
pub fn detect_listening_ports(pid: u32) -> Vec<u16> {
    let socket_inodes = match collect_socket_inodes(pid) {
        Ok(inodes) => inodes,
        Err(_) => return Vec::new(),
    };

    if socket_inodes.is_empty() {
        return Vec::new();
    }

    let mut ports = Vec::new();

    // Check both IPv4 and IPv6 TCP entries
    for tcp_path in &["/proc/net/tcp", "/proc/net/tcp6"] {
        if let Ok(entries) = parse_tcp_file(tcp_path) {
            for entry in entries {
                // st == 0x0A means TCP_LISTEN
                if entry.state == 0x0A && socket_inodes.contains(&entry.inode) {
                    ports.push(entry.local_port);
                }
            }
        }
    }

    ports.sort();
    ports.dedup();
    ports
}

/// Collect all socket inodes owned by the given PID by reading `/proc/[pid]/fd/`.
fn collect_socket_inodes(pid: u32) -> std::io::Result<HashSet<u64>> {
    let fd_dir = format!("/proc/{}/fd", pid);
    let mut inodes = HashSet::new();

    for entry in fs::read_dir(&fd_dir)? {
        let entry = entry?;
        let link = match fs::read_link(entry.path()) {
            Ok(l) => l,
            Err(_) => continue,
        };
        let link_str = link.to_string_lossy();
        // Socket symlinks look like "socket:[12345]"
        if let Some(inode_str) = link_str.strip_prefix("socket:[").and_then(|s| s.strip_suffix(']')) {
            if let Ok(inode) = inode_str.parse::<u64>() {
                inodes.insert(inode);
            }
        }
    }

    Ok(inodes)
}

/// A parsed entry from /proc/net/tcp{,6}
struct TcpEntry {
    local_port: u16,
    state: u8,
    inode: u64,
}

/// Parse a /proc/net/tcp or /proc/net/tcp6 file.
///
/// Each non-header line has the format:
///   sl  local_address  rem_address  st  ...  inode  ...
///
/// Fields are whitespace-separated. `local_address` is `HEX_IP:HEX_PORT`.
fn parse_tcp_file(path: &str) -> std::io::Result<Vec<TcpEntry>> {
    let content = fs::read_to_string(Path::new(path))?;
    let mut entries = Vec::new();

    for line in content.lines().skip(1) {
        // Skip the header line
        let fields: Vec<&str> = line.split_whitespace().collect();
        if fields.len() < 10 {
            continue;
        }

        // fields[1] = local_address (e.g. "0100007F:1CE4")
        let local_port = match parse_hex_port(fields[1]) {
            Some(p) => p,
            None => continue,
        };

        // fields[3] = st (TCP state in hex)
        let state = match u8::from_str_radix(fields[3], 16) {
            Ok(s) => s,
            Err(_) => continue,
        };

        // fields[9] = inode
        let inode = match fields[9].parse::<u64>() {
            Ok(i) => i,
            Err(_) => continue,
        };

        entries.push(TcpEntry {
            local_port,
            state,
            inode,
        });
    }

    Ok(entries)
}

/// Extract the port number from a hex address string like "0100007F:1CE4"
fn parse_hex_port(addr: &str) -> Option<u16> {
    let parts: Vec<&str> = addr.split(':').collect();
    if parts.len() != 2 {
        return None;
    }
    u16::from_str_radix(parts[1], 16).ok()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_hex_port() {
        assert_eq!(parse_hex_port("0100007F:1CE4"), Some(0x1CE4)); // 7396
        assert_eq!(parse_hex_port("00000000:0050"), Some(80));
        assert_eq!(parse_hex_port("invalid"), None);
    }
}
