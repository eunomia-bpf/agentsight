#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_FILE="${1:-$ROOT_DIR/.artifacts/macos-top-output.txt}"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "macos_top_smoke.sh requires macOS" >&2
    exit 2
fi

mkdir -p "$(dirname "$OUT_FILE")"

cargo build --manifest-path "$ROOT_DIR/collector/Cargo.toml" --verbose

TMP_ROOT="$(mktemp -d)"
AGENT_PID=""
SERVER_PID=""
cleanup() {
    if [[ -n "$AGENT_PID" ]]; then
        kill -CONT "$AGENT_PID" 2>/dev/null || true
        pkill -CONT -P "$AGENT_PID" 2>/dev/null || true
        pkill -TERM -P "$AGENT_PID" 2>/dev/null || true
        kill "$AGENT_PID" 2>/dev/null || true
        wait "$AGENT_PID" 2>/dev/null || true
    fi
    if [[ -n "$SERVER_PID" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

AGENT_HOME="$TMP_ROOT/home"
WORK_DIR="$TMP_ROOT/work"
TOOLS_DIR="$TMP_ROOT/tools"
MOCK_LOG="$TMP_ROOT/mock-requests.jsonl"
MOCK_PORT=18445
PROMPT="agentsight macos live token check"
mkdir -p "$AGENT_HOME/.codex" "$WORK_DIR" "$TOOLS_DIR"

npm install -g --prefix "$TOOLS_DIR" @openai/codex@latest
CODEX_BIN="$TOOLS_DIR/bin/codex"
"$CODEX_BIN" --version

python3 "$ROOT_DIR/script/e2e/mock_llm_server.py" \
    --port "$MOCK_PORT" --log "$MOCK_LOG" --quiet \
    >"$TMP_ROOT/mock-server.out" 2>"$TMP_ROOT/mock-server.err" &
SERVER_PID=$!
for _ in {1..50}; do
    if curl -fsS "http://127.0.0.1:$MOCK_PORT/health" >/dev/null 2>&1; then
        break
    fi
    sleep 0.1
done
curl -fsS "http://127.0.0.1:$MOCK_PORT/health" >/dev/null

(
    cd "$WORK_DIR"
    exec env HOME="$AGENT_HOME" CODEX_HOME="$AGENT_HOME/.codex" \
        OPENAI_API_KEY=agentsight-test \
        "$CODEX_BIN" exec --skip-git-repo-check --ignore-user-config \
        -c 'model_provider="agentsight-mock"' \
        -c 'model_providers.agentsight-mock.name="AgentSight Mock"' \
        -c "model_providers.agentsight-mock.base_url=\"http://127.0.0.1:$MOCK_PORT/v1\"" \
        -c 'model_providers.agentsight-mock.env_key="OPENAI_API_KEY"' \
        -c 'model_providers.agentsight-mock.wire_api="responses"' \
        -c 'model_providers.agentsight-mock.supports_websockets=false' \
        -c 'model_providers.agentsight-mock.request_max_retries=0' \
        --sandbox read-only --model gpt-agentsight-mock "$PROMPT"
) &
AGENT_PID=$!

for _ in {1..1000}; do
    if ps -p "$AGENT_PID" >/dev/null 2>&1 && \
        grep -Rqs '"total_tokens":15' "$AGENT_HOME/.codex/sessions" 2>/dev/null; then
        break
    fi
    sleep 0.01
done

if ! ps -p "$AGENT_PID" >/dev/null 2>&1 || \
    ! grep -Rqs '"total_tokens":15' "$AGENT_HOME/.codex/sessions" 2>/dev/null; then
    echo "latest Codex did not record the expected token usage" >&2
    cat "$TMP_ROOT/mock-server.err" >&2 || true
    exit 1
fi
kill -STOP "$AGENT_PID"
pkill -STOP -P "$AGENT_PID" 2>/dev/null || true

HOME="$AGENT_HOME" TZ=UTC "$ROOT_DIR/collector/target/debug/agentsight" top --plain --once -p "$AGENT_PID" --limit 20 >"$OUT_FILE"
cat "$OUT_FILE"

grep -q "AgentSight top" "$OUT_FILE"
grep -q "live kernel probes are Linux-only" "$OUT_FILE"
grep -Eq "codex:.*[[:space:]]+codex[[:space:]]+live" "$OUT_FILE"
grep -q "session tokens: 15" "$OUT_FILE"
grep -q "gpt-agentsight-" "$OUT_FILE"
grep -Eq '[[:space:]][0-9]{2}:[0-9]{2}:[0-9]{2}[[:space:]]+gpt-agentsight-' "$OUT_FILE"
grep -q "$PROMPT" "$OUT_FILE"
grep -q "proc evidence uses process snapshots" "$OUT_FILE"
grep -q "$PROMPT" "$MOCK_LOG"
