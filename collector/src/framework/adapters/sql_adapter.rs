// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::storage::SqliteStore;
use rusqlite::params;
use uuid::Uuid;

pub type AdapterResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

#[derive(Debug, Clone)]
pub struct SqlAdapter {
    pub id: &'static str,
    pub version: &'static str,
    pub adapter_type: &'static str,
    pub detect_sql: Option<&'static str>,
    pub sql_files: &'static [(&'static str, &'static str)],
}

impl SqlAdapter {
    pub fn validate(&self) -> AdapterResult<()> {
        if self.id.is_empty() || self.version.is_empty() || self.adapter_type.is_empty() {
            return Err("SQL adapter id/version/type must not be empty".into());
        }
        for (name, sql) in self.sql_files {
            validate_sql_safety(name, sql)?;
        }
        Ok(())
    }

    pub fn run(&self, store: &mut SqliteStore) -> AdapterResult<()> {
        let started = now_ms();
        let run_id = format!("adapter-{}-{}", self.id, Uuid::new_v4());
        store.connection_mut().execute(
            "INSERT OR REPLACE INTO adapter_runs
             (id, adapter_id, adapter_version, started_at_ms, mode, status)
             VALUES (?1, ?2, ?3, ?4, 'sql', 'running')",
            params![run_id, self.id, self.version, started as i64],
        )?;

        let run_result = (|| -> AdapterResult<()> {
            self.validate()?;
            let tx = store.connection_mut().transaction()?;
            for (_name, sql) in self.sql_files {
                tx.execute_batch(sql)?;
            }
            tx.commit()?;
            Ok(())
        })();

        if let Err(e) = run_result {
            let message = e.to_string();
            store.connection_mut().execute(
                "UPDATE adapter_runs
                 SET finished_at_ms = ?1, status = 'failed', error_message = ?2
                 WHERE id = ?3",
                params![now_ms() as i64, message, run_id],
            )?;
            return Err(e);
        }

        store.connection_mut().execute(
            "UPDATE adapter_runs SET finished_at_ms = ?1, status = 'ok' WHERE id = ?2",
            params![now_ms() as i64, run_id],
        )?;
        Ok(())
    }

    pub fn supports_detect(&self) -> bool {
        self.detect_sql.is_some()
    }

    pub fn detects(&self, store: &mut SqliteStore) -> AdapterResult<bool> {
        let Some(sql) = self.detect_sql else {
            return Ok(true);
        };
        let detected: i64 = store
            .connection_mut()
            .query_row(sql, [], |row| row.get(0))?;
        Ok(detected != 0)
    }
}

pub fn run_sql_adapters(store: &mut SqliteStore, adapter: &str) -> AdapterResult<()> {
    let adapters = builtin_adapters();
    let selected: Vec<_> = if adapter == "auto" {
        adapters
            .into_iter()
            .filter_map(|adapter| match adapter.detects(store) {
                Ok(true) => Some(Ok(adapter)),
                Ok(false) => None,
                Err(e) => Some(Err(e)),
            })
            .collect::<AdapterResult<Vec<_>>>()?
    } else {
        adapters.into_iter().filter(|a| a.id == adapter).collect()
    };

    if selected.is_empty() && adapter != "auto" {
        return Err(format!("unknown SQL adapter '{}'", adapter).into());
    }

    for adapter in selected {
        adapter.run(store)?;
    }
    Ok(())
}

