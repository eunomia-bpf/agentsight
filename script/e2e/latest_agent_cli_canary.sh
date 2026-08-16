#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

AGENTSIGHT_BIN="${AGENTSIGHT_BIN:-$REPO_ROOT/collector/target/debug/agentsight}"
WORK_DIR="${AGENTSIGHT_AGENT_CANARY_WORK_DIR:-$(mktemp -d -t agentsight-agent-canary.XXXXXX)}"
TOOLS_PREFIX="${AGENTSIGHT_AGENT_CANARY_TOOLS_PREFIX:-$WORK_DIR/npm-tools}"
MOCK_PORT="${AGENTSIGHT_AGENT_CANARY_PORT:-18443}"
PROMPT="${AGENTSIGHT_AGENT_CANARY_PROMPT:-agentsight mock prompt collect this exact text}"
REQUIRE_EBPF="${AGENTSIGHT_AGENT_CANARY_REQUIRE_EBPF:-1}"
BUILD_AGENTSIGHT="${AGENTSIGHT_AGENT_CANARY_BUILD:-1}"
AGENT_TIMEOUT="${AGENTSIGHT_AGENT_CANARY_AGENT_TIMEOUT:-60}"

MOCK_LOG="$WORK_DIR/mock-llm-requests.jsonl"
SERVER_STDOUT="$WORK_DIR/mock-llm-server.out"
SERVER_STDERR="$WORK_DIR/mock-llm-server.err"
TLS_CERT="$WORK_DIR/mock-llm.crt"
TLS_KEY="$WORK_DIR/mock-llm.key"
TLS_CA_CERT="$WORK_DIR/mock-llm-ca.crt"
TLS_CA_KEY="$WORK_DIR/mock-llm-ca.key"
SERVER_PID=""
CODEX_BIN=""
CLAUDE_BIN=""
OPENCODE_BIN=""

