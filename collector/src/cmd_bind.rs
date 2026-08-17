// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::server::{WebServer, relay_client};
use crate::shutdown_notify;
use crate::view::MaterializedView;
use qrcode::QrCode;
use qrcode::render::unicode;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;
use std::process::Command;
use std::time::Duration;
use url::{Url, form_urlencoded};

const DEFAULT_APP_URL: &str = "https://app.agentsight.us/";
const DEFAULT_CONTROLLER_URL: &str = "https://control.agentsight.us";
const CONTROLLER_URL_ENV: &str = "AGENTSIGHT_CONTROLLER_URL";

pub(crate) async fn run_bind(
    listen: &str,
    port: u16,
    no_open: bool,
    qr: bool,
    db_path: Option<String>,
    app_url: &str,
    public_endpoint: Option<&str>,
    docker_containers: &[String],
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let ip: IpAddr = listen
        .parse()
        .map_err(|_| format!("agentsight bind requires an IP listen address, got {listen:?}"))?;

    let addr = SocketAddr::new(ip, port);
    let endpoint = match public_endpoint {
        Some(endpoint) => normalize_endpoint(endpoint),
        None => endpoint_url(ip, port),
    }?;
    let (app_url, allowed_origin) = normalize_app_url(app_url)?;
    let controller_url = controller_url_for_app(&app_url)?;
    let access_token = local_access_token()?;
    let bind_url = build_bind_url(&app_url, &endpoint, &access_token)?;
    let node = local_node_metadata()?;
    let view = MaterializedView::shared_bounded();
    let server = WebServer::new_with_db_path(view, db_path.clone())?;
    let server = if db_path.is_none() {
        server.with_live_host()
    } else {
        server
    };
    let server = server.with_docker_containers(docker_containers)?;
    let server = server.with_direct_access(access_token.clone(), node.clone(), allowed_origin);

    let handle = tokio::spawn(async move { server.start(addr).await });
    tokio::time::sleep(Duration::from_millis(100)).await;
    if handle.is_finished() {
        return match handle.await {
            Ok(Ok(())) => Err("bind server exited during startup".into()),
            Ok(Err(err)) => Err(err),
            Err(err) => Err(err.into()),
        };
    }

    let relay_handle = controller_url.map(|controller_url| {
        tokio::spawn(relay_client::run(
            controller_url,
            node.id.clone(),
            access_token.clone(),
            relay_local_endpoint(ip, port),
        ))
    });

    println!("Bind this device at:\n{bind_url}");
    println!(
        "The access key is stored locally, survives Node restarts, and is removed from the browser URL after opening."
    );
    if relay_handle.is_some() {
        println!(
            "Controller relay is enabled for signed-in remote browsers; Direct access remains preferred."
        );
    }
    if let Some(db_path) = db_path {
        println!("Serving saved AgentSight data from {db_path}.");
    } else {
        println!(
            "Serving the live agent overview and local session history; pass --db for a saved capture."
        );
    }
    if !docker_containers.is_empty() {
        println!(
            "Including agent sessions from Docker containers: {}.",
            docker_containers.join(", ")
        );
    }
    if qr {
        print_qr(&bind_url)?;
    }
    if !no_open && !open_browser(&bind_url) {
        eprintln!("Could not open a browser automatically; open the URL above.");
    }

    shutdown_notify().notified().await;
    if let Some(relay_handle) = relay_handle {
        relay_handle.abort();
    }
    handle.abort();
    Ok(())
}

fn endpoint_url(ip: IpAddr, port: u16) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    if ip.is_unspecified() {
        return Err(
            "--listen 0.0.0.0/:: requires --endpoint with the browser-reachable Node URL".into(),
        );
    }
    Ok(match ip {
        IpAddr::V4(ip) => format!("http://{ip}:{port}"),
        IpAddr::V6(ip) => format!("http://[{ip}]:{port}"),
    })
}

fn relay_local_endpoint(ip: IpAddr, port: u16) -> String {
    match ip {
        IpAddr::V4(ip) if ip.is_unspecified() => {
            format!("http://{}:{port}", Ipv4Addr::LOCALHOST)
        }
        IpAddr::V6(ip) if ip.is_unspecified() => {
            format!("http://[{}]:{port}", Ipv6Addr::LOCALHOST)
        }
        IpAddr::V4(ip) => format!("http://{ip}:{port}"),
        IpAddr::V6(ip) => format!("http://[{ip}]:{port}"),
    }
}

