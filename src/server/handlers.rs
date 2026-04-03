//! API request handlers

use actix_web::{get, web, HttpResponse, Responder};
use serde::Deserialize;

use super::AppState;
use crate::storage::sqlite::{AuditStore, TokenStore, GenAISqliteStore};
use crate::storage::sqlite::genai::{TimeseriesBucket, ModelTimeseriesBucket};
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

// ─── Session / Trace query endpoints ───────────────────────────────────────

/// Query parameters for /api/sessions
#[derive(Debug, Deserialize)]
pub struct SessionQuery {
    /// Start of time range in nanoseconds (default: 24 h ago)
    pub start_ns: Option<i64>,
    /// End of time range in nanoseconds (default: now)
    pub end_ns: Option<i64>,
}

/// GET /api/sessions?start_ns=<i64>&end_ns=<i64>
///
/// Returns a list of gen_ai.session_id values with aggregated stats.
#[get("/api/sessions")]
pub async fn list_sessions(
    data: web::Data<AppState>,
    query: web::Query<SessionQuery>,
) -> impl Responder {
    let db_path = &data.storage_path;

    let end_ns = query.end_ns.unwrap_or_else(|| now_ns() as i64);
    let start_ns = query.start_ns.unwrap_or_else(|| end_ns - 86_400_000_000_000i64); // 24 h

    match GenAISqliteStore::new_with_path(db_path) {
        Ok(store) => match store.list_sessions(start_ns, end_ns) {
            Ok(sessions) => HttpResponse::Ok().json(sessions),
            Err(e) => HttpResponse::InternalServerError()
                .json(serde_json::json!({"error": e.to_string()})),
        },
        Err(e) => HttpResponse::InternalServerError()
            .json(serde_json::json!({"error": e.to_string()})),
    }
}

/// GET /api/sessions/{session_id}/traces
///
/// Returns all trace IDs belonging to a session with token stats.
#[get("/api/sessions/{session_id}/traces")]
pub async fn list_traces_by_session(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> impl Responder {
    let db_path = &data.storage_path;
    let session_id = path.into_inner();

    match GenAISqliteStore::new_with_path(db_path) {
        Ok(store) => match store.list_traces_by_session(&session_id) {
            Ok(traces) => HttpResponse::Ok().json(traces),
            Err(e) => HttpResponse::InternalServerError()
                .json(serde_json::json!({"error": e.to_string()})),
        },
        Err(e) => HttpResponse::InternalServerError()
            .json(serde_json::json!({"error": e.to_string()})),
    }
}

/// GET /api/traces/{trace_id}
///
/// Returns detailed LLM call events for a trace.
#[get("/api/traces/{trace_id}")]
pub async fn get_trace_detail(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> impl Responder {
    let db_path = &data.storage_path;
    let trace_id = path.into_inner();

    match GenAISqliteStore::new_with_path(db_path) {
        Ok(store) => match store.get_trace_events(&trace_id) {
            Ok(events) => HttpResponse::Ok().json(events),
            Err(e) => HttpResponse::InternalServerError()
                .json(serde_json::json!({"error": e.to_string()})),
        },
        Err(e) => HttpResponse::InternalServerError()
            .json(serde_json::json!({"error": e.to_string()})),
    }
}

// ─── Agent-name & time-series endpoints ────────────────────────────────────

/// Query parameters shared by agent-name and time-series endpoints
#[derive(Debug, Deserialize)]
pub struct TimeRangeQuery {
    pub start_ns: Option<i64>,
    pub end_ns: Option<i64>,
}

/// Query parameters for time-series endpoints
#[derive(Debug, Deserialize)]
pub struct TimeseriesQuery {
    pub start_ns: Option<i64>,
    pub end_ns: Option<i64>,
    /// Filter by a specific agent name (optional)
    pub agent_name: Option<String>,
    /// Number of buckets (default 30)
    pub buckets: Option<u32>,
}

/// GET /api/agent-names?start_ns=<i64>&end_ns=<i64>
///
/// Returns a sorted list of distinct agent_name values.
#[get("/api/agent-names")]
pub async fn list_agent_names(
    data: web::Data<AppState>,
    query: web::Query<TimeRangeQuery>,
) -> impl Responder {
    let db_path = &data.storage_path;
    let end_ns = query.end_ns.unwrap_or_else(|| now_ns() as i64);
    let start_ns = query.start_ns.unwrap_or_else(|| end_ns - 86_400_000_000_000i64);

    match GenAISqliteStore::new_with_path(db_path) {
        Ok(store) => match store.list_agent_names(start_ns, end_ns) {
            Ok(names) => HttpResponse::Ok().json(names),
            Err(e) => HttpResponse::InternalServerError()
                .json(serde_json::json!({"error": e.to_string()})),
        },
        Err(e) => HttpResponse::InternalServerError()
            .json(serde_json::json!({"error": e.to_string()})),
    }
}

/// Response body for /api/timeseries
#[derive(Debug, serde::Serialize)]
pub struct TimeseriesResponse {
    pub token_series: Vec<TimeseriesBucket>,
    pub model_series: Vec<ModelTimeseriesBucket>,
}

/// GET /api/timeseries?start_ns=<i64>&end_ns=<i64>&agent_name=<str>&buckets=<u32>
///
/// Returns time-bucketed token stats (input/output/total) and per-model total-token
/// breakdowns, both within the requested time range.
#[get("/api/timeseries")]
pub async fn get_timeseries(
    data: web::Data<AppState>,
    query: web::Query<TimeseriesQuery>,
) -> impl Responder {
    let db_path = &data.storage_path;
    let end_ns = query.end_ns.unwrap_or_else(|| now_ns() as i64);
    let start_ns = query.start_ns.unwrap_or_else(|| end_ns - 86_400_000_000_000i64);
    let buckets = query.buckets.unwrap_or(30);
    let agent_name = query.agent_name.as_deref();

    match GenAISqliteStore::new_with_path(db_path) {
        Ok(store) => {
            let token_series = match store.get_token_timeseries(start_ns, end_ns, agent_name, buckets) {
                Ok(v) => v,
                Err(e) => return HttpResponse::InternalServerError()
                    .json(serde_json::json!({"error": e.to_string()})),
            };
            let model_series = match store.get_model_timeseries(start_ns, end_ns, agent_name, buckets) {
                Ok(v) => v,
                Err(e) => return HttpResponse::InternalServerError()
                    .json(serde_json::json!({"error": e.to_string()})),
            };
            HttpResponse::Ok().json(TimeseriesResponse { token_series, model_series })
        }
        Err(e) => HttpResponse::InternalServerError()
            .json(serde_json::json!({"error": e.to_string()})),
    }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/// Current UNIX time in nanoseconds
fn now_ns() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64
}

/// Calculate nanosecond timestamp for N hours ago
fn hours_ago_ns(hours: u64) -> u64 {
    now_ns().saturating_sub(hours * 3600 * 1_000_000_000)
}