cleanup() {
    if [[ -n "$SERVER_PID" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

die() {
    echo "error: $*" >&2
    exit 1
}

have() {
    command -v "$1" >/dev/null 2>&1
}

is_enabled() {
    case "${1:-0}" in
        1|true|TRUE|yes|YES|on|ON) return 0 ;;
        *) return 1 ;;
    esac
}

sudo_available() {
    have sudo && sudo -n true >/dev/null 2>&1
}

build_agentsight() {
    if ! is_enabled "$BUILD_AGENTSIGHT"; then
        return
    fi

    make -C "$REPO_ROOT/bpf" sslsniff process stdiocap
    if [[ ! -f "$REPO_ROOT/frontend/dist/index.html" ]]; then
        npm --prefix "$REPO_ROOT/frontend" install
        npm --prefix "$REPO_ROOT/frontend" run build
    fi
    (cd "$REPO_ROOT/collector" && AGENTSIGHT_SYNC_VENDOR=1 cargo build)
}

install_latest_agent_clis() {
    have npm || die "npm is required to install latest Claude/Codex/OpenCode CLIs"

    mkdir -p "$TOOLS_PREFIX"
    npm install -g \
        --prefix "$TOOLS_PREFIX" \
        @openai/codex@latest \
        @anthropic-ai/claude-code@latest \
        opencode-ai@latest

    export PATH="$TOOLS_PREFIX/bin:$PATH"
    CODEX_BIN="$(command -v codex)"
    CLAUDE_BIN="$(command -v claude)"
    OPENCODE_BIN="$(command -v opencode)"

    echo "Installed agent CLI versions:"
    "$CODEX_BIN" -V
    "$CLAUDE_BIN" -v
    "$OPENCODE_BIN" --version
}

create_tls_cert() {
    have openssl || die "openssl is required to generate the local HTTPS certificate"

    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$TLS_CA_KEY" \
        -out "$TLS_CA_CERT" \
        -days 1 \
        -subj "/CN=AgentSight Mock LLM CA" \
        -addext "basicConstraints = critical, CA:TRUE" \
        -addext "keyUsage = critical, keyCertSign, cRLSign" >/dev/null 2>&1

    local csr="$WORK_DIR/mock-llm.csr"
    local ext="$WORK_DIR/mock-llm.ext"
    openssl req -newkey rsa:2048 -nodes \
        -keyout "$TLS_KEY" \
        -out "$csr" \
        -subj "/CN=127.0.0.1" >/dev/null 2>&1
    {
        echo "subjectAltName = IP:127.0.0.1,DNS:localhost"
        echo "basicConstraints = critical, CA:FALSE"
        echo "keyUsage = critical, digitalSignature, keyEncipherment"
        echo "extendedKeyUsage = serverAuth"
    } > "$ext"
    openssl x509 -req \
        -in "$csr" \
        -CA "$TLS_CA_CERT" \
        -CAkey "$TLS_CA_KEY" \
        -CAcreateserial \
        -out "$TLS_CERT" \
        -days 1 \
        -sha256 \
        -extfile "$ext" >/dev/null 2>&1
}

start_mock_server() {
    create_tls_cert
    python3 "$SCRIPT_DIR/mock_llm_server.py" \
        --host 127.0.0.1 \
        --port "$MOCK_PORT" \
        --tls-cert "$TLS_CERT" \
        --tls-key "$TLS_KEY" \
        --log "$MOCK_LOG" \
        --quiet >"$SERVER_STDOUT" 2>"$SERVER_STDERR" &
    SERVER_PID="$!"

    for _ in $(seq 1 50); do
        if python3 - "$MOCK_PORT" 2>/dev/null <<'PY'
import ssl
import sys
import urllib.request

port = sys.argv[1]
ctx = ssl._create_unverified_context()
try:
    urllib.request.urlopen(f"https://127.0.0.1:{port}/health", context=ctx, timeout=1).read()
except Exception:
    sys.exit(1)
PY
        then
            echo "Mock LLM server: https://127.0.0.1:$MOCK_PORT"
            return
        fi
        sleep 0.1
    done

    echo "mock server stdout:" >&2
    sed -n '1,80p' "$SERVER_STDOUT" >&2 || true
    echo "mock server stderr:" >&2
    sed -n '1,80p' "$SERVER_STDERR" >&2 || true
    die "mock LLM server did not become healthy"
}

run_mock_client_record_smoke() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        if is_enabled "$REQUIRE_EBPF"; then
            die "record/sslsniff canary requires Linux"
        fi
        echo "Skipping record/sslsniff canary on non-Linux host"
        return
    fi
    if ! sudo_available; then
        if is_enabled "$REQUIRE_EBPF"; then
            die "record/sslsniff canary requires passwordless sudo"
        fi
        echo "Skipping record/sslsniff canary because sudo -n is unavailable"
        return
    fi

    local db="$WORK_DIR/mock-record.db"
    local prompts="$WORK_DIR/mock-prompts.json"
    local summary="$WORK_DIR/mock-summary.out"
    local url="https://127.0.0.1:$MOCK_PORT/v1/chat/completions"
    local prompt_json
    local payload

    if ! have curl; then
        if is_enabled "$REQUIRE_EBPF"; then
            die "record/sslsniff canary requires curl"
        fi
        echo "Skipping record/sslsniff canary because curl is unavailable"
        return
    fi

    prompt_json="$(python3 -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$PROMPT")"
    payload="{\"model\":\"gpt-agentsight-mock\",\"messages\":[{\"role\":\"user\",\"content\":$prompt_json}]}"

    sudo -n env \
        PATH="$PATH" \
        HOME="$HOME" \
        "$AGENTSIGHT_BIN" record --no-server --db "$db" -- \
        curl --http1.1 -sS --cacert "$TLS_CA_CERT" "$url" \
            -H "content-type: application/json" \
            -H "authorization: Bearer agentsight-test" \
            --data "$payload"

    "$AGENTSIGHT_BIN" report prompts --db "$db" --json > "$prompts"
    grep -Fq "$PROMPT" "$prompts"

    "$AGENTSIGHT_BIN" report --db "$db" > "$summary"
    grep -Eq "[1-9][0-9]* API calls" "$summary"

    grep -Fq "$PROMPT" "$MOCK_LOG"
    echo "record/sslsniff mock canary captured prompt into $db"
}

codex_native_binary() {
    find "$TOOLS_PREFIX" \
        -path '*/node_modules/@openai/codex-linux-*/vendor/*/bin/codex' \
        -type f \
        -perm /111 \
        -print \
        -quit
}

