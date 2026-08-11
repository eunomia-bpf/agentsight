// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::server::WebServer;
use crate::shutdown_notify;
use crate::view::MaterializedView;
use qrcode::QrCode;
use qrcode::render::unicode;
use std::net::{IpAddr, SocketAddr};
use std::process::Command;
use std::time::Duration;
use url::form_urlencoded;

const HOSTED_APP_BIND_URL: &str = "https://app.agentsight.us/";

pub(crate) async fn run_bind(
    listen: &str,
    port: u16,
    no_open: bool,
    qr: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let ip: IpAddr = listen
        .parse()
        .map_err(|_| format!("agentsight bind requires a loopback IP address, got {listen:?}"))?;
    if !ip.is_loopback() {
        return Err(
            "agentsight bind only listens on loopback; use managed relay for remote access".into(),
        );
    }

    let addr = SocketAddr::new(ip, port);
    let endpoint = endpoint_url(ip, port);
    let pairing_code = random_token();
    let bind_url = build_bind_url(&endpoint, &pairing_code);
    let view = MaterializedView::shared_bounded();
    let server = WebServer::new_with_db_path(view, None)?.with_pairing_code(pairing_code);

    println!("Bind this device at:\n{bind_url}");
    println!("The pairing code expires when this command exits and can be used only once.");
    if qr {
        print_qr(&bind_url)?;
    }
    if !no_open && !open_browser(&bind_url) {
        eprintln!("Could not open a browser automatically; open the URL above.");
    }

    let handle = tokio::spawn(async move { server.start(addr).await });
    tokio::time::sleep(Duration::from_millis(100)).await;
    if handle.is_finished() {
        return match handle.await {
            Ok(Ok(())) => Err("bind server exited during startup".into()),
            Ok(Err(err)) => Err(err),
            Err(err) => Err(err.into()),
        };
    }

    shutdown_notify().notified().await;
    handle.abort();
    Ok(())
}

fn endpoint_url(ip: IpAddr, port: u16) -> String {
    match ip {
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

fn build_bind_url(endpoint: &str, pairing_code: &str) -> String {
    let fragment = form_urlencoded::Serializer::new(String::new())
        .append_pair("action", "bind")
        .append_pair("v", "1")
        .append_pair("endpoint", endpoint)
        .append_pair("code", pairing_code)
        .finish();
    format!("{HOSTED_APP_BIND_URL}#{fragment}")
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
    fn bind_url_keeps_secret_in_fragment() {
        let url = build_bind_url("http://127.0.0.1:7395", "one-time-code");
        assert_eq!(
            url,
            "https://app.agentsight.us/#action=bind&v=1&endpoint=http%3A%2F%2F127.0.0.1%3A7395&code=one-time-code"
        );
        assert!(!url.contains('?'));
    }

    #[test]
    fn endpoint_formats_ipv6_for_urls() {
        let ip: IpAddr = "::1".parse().unwrap();
        assert_eq!(endpoint_url(ip, 7395), "http://[::1]:7395");
    }
}
