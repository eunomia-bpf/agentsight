//! API request handlers

use actix_web::{get, web, HttpResponse, Responder};

use super::AppState;
use crate::storage::sqlite::{AuditStore, TokenStore};
use crate::storage::sqlite::token::TokenQuery;
use crate::TimePeriod;

/// GET /health — health check endpoint
#[get("/health")]
pub async fn health(data: web::Data<AppState>) -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "ok",
        "version": env!("CARGO_PKG_VERSION"),
        "uptime_seconds": data.start_time.elapsed().as_secs()
    }))
}

/// GET /api/stats — demo endpoint showing storage statistics
#[get("/api/stats")]
pub async fn stats(data: web::Data<AppState>) -> impl Responder {
    let db_path = &data.storage_path;

    // Query audit summary (last 24 hours)
    let audit_json = match AuditStore::new(db_path) {
        Ok(store) => {
            let since_ns = hours_ago_ns(24);
            match store.summary(since_ns) {
                Ok(summary) => serde_json::to_value(&summary).unwrap_or(serde_json::json!(null)),
                Err(e) => serde_json::json!({"error": e.to_string()}),
            }
        }
        Err(e) => serde_json::json!({"error": e.to_string()}),
    };

    // Query token usage (today)
    let token_json = {
        let store = TokenStore::new(db_path);
        let query = TokenQuery::new(&store);
        let result = query.by_period(TimePeriod::Today);
        serde_json::to_value(&result).unwrap_or(serde_json::json!(null))
    };

    HttpResponse::Ok().json(serde_json::json!({
        "audit": audit_json,
        "tokens": token_json,
    }))
}

/// Calculate nanosecond timestamp for N hours ago
fn hours_ago_ns(hours: u64) -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;
    now.saturating_sub(hours * 3600 * 1_000_000_000)
}