run_codex_offset_canary() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        if is_enabled "$REQUIRE_EBPF"; then
            die "Codex signature canary requires Linux"
        fi
        echo "Skipping Codex signature canary on non-Linux host"
        return
    fi
    if ! sudo_available; then
        if is_enabled "$REQUIRE_EBPF"; then
            die "Codex signature canary requires passwordless sudo"
        fi
        echo "Skipping Codex signature canary because sudo -n is unavailable"
        return
    fi
    have timeout || die "timeout is required for the Codex signature canary"

    local native
    local stdout="$WORK_DIR/codex-sslsniff-offset.out"
    local stderr="$WORK_DIR/codex-sslsniff-offset.err"
    local status

    native="$(codex_native_binary)"
    [[ -n "$native" ]] || die "could not find latest Codex native binary under $TOOLS_PREFIX"

    set +e
    sudo -n timeout --foreground --signal=INT 5s \
        "$REPO_ROOT/bpf/sslsniff" --binary-path "$native" \
        >"$stdout" 2>"$stderr"
    status=$?
    set -e

    if ! grep -Fq "Codex/rustls plaintext write patterns detected" "$stderr" \
        || ! grep -Eq "Attaching [1-9][0-9]* offsets" "$stderr"; then
        echo "Codex sslsniff output did not prove signature attachment" >&2
        sed -n '1,160p' "$stderr" >&2 || true
        return 1
    fi
    if grep -Fq "binary-path attach failed" "$stderr"; then
        echo "Codex sslsniff signature attachment failed" >&2
        sed -n '1,160p' "$stderr" >&2 || true
        return 1
    fi
    case "$status" in
        0|124|130) ;;
        *)
            echo "Codex sslsniff signature canary exited with status $status" >&2
            sed -n '1,160p' "$stderr" >&2 || true
            return 1
            ;;
    esac

    echo "sslsniff Codex signature canary matched latest native binary: $native"
}

assert_codex_ssl_prompt() {
    local db="$1"

    python3 - "$db" "$PROMPT" <<'PY'
import sqlite3
import sys

db, prompt = sys.argv[1:]
match = sqlite3.connect(db).execute(
    "SELECT 1 FROM llm_calls WHERE path = '/v1/responses' "
    "AND instr(request_body_json, ?) > 0 AND EXISTS (SELECT 1 FROM audit_events "
    "WHERE audit_type = 'llm' AND action = 'request' AND instr(details_json, ?) > 0)",
    (prompt, prompt),
).fetchone()
if not match:
    raise SystemExit("Codex prompt was not reconstructed from SSL /v1/responses traffic")
print("Codex SSL /v1/responses request contains the exact canary prompt")
PY
}

write_opencode_config() {
    local config_dir="$1"
    mkdir -p "$config_dir"
    cat > "$config_dir/opencode.json" <<EOF
{
  "\$schema": "https://opencode.ai/config.json",
  "enabled_providers": ["agentsight-mock"],
  "model": "agentsight-mock/gpt-agentsight-mock",
  "small_model": "agentsight-mock/gpt-agentsight-mock",
  "agent": {
    "build": {
      "model": "agentsight-mock/gpt-agentsight-mock",
      "steps": 1
    },
    "title": {
      "model": "agentsight-mock/gpt-agentsight-mock"
    }
  },
  "provider": {
    "agentsight-mock": {
      "name": "AgentSight Mock",
      "env": ["OPENAI_API_KEY"],
      "npm": "@ai-sdk/openai",
      "api": "https://127.0.0.1:$MOCK_PORT/v1",
      "models": {
        "gpt-agentsight-mock": {
          "id": "gpt-agentsight-mock",
          "name": "AgentSight Mock",
          "tool_call": true,
          "temperature": true,
          "limit": {"context": 128000, "output": 4096},
          "cost": {"input": 0, "output": 0},
          "modalities": {"input": ["text"], "output": ["text"]},
          "status": "active"
        }
      }
    }
  }
}
EOF
}