fn random_token() -> String {
    format!(
        "{}{}",
        uuid::Uuid::new_v4().simple(),
        uuid::Uuid::new_v4().simple()
    )
}

fn config_dir() -> Result<std::path::PathBuf, Box<dyn std::error::Error + Send + Sync>> {
    let dir = dirs::config_dir()
        .ok_or("could not find the user configuration directory")?
        .join("agentsight");
    std::fs::create_dir_all(&dir)?;
    Ok(dir)
}

fn local_access_token() -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let path = config_dir()?.join("access-token");
    match std::fs::read_to_string(&path) {
        Ok(value) if valid_access_token(value.trim()) => Ok(value.trim().to_string()),
        Ok(_) => Err(format!("invalid AgentSight access token at {}", path.display()).into()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let token = random_token();
            let mut file = create_private_file(&path)?;
            use std::io::Write;
            writeln!(file, "{token}")?;
            Ok(token)
        }
        Err(error) => Err(error.into()),
    }
}

fn valid_access_token(value: &str) -> bool {
    (32..=256).contains(&value.len())
        && value
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || matches!(character, '_' | '-'))
}

fn local_node_metadata()
-> Result<crate::server::NodeMetadata, Box<dyn std::error::Error + Send + Sync>> {
    let id_path = config_dir()?.join("node-id");
    let id = match std::fs::read_to_string(&id_path) {
        Ok(value) if valid_node_id(value.trim()) => value.trim().to_string(),
        Ok(_) => {
            return Err(
                format!("invalid AgentSight node identity at {}", id_path.display()).into(),
            );
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let id = format!("node_{}", uuid::Uuid::new_v4().simple());
            let mut file = create_private_file(&id_path)?;
            use std::io::Write;
            writeln!(file, "{id}")?;
            id
        }
        Err(error) => return Err(error.into()),
    };
    let name = std::fs::read_to_string("/etc/hostname")
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .or_else(|| std::env::var("COMPUTERNAME").ok())
        .unwrap_or_else(|| "AgentSight Node".to_string());
    Ok(crate::server::NodeMetadata {
        id,
        name,
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

fn create_private_file(path: &Path) -> std::io::Result<std::fs::File> {
    let mut options = std::fs::OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    options.mode(0o600);
    options.open(path)
}

fn valid_node_id(value: &str) -> bool {
    value.starts_with("node_")
        && value.len() <= 64
        && value
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || character == '_')
}

fn normalize_endpoint(value: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let mut endpoint = Url::parse(value)?;
    if !matches!(endpoint.scheme(), "http" | "https")
        || endpoint.host().is_none()
        || !endpoint.username().is_empty()
        || endpoint.password().is_some()
    {
        return Err("--endpoint must be an http(s) URL without credentials".into());
    }
    endpoint.set_path("");
    endpoint.set_query(None);
    endpoint.set_fragment(None);
    Ok(endpoint.to_string().trim_end_matches('/').to_string())
}

fn normalize_controller_url(
    value: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let mut controller = Url::parse(value)?;
    if !matches!(controller.scheme(), "http" | "https")
        || controller.host().is_none()
        || !controller.username().is_empty()
        || controller.password().is_some()
    {
        return Err("AgentSight Controller URL must be an http(s) URL without credentials".into());
    }
    controller.set_path("");
    controller.set_query(None);
    controller.set_fragment(None);
    Ok(controller.to_string().trim_end_matches('/').to_string())
}

fn controller_url_for_app(
    app_url: &Url,
) -> Result<Option<String>, Box<dyn std::error::Error + Send + Sync>> {
    if let Ok(value) = std::env::var(CONTROLLER_URL_ENV) {
        if !value.trim().is_empty() {
            return Ok(Some(normalize_controller_url(value.trim())?));
        }
    }
    if app_url.origin().ascii_serialization() == "https://app.agentsight.us" {
        return Ok(Some(DEFAULT_CONTROLLER_URL.to_string()));
    }
    Ok(None)
}

fn normalize_app_url(
    value: &str,
) -> Result<(Url, String), Box<dyn std::error::Error + Send + Sync>> {
    let mut app_url = Url::parse(if value.is_empty() {
        DEFAULT_APP_URL
    } else {
        value
    })?;
    if !matches!(app_url.scheme(), "http" | "https")
        || app_url.host().is_none()
        || !app_url.username().is_empty()
        || app_url.password().is_some()
    {
        return Err("--app-url must be an http(s) URL without credentials".into());
    }
    app_url.set_query(None);
    app_url.set_fragment(None);
    let allowed_origin = app_url.origin().ascii_serialization();
    Ok((app_url, allowed_origin))
}

fn build_bind_url(
    app_url: &Url,
    endpoint: &str,
    access_token: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let fragment = form_urlencoded::Serializer::new(String::new())
        .append_pair("action", "bind")
        .append_pair("v", "1")
        .append_pair("endpoint", endpoint)
        .append_pair("token", access_token)
        .finish();
    let mut url = app_url.clone();
    url.set_fragment(Some(&fragment));
    Ok(url.into())
}

fn print_qr(value: &str) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let code = QrCode::new(value.as_bytes())?;
    let image = code
        .render::<unicode::Dense1x2>()
        .quiet_zone(true)
        .module_dimensions(2, 1)
        .build();
    println!("\n{image}");
    Ok(())
}

fn open_browser(url: &str) -> bool {
    #[cfg(target_os = "windows")]
    let mut command = {
        let mut command = Command::new("explorer.exe");
        command.arg(url);
        command
    };
    #[cfg(target_os = "macos")]
    let mut command = {
        let mut command = Command::new("open");
        command.arg(url);
        command
    };
    #[cfg(all(unix, not(target_os = "macos")))]
    let mut command = {
        let mut command = Command::new("xdg-open");
        command.arg(url);
        command
    };

    command
        .spawn()
        .map(|mut child| {
            std::thread::spawn(move || {
                let _ = child.wait();
            });
        })
        .is_ok()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bind_url_keeps_access_key_in_fragment() {
        let app = Url::parse("https://self-hosted.example/ui/").unwrap();
        let url = build_bind_url(&app, "http://127.0.0.1:7395", "access-key").unwrap();
        assert_eq!(
            url,
            "https://self-hosted.example/ui/#action=bind&v=1&endpoint=http%3A%2F%2F127.0.0.1%3A7395&token=access-key"
        );
        assert!(!url.contains('?'));
    }

    #[test]
    fn endpoint_formats_ipv6_for_urls() {
        let ip: IpAddr = "::1".parse().unwrap();
        assert_eq!(endpoint_url(ip, 7395).unwrap(), "http://[::1]:7395");
    }

    #[test]
    fn direct_endpoint_accepts_private_ip_url() {
        assert_eq!(
            normalize_endpoint("http://192.168.50.12:7395").unwrap(),
            "http://192.168.50.12:7395"
        );
    }

    #[test]
    fn direct_endpoint_accepts_https_hostname_and_strips_path() {
        assert_eq!(
            normalize_endpoint("https://lab.example.net/agentsight?ignored=1#fragment").unwrap(),
            "https://lab.example.net"
        );
    }

    #[test]
    fn relay_uses_loopback_for_unspecified_bind_addresses() {
        assert_eq!(
            relay_local_endpoint("0.0.0.0".parse().unwrap(), 7395),
            "http://127.0.0.1:7395"
        );
    }

    #[test]
    fn unspecified_listen_requires_a_public_endpoint() {
        assert!(endpoint_url("0.0.0.0".parse().unwrap(), 7395).is_err());
    }

    #[test]
    fn app_url_controls_the_cors_origin() {
        let (url, origin) = normalize_app_url("https://console.example/path").unwrap();
        assert_eq!(url.as_str(), "https://console.example/path");
        assert_eq!(origin, "https://console.example");
    }

    #[test]
    fn node_ids_are_narrowly_validated() {
        assert!(valid_node_id("node_0123abcdef"));
        assert!(!valid_node_id("../../node_secret"));
        assert!(!valid_node_id("machine"));
    }

    #[test]
    fn access_tokens_are_narrowly_validated() {
        assert!(valid_access_token(&"a".repeat(64)));
        assert!(!valid_access_token("short"));
        assert!(!valid_access_token(&format!("{}!", "a".repeat(63))));
    }
}