pub fn builtin_adapters() -> Vec<SqlAdapter> {
    vec![
        SqlAdapter {
            id: "anthropic",
            version: "0.1.0",
            adapter_type: "provider",
            detect_sql: Some(
                "SELECT CASE WHEN EXISTS (
                   SELECT 1 FROM canonical_events
                   WHERE provider = 'anthropic'
                      OR host LIKE '%anthropic%'
                 ) OR EXISTS (
                   SELECT 1 FROM llm_calls
                   WHERE provider = 'anthropic'
                      OR host LIKE '%anthropic%'
                 ) THEN 1 ELSE 0 END",
            ),
            sql_files: &[(
                "project_token_usage.sql",
                include_str!("../../../adapters/sql/anthropic/project_token_usage.sql"),
            )],
        },
        SqlAdapter {
            id: "claude-code",
            version: "0.1.0",
            adapter_type: "agent",
            detect_sql: Some(
                "SELECT CASE
                   WHEN EXISTS (
                     SELECT 1 FROM canonical_events
                     WHERE comm LIKE 'claude%'
                        OR json_extract(attributes_json, '$.program') = 'claude'
                   ) THEN 1
                   WHEN EXISTS (
                     SELECT 1 FROM canonical_events
                     WHERE host LIKE '%datadoghq.com'
                       AND attributes_json LIKE '%tengu_api_success%'
                   ) THEN 1
                   ELSE 0
                 END",
            ),
            sql_files: &[
                (
                    "project_cli_output_tokens.sql",
                    include_str!("../../../adapters/sql/claude-code/project_cli_output_tokens.sql"),
                ),
                (
                    "project_telemetry_tokens.sql",
                    include_str!("../../../adapters/sql/claude-code/project_telemetry_tokens.sql"),
                ),
                (
                    "project_sessions.sql",
                    include_str!("../../../adapters/sql/claude-code/project_sessions.sql"),
                ),
                (
                    "project_tool_calls.sql",
                    include_str!("../../../adapters/sql/claude-code/project_tool_calls.sql"),
                ),
            ],
        },
        SqlAdapter {
            id: "openclaw",
            version: "0.1.0",
            adapter_type: "agent",
            detect_sql: Some(
                "SELECT CASE WHEN EXISTS (
                   SELECT 1 FROM llm_calls
                   WHERE instr(COALESCE(request_body_json, ''), 'OpenClaw gateway') > 0
                      OR instr(COALESCE(request_body_json, ''), 'openclaw.mjs') > 0
                      OR instr(COALESCE(response_body_json, ''), 'OpenClaw gateway') > 0
                      OR instr(COALESCE(response_body_json, ''), 'openclaw.mjs') > 0
                 ) THEN 1 ELSE 0 END",
            ),
            sql_files: &[(
                "project_sessions.sql",
                include_str!("../../../adapters/sql/openclaw/project_sessions.sql"),
            )],
        },
        SqlAdapter {
            id: "gemini-cli",
            version: "0.1.0",
            adapter_type: "agent",
            detect_sql: Some(
                "SELECT CASE
                   WHEN EXISTS (
                     SELECT 1 FROM canonical_events
                     WHERE json_extract(attributes_json, '$.program') = 'gemini'
                        OR host LIKE '%cloudcode-pa.googleapis.com%'
                        OR LOWER(attributes_json) LIKE '%geminicli/%'
                   ) THEN 1
                   WHEN EXISTS (
                     SELECT 1 FROM llm_calls
                     WHERE host LIKE '%cloudcode-pa.googleapis.com%'
                        OR LOWER(COALESCE(request_body_json, '')) LIKE '%geminicli/%'
                   ) THEN 1
                   ELSE 0
                 END",
            ),
            sql_files: &[
                (
                    "project_cli_output_tokens.sql",
                    include_str!("../../../adapters/sql/gemini-cli/project_cli_output_tokens.sql"),
                ),
                (
                    "project_sessions.sql",
                    include_str!("../../../adapters/sql/gemini-cli/project_sessions.sql"),
                ),
            ],
        },
    ]
}

