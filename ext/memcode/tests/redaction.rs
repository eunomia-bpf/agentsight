use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::path::PathBuf;
use std::time::SystemTime;

use agent_session::{
    AgentSession, LiveProcessCandidate, ProcessKey, ProcessTree, SessionEvents,
    SessionProcessMatcher, TokenUsage,
};
use agentsight_memcode_correlation_example::{
    MemoryEvent, correlate, otel_attributes, write_sqlite,
};
use rusqlite::Connection;

const REQUEST: &str = "0123456789abcdef0123456789abcdef";

fn event(pid: u32, ticks: u64) -> MemoryEvent {
    MemoryEvent::parse(&format!(r#"{{"operation":"recall","duration_ms":12,"status":"ok","request_id":"{REQUEST}","pid":{pid},"starttime_ticks":{ticks}}}"#)).unwrap()
}

fn session() -> AgentSession {
    AgentSession {
        agent_type: "codex".into(),
        session_id: "private-session-name".into(),
        conversation_id: None,
        display_id: "private-display".into(),
        path: PathBuf::from("/synthetic/private-project/session.jsonl"),
        updated: SystemTime::now(),
        start_timestamp_ms: Some(1000),
        end_timestamp_ms: Some(2000),
        model: None,
        usage: TokenUsage::default(),
        model_usage: BTreeMap::new(),
        tools: BTreeMap::new(),
        files: BTreeMap::new(),
        prompt_preview: Some("PRIVATE_PROMPT_DO_NOT_EXPORT".into()),
        duration_ms: 1000,
        cwd: Some("/synthetic/private-project".into()),
        last_message_at: None,
        events: SessionEvents::default(),
    }
}

#[test]
fn sqlite_and_otel_never_contain_prompt_payload_paths_or_identity() {
    let key = ProcessKey {
        pid: 42,
        starttime_ticks: 7,
    };
    let child = ProcessKey {
        pid: 43,
        starttime_ticks: 8,
    };
    let process = LiveProcessCandidate {
        tree: ProcessTree {
            root: key,
            members: vec![key, child],
        },
        agent: "codex".into(),
        age_s: Some(1.),
        cwd: Some("/synthetic/private-project".into()),
    };
    let session = session();
    let fds = HashMap::from([(key, BTreeSet::from([session.path.clone()]))]);
    let rows = correlate(
        &mut SessionProcessMatcher::default(),
        &[event(43, 8)],
        &[session],
        &[process],
        &fds,
        &HashMap::new(),
        2000,
    );
    assert_eq!(rows.len(), 1);
    let mut db = Connection::open_in_memory().unwrap();
    write_sqlite(&mut db, &rows).unwrap();
    write_sqlite(&mut db, &rows).unwrap(); // opaque request ID is idempotent
    let count: u32 = db
        .query_row("SELECT COUNT(*) FROM memcode_operations", [], |r| r.get(0))
        .unwrap();
    assert_eq!(count, 1);
    let stored: String = db.query_row("SELECT request_id || operation || duration_ms || status || session_key || root_pid FROM memcode_operations", [], |r| r.get(0)).unwrap();
    let otel = otel_attributes(&rows[0]).to_string();
    for sink in [stored, otel] {
        assert!(sink.contains(REQUEST));
        for private in [
            "PRIVATE_PROMPT",
            "private-project",
            "private-display",
            "private-session-name",
            "payload",
            "user_id",
            "api_key",
        ] {
            assert!(!sink.contains(private), "private field leaked: {private}");
        }
    }
}

#[test]
fn pid_reuse_unmatched_processes_and_payload_fields_are_rejected() {
    let good = serde_json::json!({"operation":"save","duration_ms":3,"status":"ok",
        "request_id":REQUEST,"pid":42,"starttime_ticks":7});
    for field in ["payload", "prompt", "user_id", "space_id", "api_key"] {
        let mut bad = good.clone();
        bad[field] = serde_json::json!("private");
        assert!(MemoryEvent::parse(&bad.to_string()).is_err());
    }
    let key = ProcessKey {
        pid: 42,
        starttime_ticks: 9,
    };
    let process = LiveProcessCandidate {
        tree: ProcessTree {
            root: key,
            members: vec![key],
        },
        agent: "codex".into(),
        ..Default::default()
    };
    let s = session();
    let fds = HashMap::from([(key, BTreeSet::from([s.path.clone()]))]);
    assert!(
        correlate(
            &mut SessionProcessMatcher::default(),
            &[event(42, 7), event(99, 7)],
            &[s],
            &[process],
            &fds,
            &HashMap::new(),
            2000
        )
        .is_empty()
    );
    let mut bad = good;
    bad["request_id"] = serde_json::json!("private prompt");
    assert!(MemoryEvent::parse(&bad.to_string()).is_err());
}
