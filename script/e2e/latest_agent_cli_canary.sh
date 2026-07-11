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
REAL_AGENT="${AGENTSIGHT_AGENT_CANARY_REAL_AGENT:-0}"
REQUIRE_EBPF="${AGENTSIGHT_AGENT_CANARY_REQUIRE_EBPF:-0}"

MOCK_LOG="$WORK_DIR/mock-llm-requests.jsonl"
SERVER_STDOUT="$WORK_DIR/mock-llm-server.out"
SERVER_STDERR="$WORK_DIR/mock-llm-server.err"
TLS_CERT="$WORK_DIR/mock-llm.crt"
TLS_KEY="$WORK_DIR/mock-llm.key"
TLS_CA_CERT="$WORK_DIR/mock-llm-ca.crt"
TLS_CA_KEY="$WORK_DIR/mock-llm-ca.key"
SERVER_PID=""

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

build_agentsight_if_needed() {
    if [[ -x "$AGENTSIGHT_BIN" ]]; then
        return
    fi
    (cd "$REPO_ROOT/collector" && cargo build)
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
    echo "Installed agent CLI versions:"
    codex -V
    claude -v
    opencode --version
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

run_top_and_agent_session_smoke() {
    AGENTSIGHT_BIN="$AGENTSIGHT_BIN" "$REPO_ROOT/script/ci/top_fixture_smoke.sh"
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
    local top="$WORK_DIR/mock-top.out"
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

    "$AGENTSIGHT_BIN" report prompts --db "$db" --json | tee "$prompts"
    grep -Fq "$PROMPT" "$prompts"

    "$AGENTSIGHT_BIN" top --db "$db" --once --plain --limit 20 | tee "$top"
    grep -Fq "AgentSight top -" "$top"

    grep -Fq "$PROMPT" "$MOCK_LOG"
    echo "record/sslsniff mock canary captured prompt into $db"
}

record_real_agent() {
    local name="$1"
    shift
    local db="$WORK_DIR/$name.db"
    local prompts="$WORK_DIR/$name-prompts.json"

    mkdir -p "$WORK_DIR/$name-home" "$WORK_DIR/$name-codex-home"

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
        "$AGENTSIGHT_BIN" record --no-server --db "$db" -- "$@"

    "$AGENTSIGHT_BIN" report prompts --db "$db" --json | tee "$prompts"
    grep -Fq "$PROMPT" "$prompts"
}

run_real_agent_mock_canary() {
    if ! sudo_available; then
        die "real agent canary requires passwordless sudo"
    fi

    local failures=()

    if ! record_real_agent codex \
        codex exec --skip-git-repo-check --ignore-user-config \
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
        claude --bare -p "$PROMPT" --output-format json \
        --model claude-agentsight-mock; then
        failures+=("claude")
    fi

    if ! record_real_agent opencode \
        opencode run --pure --model openai/gpt-agentsight-mock \
        --format json "$PROMPT"; then
        failures+=("opencode")
    fi

    if ((${#failures[@]} > 0)); then
        die "real agent canary failed for: ${failures[*]}"
    fi
}

main() {
    mkdir -p "$WORK_DIR"
    build_agentsight_if_needed
    install_latest_agent_clis
    start_mock_server
    run_top_and_agent_session_smoke
    run_mock_client_record_smoke

    if is_enabled "$REAL_AGENT"; then
        run_real_agent_mock_canary
    else
        echo "Set AGENTSIGHT_AGENT_CANARY_REAL_AGENT=1 to also run latest Claude/Codex/OpenCode against the mock server."
    fi

    echo "canary work dir: $WORK_DIR"
}

main "$@"
