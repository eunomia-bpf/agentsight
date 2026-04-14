//! API server module
//!
//! Provides a lightweight HTTP API server using actix-web for querying
//! AgentSight storage data, and optionally serves the embedded frontend.

mod handlers;

use std::path::PathBuf;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

use actix_cors::Cors;
use actix_web::{get, web, App, HttpRequest, HttpResponse, HttpServer, Responder};
use include_dir::{include_dir, Dir};

use crate::health::{HealthChecker, HealthStore};

/// Embedded frontend static files (built from dashboard/ via `npm run build:embed`)
/// The directory `frontend-dist/` must exist at compile time; if it is absent
/// (e.g. first build before running npm), Rust will use an empty dir.
static FRONTEND: Dir<'static> = include_dir!("$CARGO_MANIFEST_DIR/frontend-dist");

/// Shared application state accessible from all handlers
pub struct AppState {
    /// Path to the SQLite database file
    pub storage_path: PathBuf,
    /// Server start time (for uptime calculation)
    pub start_time: Instant,
    /// Shared health store populated by the background HealthChecker
    pub health_store: Arc<RwLock<HealthStore>>,
}

// ─── Static file handler ─────────────────────────────────────────────────────

/// Serve embedded frontend files.
/// Any path that doesn't start with /api or /health is treated as a static
/// asset; unknown paths fall back to index.html (SPA client-side routing).
#[get("/{tail:.*}")]
async fn serve_frontend(req: HttpRequest) -> impl Responder {
    let path = req.match_info().get("tail").unwrap_or("");

    // Try exact match first
    let file = if path.is_empty() {
        FRONTEND.get_file("index.html")
    } else {
        FRONTEND.get_file(path)
    };

    match file {
        Some(f) => {
            let mime = if path.is_empty() {
                "text/html; charset=utf-8"
            } else {
                mime_for_path(path)
            };
            HttpResponse::Ok()
                .content_type(mime)
                .body(f.contents())
        }
        None => {
            // SPA fallback: return index.html for unmatched paths
            match FRONTEND.get_file("index.html") {
                Some(index) => HttpResponse::Ok()
                    .content_type("text/html; charset=utf-8")
                    .body(index.contents()),
                None => HttpResponse::NotFound().body("Frontend not embedded. Run `npm run build:embed` first."),
            }
        }
    }
}

fn mime_for_path(path: &str) -> &'static str {
    if path.ends_with(".html") { "text/html; charset=utf-8" }
    else if path.ends_with(".js") { "application/javascript; charset=utf-8" }
    else if path.ends_with(".css") { "text/css; charset=utf-8" }
    else if path.ends_with(".json") { "application/json" }
    else if path.ends_with(".svg") { "image/svg+xml" }
    else if path.ends_with(".png") { "image/png" }
    else if path.ends_with(".ico") { "image/x-icon" }
    else if path.ends_with(".woff2") { "font/woff2" }
    else { "application/octet-stream" }
}

// ─── Server entry point ───────────────────────────────────────────────────────

/// Start the API server
///
/// Binds to the given host:port and serves API endpoints + embedded frontend.
/// This function blocks until the server is shut down.
pub async fn run_server(host: &str, port: u16, storage_path: PathBuf) -> std::io::Result<()> {
    // Spin up the background health checker
    let health_store = Arc::new(RwLock::new(HealthStore::new()));
    let checker = HealthChecker::new(Arc::clone(&health_store), Duration::from_secs(30));
    checker.start();

    let data = web::Data::new(AppState {
        storage_path,
        start_time: Instant::now(),
        health_store,
    });

    let has_frontend = FRONTEND.get_file("index.html").is_some();
    log::info!("AgentSight API server listening on http://{}:{}", host, port);
    eprintln!("AgentSight API server listening on http://{}:{}", host, port);
    if has_frontend {
        eprintln!("Dashboard UI: http://{}:{}/", host, port);
    } else {
        eprintln!("[WARN] Frontend not embedded. Run `npm run build:embed` in dashboard/ then recompile.");
    }

    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allowed_methods(vec!["GET", "DELETE", "POST", "OPTIONS"])
            .allowed_headers(vec!["Content-Type"])
            .max_age(3600);

        App::new()
            .wrap(cors)
            .app_data(data.clone())
            // API routes (registered before the catch-all static handler)
            .service(handlers::health)
            .service(handlers::metrics)
            .service(handlers::stats)
            .service(handlers::list_sessions)
            .service(handlers::list_traces_by_session)
            .service(handlers::get_trace_detail)
            .service(handlers::list_agent_names)
            .service(handlers::get_timeseries)
            .service(handlers::export_atif_trace)
            .service(handlers::export_atif_session)
            .service(handlers::get_agent_health)
            .service(handlers::delete_agent_health)
            .service(handlers::restart_agent_health)
            // Frontend static files (catch-all, must be last)
            .service(serve_frontend)
    })
    .bind((host, port))?
    .run()
    .await
}
