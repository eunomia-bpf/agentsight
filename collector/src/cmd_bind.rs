// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::server::WebServer;
use crate::shutdown_notify;
use crate::view::MaterializedView;
use qrcode::QrCode;
use qrcode::render::unicode;
use std::net::{IpAddr, SocketAddr};
use std::os::unix::fs::OpenOptionsExt;
use std::process::Command;
use std::time::Duration;
use url::{Url, form_urlencoded};

const DEFAULT_APP_URL: &str = "https://app.agentsight.us/";

pub(crate) async fn run_bind(
    listen: &str,
    port: u16,
    no_open: bool,
    qr: bool,
    db_path: Option<String>,
    app_url: &str,
    public_endpoint: Option<&str>,
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
    let access_token = random_token();
    let bind_url = build_bind_url(&app_url, &endpoint, &access_token)?;
    let node = local_node_metadata()?;
    let view = MaterializedView::shared_bounded();
    let server = WebServer::new_with_db_path(view, db_path.clone())?.with_direct_access(
        access_token,
        node,
        allowed_origin,
    );

    let handle = tokio::spawn(async move { server.start(addr).await });
    tokio::time::sleep(Duration::from_millis(100)).await;
    if handle.is_finished() {
        return match handle.await {
            Ok(Ok(())) => Err("bind server exited during startup".into()),
            Ok(Err(err)) => Err(err),
            Err(err) => Err(err.into()),
        };
    }

    println!("Bind this device at:\n{bind_url}");
    println!(
        "The access key lasts only while this command is running and is removed from the browser URL after opening."
    );
    if let Some(db_path) = db_path {
        println!("Serving saved AgentSight data from {db_path}.");
    } else {
        println!("Serving the local agent session index; pass --db for a saved capture.");
    }
    if qr {
        print_qr(&bind_url)?;
    }
    if !no_open && !open_browser(&bind_url) {
        eprintln!("Could not open a browser automatically; open the URL above.");
    }

    shutdown_notify().notified().await;
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

fn random_token() -> String {
    format!(
        "{}{}",
        uuid::Uuid::new_v4().simple(),
        uuid::Uuid::new_v4().simple()
    )
}

fn local_node_metadata()
-> Result<crate::server::NodeMetadata, Box<dyn std::error::Error + Send + Sync>> {
    let config_dir = dirs::config_dir()
        .ok_or("could not find the user configuration directory")?
        .join("agentsight");
    std::fs::create_dir_all(&config_dir)?;
    let id_path = config_dir.join("node-id");
    let id = match std::fs::read_to_string(&id_path) {
        Ok(value) if valid_node_id(value.trim()) => value.trim().to_string(),
        Ok(_) => {
            return Err(
                format!("invalid AgentSight node identity at {}", id_path.display()).into(),
            );
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let id = format!("node_{}", uuid::Uuid::new_v4().simple());
            let mut file = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .mode(0o600)
                .open(&id_path)?;
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
        .unwrap_or_else(|| "AgentSight Node".to_string());
    Ok(crate::server::NodeMetadata {
        id,
        name,
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
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
    Command::new("xdg-open")
        .arg(url)
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
}
