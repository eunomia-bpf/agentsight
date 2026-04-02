//! API server module
//!
//! Provides a lightweight HTTP API server using actix-web for querying
//! AgentSight storage data.

mod handlers;

use std::path::PathBuf;
use std::time::Instant;

use actix_cors::Cors;
use actix_web::{web, App, HttpServer};

/// Shared application state accessible from all handlers
pub struct AppState {
    /// Path to the SQLite database file
    pub storage_path: PathBuf,
    /// Server start time (for uptime calculation)
    pub start_time: Instant,
}

/// Start the API server
///
/// Binds to the given host:port and serves API endpoints.
/// This function blocks until the server is shut down.
pub async fn run_server(host: &str, port: u16, storage_path: PathBuf) -> std::io::Result<()> {
    let data = web::Data::new(AppState {
        storage_path,
        start_time: Instant::now(),
    });

    log::info!("AgentSight API server listening on http://{}:{}", host, port);
    eprintln!("AgentSight API server listening on http://{}:{}", host, port);

    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allowed_methods(vec!["GET", "OPTIONS"])
            .allowed_headers(vec!["Content-Type"])
            .max_age(3600);

        App::new()
            .wrap(cors)
            .app_data(data.clone())
            .service(handlers::health)
            .service(handlers::stats)
    })
    .bind((host, port))?
    .run()
    .await
}
