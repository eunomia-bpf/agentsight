#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_FILE="${1:-$ROOT_DIR/.artifacts/macos-top-output.txt}"
LIVE_OUT_FILE="${OUT_FILE%.txt}-live.txt"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "macos_top_smoke.sh requires macOS" >&2
    exit 2
fi

mkdir -p "$(dirname "$OUT_FILE")"

cargo build --manifest-path "$ROOT_DIR/collector/Cargo.toml" --verbose

TMP_ROOT="$(mktemp -d)"
AGENT_PID=""
cleanup() {
    if [[ -n "$AGENT_PID" ]]; then
        kill "$AGENT_PID" 2>/dev/null || true
        wait "$AGENT_PID" 2>/dev/null || true
    fi
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

FIXTURE_HOME="$TMP_ROOT/home"
WORK_DIR="$TMP_ROOT/work"
BIN_DIR="$TMP_ROOT/bin"
SESSION_PATH="$FIXTURE_HOME/.codex/sessions/2026/07/12/macos-ci.jsonl"
mkdir -p "$(dirname "$SESSION_PATH")" "$WORK_DIR" "$BIN_DIR"
SESSION_REAL_PATH="$(cd "$(dirname "$SESSION_PATH")" && pwd -P)/$(basename "$SESSION_PATH")"
SESSION_TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
SESSION_LAST_MSG="$(date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$SESSION_TS" '+%H:%M:%S')"
LSOF_BIN="/usr/sbin/lsof"
if [[ ! -x "$LSOF_BIN" ]]; then
    LSOF_BIN="$(command -v lsof || true)"
fi
if [[ -z "$LSOF_BIN" ]]; then
    echo "lsof not found; macOS session fd binding cannot be tested" >&2
    exit 1
fi

cat >"$SESSION_PATH" <<EOF
{"timestamp":"$SESSION_TS","type":"turn_context","payload":{"model":"gpt-macos-ci","cwd":"$WORK_DIR"}}
{"timestamp":"$SESSION_TS","type":"event_msg","payload":{"type":"user_message","message":"macos top token check"}}
{"timestamp":"$SESSION_TS","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":11,"output_tokens":4,"total_tokens":15}}}}
EOF

cat >"$BIN_DIR/codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec 3<"$AGENTSIGHT_SESSION_PATH"
sleep "${AGENTSIGHT_SLEEP_SECS:-30}"
EOF
chmod +x "$BIN_DIR/codex"

(
    cd "$WORK_DIR"
    AGENTSIGHT_SESSION_PATH="$SESSION_PATH" AGENTSIGHT_SLEEP_SECS=30 "$BIN_DIR/codex"
) &
AGENT_PID=$!

for _ in {1..20}; do
    if ps -p "$AGENT_PID" >/dev/null 2>&1 &&
        "$LSOF_BIN" -nP -Fn -p "$AGENT_PID" 2>/dev/null | grep -Fqx "n$SESSION_REAL_PATH"; then
        break
    fi
    sleep 0.25
done

if ! "$LSOF_BIN" -nP -Fn -p "$AGENT_PID" 2>/dev/null | grep -Fqx "n$SESSION_REAL_PATH"; then
    echo "mock codex process did not open expected session fd: $SESSION_REAL_PATH" >&2
    "$LSOF_BIN" -nP -Fn -p "$AGENT_PID" >&2 || true
    exit 1
fi

HOME="$FIXTURE_HOME" TZ=UTC "$ROOT_DIR/collector/target/debug/agentsight" top --plain --count 1 -c codex --limit 20 >"$LIVE_OUT_FILE"
cat "$LIVE_OUT_FILE"

grep -q "AgentSight top" "$LIVE_OUT_FILE"
grep -q "codex:macos-ci" "$LIVE_OUT_FILE"
grep -Eq "codex:macos-ci[[:space:]]+codex[[:space:]]+live" "$LIVE_OUT_FILE"
grep -q "session tokens: 15" "$LIVE_OUT_FILE"
grep -q "gpt-macos-ci" "$LIVE_OUT_FILE"
grep -q "$SESSION_LAST_MSG" "$LIVE_OUT_FILE"
grep -q "macos top token check" "$LIVE_OUT_FILE"
grep -q "matching session path" "$LIVE_OUT_FILE"

HOME="$FIXTURE_HOME" TZ=UTC "$ROOT_DIR/collector/target/debug/agentsight" top --plain --once -c codex --limit 20 >"$OUT_FILE"
cat "$OUT_FILE"

grep -q "AgentSight top" "$OUT_FILE"
if grep -Eiq "eBPF|sudo|kernel probes|Linux-only" "$OUT_FILE"; then
    echo "plain top unexpectedly mentioned live backend/probe state" >&2
    exit 1
fi
grep -q "codex:macos-ci" "$OUT_FILE"
grep -Eq "codex:macos-ci[[:space:]]+codex[[:space:]]+history" "$OUT_FILE"
grep -q "session tokens: 15" "$OUT_FILE"
grep -q "gpt-macos-ci" "$OUT_FILE"
grep -q "$SESSION_LAST_MSG" "$OUT_FILE"
grep -q "macos top token check" "$OUT_FILE"
grep -q "agent-native once view; no process scan" "$OUT_FILE"