fn validate_sql_safety(name: &str, sql: &str) -> AdapterResult<()> {
    let lowered = sql.to_ascii_lowercase();
    let forbidden = [
        "drop ",
        "alter ",
        "delete ",
        "vacuum",
        "attach ",
        "detach ",
        "pragma ",
        "create ",
        "update ",
        "reindex",
        "load_extension",
        "begin",
        "commit",
        "rollback",
        "insert into raw_events",
    ];
    for token in forbidden {
        if lowered.contains(token) {
            return Err(format!(
                "SQL adapter file '{}' uses forbidden statement '{}'",
                name,
                token.trim()
            )
            .into());
        }
    }
    let approved_targets = [
        "llm_calls",
        "token_usage",
        "audit_events",
        "agent_sessions",
        "conversations",
        "tool_calls",
        "interruptions",
    ];
    for statement in lowered.split(';').map(str::trim).filter(|s| !s.is_empty()) {
        let valid_prefix = approved_targets.iter().any(|target| {
            statement.starts_with(&format!("insert or replace into {}", target))
                || statement.starts_with(&format!("insert or ignore into {}", target))
        });
        if !valid_prefix {
            return Err(format!(
                "SQL adapter file '{}' may only insert into approved semantic tables",
                name
            )
            .into());
        }
    }
    Ok(())
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::framework::core::Event;
    use crate::framework::storage::{GenericProjector, SqliteStore};
    use serde_json::json;

    #[test]
    fn builtin_sql_adapters_are_safe() {
        for adapter in builtin_adapters() {
            adapter.validate().unwrap();
        }
    }

    #[test]
    fn builtin_sql_adapters_support_auto_detection() {
        for adapter in builtin_adapters() {
            assert!(
                adapter.supports_detect(),
                "adapter '{}' should expose detect_sql",
                adapter.id
            );
        }
    }

    #[test]
    fn auto_adapter_runs_only_detected_adapter() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            42,
            "gemini".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "gemini",
                "stream": "stdout",
                "parsed_json": {
                    "stats": {
                        "models": {
                            "gemini-2.5-pro": {
                                "tokens": {
                                    "input": 100,
                                    "prompt": 100,
                                    "candidates": 20,
                                    "thoughts": 0,
                                    "cached": 0,
                                    "total": 120
                                }
                            }
                        }
                    }
                }
            }),
        );
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "auto").unwrap();

        let adapter_ids: Vec<String> = {
            let mut stmt = store
                .connection()
                .prepare(
                    "SELECT DISTINCT adapter_id FROM adapter_runs
                     WHERE status = 'ok'
                     ORDER BY adapter_id",
                )
                .unwrap();
            stmt.query_map([], |row| row.get(0))
                .unwrap()
                .collect::<Result<Vec<String>, _>>()
                .unwrap()
        };
        assert_eq!(adapter_ids, vec!["gemini-cli".to_string()]);

        let total: i64 = store
            .connection()
            .query_row(
                "SELECT COALESCE(SUM(total_tokens), 0)
                 FROM token_usage WHERE adapter_id = 'gemini-cli'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(total, 120);
    }

    #[test]
    fn auto_adapter_skips_undetected_adapters() {
        let mut store = SqliteStore::open_in_memory().unwrap();

        run_sql_adapters(&mut store, "auto").unwrap();

        let runs: i64 = store
            .connection()
            .query_row("SELECT COUNT(*) FROM adapter_runs", [], |row| row.get(0))
            .unwrap();
        assert_eq!(runs, 0);
    }

    #[test]
    fn claude_sql_adapter_is_idempotent() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let sse = Event::new_with_timestamp(
            2,
            "sse_processor".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "sse_events": [
                    {"event":"message_start","parsed_data":{"message":{"model":"claude-sonnet-4-20250514","usage":{"input_tokens":9}}}},
                    {"event":"content_block_start","parsed_data":{"content_block":{"type":"tool_use","id":"toolu_1","name":"Bash","input":{"command":"ls"}}}},
                    {"event":"message_delta","parsed_data":{"usage":{"output_tokens":6}}}
                ]
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&sse, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();
        let first_count: i64 = store
            .connection()
            .query_row("SELECT COUNT(*) FROM tool_calls", [], |r| r.get(0))
            .unwrap();
        run_sql_adapters(&mut store, "claude-code").unwrap();
        let second_count: i64 = store
            .connection()
            .query_row("SELECT COUNT(*) FROM tool_calls", [], |r| r.get(0))
            .unwrap();
        assert_eq!(first_count, 1);
        assert_eq!(second_count, first_count);
    }

    #[test]
    fn claude_telemetry_does_not_double_count_generic_usage() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let sse = Event::new_with_timestamp(
            2,
            "sse_processor".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "sse_events": [
                    {"event":"message_start","parsed_data":{"message":{"model":"claude-sonnet-4-20250514","usage":{"input_tokens":9}}}},
                    {"event":"message_delta","parsed_data":{"usage":{"output_tokens":6}}}
                ]
            }),
        );
        let telemetry = Event::new_with_timestamp(
            3,
            "http_parser".to_string(),
            42,
            "HTTP Client".to_string(),
            json!({
                "tid": 8,
                "message_type": "request",
                "method": "POST",
                "path": "/api/v2/logs",
                "headers": { "host": "http-intake.logs.us5.datadoghq.com" },
                "body": "[{\"message\":\"tengu_api_success\",\"model\":\"claude-sonnet-4-20250514\",\"provider\":\"firstParty\",\"input_tokens\":9,\"output_tokens\":6}]"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&sse, &mut projector).unwrap();
        store.insert_event(&telemetry, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();
        let (count, total): (i64, i64) = store
            .connection()
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0) FROM token_usage",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(count, 1);
        assert_eq!(total, 15);
    }

    #[test]
    fn claude_telemetry_fallback_projects_raw_ssl_tokens() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let raw = Event::new_with_timestamp(
            1,
            "ssl".to_string(),
            42,
            "HTTP Client".to_string(),
            json!({
                "data": "{\"message\":\"tengu_api_success\",\"input_tokens\":445,\"output_tokens\":13,\"cached_input_tokens\":0}"
            }),
        );
        store.insert_event(&raw, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();
        let (source, total): (String, i64) = store
            .connection()
            .query_row("SELECT source, total_tokens FROM token_usage", [], |r| {
                Ok((r.get(0)?, r.get(1)?))
            })
            .unwrap();
        assert_eq!(source, "claude_telemetry_fallback");
        assert_eq!(total, 458);
    }

    #[test]
    fn gemini_cli_adapter_projects_sessions() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            77,
            "MainThread".to_string(),
            json!({
                "tid": 7001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1internal:generateContent",
                "headers": { "host": "cloudcode-pa.googleapis.com", "user-agent": "GeminiCLI/0.28.1" },
                "body": "{\"model\":\"gemini-2.5-pro\",\"request\":{\"contents\":[{\"role\":\"user\",\"parts\":[{\"text\":\"This is the Gemini CLI. hi\"}]}]}}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            77,
            "MainThread".to_string(),
            json!({
                "tid": 7001,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"usageMetadata\":{\"promptTokenCount\":11,\"candidatesTokenCount\":4,\"totalTokenCount\":15}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let (agent_type, total): (String, i64) = store
            .connection()
            .query_row(
                "SELECT agent_type, total_tokens FROM agent_sessions",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(agent_type, "gemini-cli");
        assert_eq!(total, 15);
    }

    #[test]
    fn gemini_cli_adapter_projects_stdout_stats_tokens() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            77,
            "gemini".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "gemini",
                "stream": "stdout",
                "parsed_json": {
                    "session_id": "session-1",
                    "response": "agentsight-smoke",
                    "stats": {
                        "models": {
                            "gemini-3-flash-preview": {
                                "tokens": {
                                    "input": 7598,
                                    "prompt": 7598,
                                    "candidates": 4,
                                    "thoughts": 0,
                                    "cached": 0,
                                    "total": 7602
                                }
                            },
                            "gemini-3.1-flash-lite": {
                                "tokens": {
                                    "input": 2853,
                                    "prompt": 2853,
                                    "candidates": 41,
                                    "thoughts": 98,
                                    "cached": 0,
                                    "total": 2992
                                }
                            }
                        }
                    }
                }
            }),
        );
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let (rows, total): (i64, i64) = store
            .connection()
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0)
                 FROM token_usage WHERE source = 'gemini_cli_stdout'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(rows, 2);
        assert_eq!(total, 10594);
        let session_total: i64 = store
            .connection()
            .query_row(
                "SELECT total_tokens FROM agent_sessions WHERE agent_type = 'gemini-cli'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(session_total, 10594);
    }

    #[test]
    fn gemini_cli_adapter_projects_request_only_sessions() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            77,
            "MainThread".to_string(),
            json!({
                "tid": 7001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1internal:streamGenerateContent?alt=sse",
                "headers": { "host": "cloudcode-pa.googleapis.com" },
                "body": "{\"model\":\"gemini-2.5-pro\",\"contents\":[{\"role\":\"user\",\"parts\":[{\"text\":\"hi\"}]}]}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let (agent_type, model, total): (String, String, i64) = store
            .connection()
            .query_row(
                "SELECT agent_type, model, total_tokens FROM agent_sessions",
                [],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
            )
            .unwrap();
        assert_eq!(agent_type, "gemini-cli");
        assert_eq!(model, "gemini-2.5-pro");
        assert_eq!(total, 0);
    }

    #[test]
    fn gemini_cli_stdout_tokens_replace_request_only_session() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            77,
            "gemini".to_string(),
            json!({
                "tid": 7001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1internal:streamGenerateContent?alt=sse",
                "headers": { "host": "cloudcode-pa.googleapis.com" },
                "body": "{\"model\":\"gemini-3-flash-preview\",\"contents\":[]}"
            }),
        );
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            77,
            "gemini".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "gemini",
                "stream": "stdout",
                "parsed_json": {
                    "stats": {
                        "models": {
                            "gemini-3-flash-preview": {
                                "tokens": {
                                    "input": 7,
                                    "candidates": 3,
                                    "thoughts": 2,
                                    "total": 12
                                }
                            }
                        }
                    }
                }
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let (projection, total): (String, i64) = store
            .connection()
            .query_row(
                "SELECT json_extract(attributes_json, '$.projection'), total_tokens
                 FROM agent_sessions WHERE agent_type = 'gemini-cli'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(projection, "cli-output");
        assert_eq!(total, 12);
    }

    #[test]
    fn gemini_cli_stdout_does_not_double_count_generic_usage() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            77,
            "node".to_string(),
            json!({
                "tid": 7001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1internal:generateContent",
                "headers": { "host": "cloudcode-pa.googleapis.com" },
                "body": "{\"model\":\"gemini-3-flash-preview\",\"contents\":[]}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            77,
            "node".to_string(),
            json!({
                "tid": 7001,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"usageMetadata\":{\"promptTokenCount\":11,\"candidatesTokenCount\":4,\"totalTokenCount\":15}}"
            }),
        );
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            70,
            "gemini".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "gemini",
                "stream": "stdout",
                "parsed_json": {
                    "stats": {
                        "models": {
                            "gemini-3-flash-preview": {
                                "tokens": {
                                    "input": 11,
                                    "candidates": 4,
                                    "total": 15
                                }
                            }
                        }
                    }
                }
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let (rows, total): (i64, i64) = store
            .connection()
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0) FROM token_usage",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(rows, 1);
        assert_eq!(total, 15);
    }

    #[test]
    fn gemini_cli_adapter_ignores_generic_gemini_api_calls() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            77,
            "node".to_string(),
            json!({
                "tid": 7001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1beta/models/gemini-2.5-pro:generateContent",
                "headers": { "host": "generativelanguage.googleapis.com" },
                "body": "{\"contents\":[{\"role\":\"user\",\"parts\":[{\"text\":\"hi\"}]}]}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            77,
            "node".to_string(),
            json!({
                "tid": 7001,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"usageMetadata\":{\"promptTokenCount\":11,\"candidatesTokenCount\":4,\"totalTokenCount\":15}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();

        run_sql_adapters(&mut store, "gemini-cli").unwrap();
        let count: i64 = store
            .connection()
            .query_row(
                "SELECT COUNT(*) FROM agent_sessions WHERE agent_type = 'gemini-cli'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 0);
    }

    #[test]
    fn claude_code_adapter_projects_stdout_model_usage() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            42,
            "claude".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "claude",
                "stream": "stdout",
                "parsed_json": [
                    {"type": "system", "subtype": "init", "session_id": "session-1"},
                    {
                        "type": "result",
                        "subtype": "success",
                        "modelUsage": {
                            "claude-haiku-4-5-20251001": {
                                "inputTokens": 445,
                                "outputTokens": 14,
                                "cacheReadInputTokens": 0,
                                "cacheCreationInputTokens": 0
                            },
                            "claude-opus-4-7[1m]": {
                                "inputTokens": 1678,
                                "outputTokens": 10,
                                "cacheReadInputTokens": 9793,
                                "cacheCreationInputTokens": 5988
                            }
                        }
                    }
                ]
            }),
        );
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();
        let (rows, total): (i64, i64) = store
            .connection()
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0)
                 FROM token_usage WHERE source = 'claude_code_stdout_model_usage'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(rows, 2);
        assert_eq!(total, 17928);
        let session_total: i64 = store
            .connection()
            .query_row(
                "SELECT total_tokens FROM agent_sessions WHERE agent_type = 'claude-code'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(session_total, 17928);
    }

    #[test]
    fn claude_code_adapter_projects_cli_output_tool_calls() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            42,
            "claude".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "claude",
                "stream": "stdout",
                "parsed_json": [
                    {
                        "type": "assistant",
                        "session_id": "session-1",
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "toolu_1",
                                    "name": "Bash",
                                    "input_redacted": true
                                }
                            ]
                        }
                    },
                    {
                        "type": "result",
                        "modelUsage": {
                            "claude-haiku-4-5-20251001": {
                                "inputTokens": 10,
                                "outputTokens": 2,
                                "cacheReadInputTokens": 0,
                                "cacheCreationInputTokens": 0
                            }
                        }
                    }
                ]
            }),
        );
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();

        let (tool_name, input_json): (String, String) = store
            .connection()
            .query_row(
                "SELECT tool_name, input_json FROM tool_calls WHERE adapter_id = 'claude-code'",
                [],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .unwrap();
        assert_eq!(tool_name, "Bash");
        assert_eq!(input_json, "{\"redacted\":true}");
    }

    #[test]
    fn claude_code_stdout_does_not_double_count_generic_usage() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-opus-4-7\"}"
            }),
        );
        let sse = Event::new_with_timestamp(
            2,
            "sse_processor".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "sse_events": [
                    {"event":"message_start","parsed_data":{"message":{"model":"claude-opus-4-7","usage":{"input_tokens":9,"cache_read_input_tokens":2}}}},
                    {"event":"message_delta","parsed_data":{"usage":{"output_tokens":6}}}
                ]
            }),
        );
        let output = Event::new_with_timestamp(
            10,
            "cli_output".to_string(),
            42,
            "claude".to_string(),
            json!({
                "event": "CLI_OUTPUT",
                "program": "claude",
                "stream": "stdout",
                "parsed_json": [
                    {
                        "type": "result",
                        "modelUsage": {
                            "claude-opus-4-7[1m]": {
                                "inputTokens": 9,
                                "outputTokens": 10,
                                "cacheReadInputTokens": 2,
                                "cacheCreationInputTokens": 0
                            }
                        }
                    }
                ]
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&sse, &mut projector).unwrap();
        store.insert_event(&output, &mut projector).unwrap();

        run_sql_adapters(&mut store, "claude-code").unwrap();
        let (rows, total): (i64, i64) = store
            .connection()
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(total_tokens), 0) FROM token_usage",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(rows, 1);
        assert_eq!(total, 17);
    }

    #[test]
    fn openclaw_adapter_ignores_generic_node_llm_calls() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            88,
            "node".to_string(),
            json!({
                "tid": 8001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.openai.com" },
                "body": "{\"model\":\"gpt-4.1-mini\",\"messages\":[{\"role\":\"user\",\"content\":\"tell me about openclaw\"}]}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            88,
            "node".to_string(),
            json!({
                "tid": 8001,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"usage\":{\"prompt_tokens\":3,\"completion_tokens\":4}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();

        run_sql_adapters(&mut store, "openclaw").unwrap();
        let count: i64 = store
            .connection()
            .query_row(
                "SELECT COUNT(*) FROM agent_sessions WHERE agent_type = 'openclaw'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 0);
    }

    #[test]
    fn openclaw_adapter_projects_marked_provider_calls_with_tokens() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            88,
            "node".to_string(),
            json!({
                "tid": 8001,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.openai.com" },
                "body": "{\"model\":\"gpt-4.1-mini\",\"messages\":[{\"role\":\"system\",\"content\":\"OpenClaw gateway agent\"},{\"role\":\"user\",\"content\":\"hi\"}]}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            88,
            "node".to_string(),
            json!({
                "tid": 8001,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"usage\":{\"prompt_tokens\":30,\"completion_tokens\":4}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();

        run_sql_adapters(&mut store, "openclaw").unwrap();
        let (agent_type, total): (String, i64) = store
            .connection()
            .query_row(
                "SELECT agent_type, total_tokens FROM agent_sessions WHERE agent_type = 'openclaw'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(agent_type, "openclaw");
        assert_eq!(total, 34);
    }

    #[test]
    fn failed_sql_adapter_records_failed_run() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let adapter = SqlAdapter {
            id: "bad",
            version: "0.1.0",
            adapter_type: "test",
            detect_sql: None,
            sql_files: &[(
                "bad.sql",
                "INSERT OR REPLACE INTO token_usage (id, missing_column) VALUES ('bad', 1);",
            )],
        };

        let err = adapter.run(&mut store).unwrap_err();
        assert!(err.to_string().contains("missing_column"));
        let (status, error_message): (String, Option<String>) = store
            .connection()
            .query_row(
                "SELECT status, error_message FROM adapter_runs WHERE adapter_id = 'bad'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(status, "failed");
        assert!(
            error_message
                .as_deref()
                .unwrap_or_default()
                .contains("missing_column")
        );
    }

    #[test]
    fn validation_failure_records_failed_run() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let adapter = SqlAdapter {
            id: "unsafe",
            version: "0.1.0",
            adapter_type: "test",
            detect_sql: None,
            sql_files: &[("unsafe.sql", "DROP TABLE raw_events;")],
        };

        let err = adapter.run(&mut store).unwrap_err();
        assert!(err.to_string().contains("forbidden"));
        let (status, error_message): (String, Option<String>) = store
            .connection()
            .query_row(
                "SELECT status, error_message FROM adapter_runs WHERE adapter_id = 'unsafe'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .unwrap();
        assert_eq!(status, "failed");
        assert!(
            error_message
                .as_deref()
                .unwrap_or_default()
                .contains("forbidden")
        );
    }
}