record_real_agent() {
    local name="$1"
    shift
    local db="$WORK_DIR/$name.db"
    local prompts="$WORK_DIR/$name-prompts.json"
    local summary="$WORK_DIR/$name-summary.out"
    local record_log="$WORK_DIR/$name-record.log"
    local opencode_config="$WORK_DIR/$name-opencode-config"
    local agent_work="$WORK_DIR/$name-work"
    local recent_mock_requests="$WORK_DIR/$name-mock-requests.jsonl"
    local mock_before
    local mock_after

    mkdir -p "$WORK_DIR/$name-home" "$WORK_DIR/$name-codex-home" "$agent_work"
    write_opencode_config "$opencode_config"
    mock_before="$(wc -l < "$MOCK_LOG")"

    if ! (
        cd "$agent_work"
        sudo -n env \
            PATH="$PATH" \
            HOME="$WORK_DIR/$name-home" \
            OPENAI_API_KEY=agentsight-test \
            OPENAI_BASE_URL="https://127.0.0.1:$MOCK_PORT/v1" \
            ANTHROPIC_API_KEY=agentsight-test \
            ANTHROPIC_BASE_URL="https://127.0.0.1:$MOCK_PORT" \
            SSL_CERT_FILE="$TLS_CA_CERT" \
            REQUESTS_CA_BUNDLE="$TLS_CA_CERT" \
            NODE_EXTRA_CA_CERTS="$TLS_CA_CERT" \
            NODE_TLS_REJECT_UNAUTHORIZED=0 \
            CODEX_HOME="$WORK_DIR/$name-codex-home" \
            OPENCODE_CONFIG_DIR="$opencode_config" \
            OPENCODE_DISABLE_PROJECT_CONFIG=1 \
            OPENCODE_DISABLE_MODELS_FETCH=1 \
            timeout --foreground --signal=INT "${AGENT_TIMEOUT}s" \
            "$AGENTSIGHT_BIN" record --no-server --db "$db" -- "$@" < /dev/null
    ) > "$record_log" 2>&1; then
        sed -n '1,240p' "$record_log" >&2 || true
        return 1
    fi

    mock_after="$(wc -l < "$MOCK_LOG")"
    if ((mock_after <= mock_before)); then
        echo "$name did not send a new request to the mock LLM server" >&2
        sed -n '1,240p' "$record_log" >&2 || true
        return 1
    fi
    tail -n "$((mock_after - mock_before))" "$MOCK_LOG" > "$recent_mock_requests"
    if ! grep -Fq "$PROMPT" "$recent_mock_requests"; then
        echo "$name mock LLM requests did not contain the canary prompt" >&2
        sed -n '1,40p' "$recent_mock_requests" >&2 || true
        return 1
    fi
    if [[ "$name" == "codex" ]] && ! assert_codex_ssl_prompt "$db"; then
        sed -n '1,240p' "$record_log" >&2 || true
        return 1
    fi

    "$AGENTSIGHT_BIN" report prompts --db "$db" --json > "$prompts"
    if ! grep -Fq "$PROMPT" "$prompts"; then
        echo "$name report prompts did not contain the canary prompt" >&2
        sed -n '1,240p' "$record_log" >&2 || true
        sed -n '1,240p' "$prompts" >&2 || true
        return 1
    fi

    "$AGENTSIGHT_BIN" report --db "$db" > "$summary"
    if ! grep -Eq "[1-9][0-9]* API calls" "$summary"; then
        echo "$name report did not show any API calls" >&2
        sed -n '1,120p' "$summary" >&2 || true
        return 1
    fi

    echo "$name real-agent canary captured prompt into $db"
}

run_real_agent_mock_canary() {
    if ! sudo_available; then
        die "real agent canary requires passwordless sudo"
    fi

    local failures=()

    if ! record_real_agent codex \
        "$CODEX_BIN" exec --skip-git-repo-check --ignore-user-config \
        -c "model_provider=\"agentsight-mock\"" \
        -c "model_providers.agentsight-mock.name=\"AgentSight Mock\"" \
        -c "model_providers.agentsight-mock.base_url=\"https://127.0.0.1:$MOCK_PORT/v1\"" \
        -c "model_providers.agentsight-mock.env_key=\"OPENAI_API_KEY\"" \
        -c "model_providers.agentsight-mock.wire_api=\"responses\"" \
        -c "model_providers.agentsight-mock.supports_websockets=false" \
        -c "model_providers.agentsight-mock.request_max_retries=0" \
        --sandbox read-only \
        --model gpt-agentsight-mock "$PROMPT"; then
        failures+=("codex")
    fi

    if ! record_real_agent claude \
        "$CLAUDE_BIN" --bare -p "$PROMPT" --output-format json \
        --model claude-agentsight-mock; then
        failures+=("claude")
    fi

    local opencode_command=(
        "$OPENCODE_BIN" run --pure --model agentsight-mock/gpt-agentsight-mock
        --format json "$PROMPT"
    )
    if ! record_real_agent opencode "${opencode_command[@]}"; then
        # OpenCode's mock invocation is a single-request, roughly three-second
        # process. An occasional scheduler race can let it exit before the
        # BoringSSL offset probe emits its first event even though the mock
        # server received the exact request. Retry once so this canary still
        # fails persistent binary-signature regressions without blocking a
        # release on one short-process sampling miss.
        echo "Retrying OpenCode capture after a short-process sampling miss" >&2
        if ! record_real_agent opencode "${opencode_command[@]}"; then
            failures+=("opencode")
        fi
    fi

    if ((${#failures[@]} > 0)); then
        die "real agent canary failed for: ${failures[*]}"
    fi
}

main() {
    [[ "$AGENT_TIMEOUT" =~ ^[1-9][0-9]*$ ]] \
        || die "AGENTSIGHT_AGENT_CANARY_AGENT_TIMEOUT must be a positive integer"
    have timeout || die "timeout is required for the real agent canary"
    mkdir -p "$WORK_DIR"
    build_agentsight
    install_latest_agent_clis
    start_mock_server
    run_mock_client_record_smoke
    run_codex_offset_canary
    run_real_agent_mock_canary

    echo "canary work dir: $WORK_DIR"
}

main "$@"
