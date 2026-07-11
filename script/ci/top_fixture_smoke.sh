#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 eunomia-bpf org.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

AGENTSIGHT_BIN="${AGENTSIGHT_BIN:-$REPO_ROOT/collector/target/debug/agentsight}"
FIXTURE_HOME="${AGENTSIGHT_TOP_FIXTURE_HOME:-$REPO_ROOT/script/fixtures/top-home}"
OUT="${AGENTSIGHT_TOP_SMOKE_OUT:-$(mktemp -t agentsight-top-smoke.XXXXXX)}"
REPORT_OUT="${AGENTSIGHT_LOCAL_REPORT_OUT:-$(mktemp -t agentsight-local-report.XXXXXX)}"

if [[ ! -x "$AGENTSIGHT_BIN" ]]; then
    echo "agentsight binary is not executable: $AGENTSIGHT_BIN" >&2
    echo "Build it first, for example: cd collector && cargo build" >&2
    exit 1
fi

if [[ ! -d "$FIXTURE_HOME" ]]; then
    echo "fixture HOME does not exist: $FIXTURE_HOME" >&2
    exit 1
fi

unset SUDO_USER
HOME="$FIXTURE_HOME" PATH=/nonexistent "$AGENTSIGHT_BIN" top --once --plain --limit 20 | tee "$OUT"

grep -Fq "AgentSight top -" "$OUT"
grep -Fq "codex:ci-codex" "$OUT"
grep -Fq "claude:ci-claude" "$OUT"
grep -Fq "gemini:ci-gemini" "$OUT"
grep -Fq "gpt-ci-codex" "$OUT"
grep -Fq "claude-ci" "$OUT"
grep -Fq "gemini-ci" "$OUT"
grep -Fq "portable top codex fixture" "$OUT"
grep -Fq "portable top claude fixture" "$OUT"
grep -Fq "portable top gemini fixture" "$OUT"
grep -Fq "live eBPF capture requires sudo" "$OUT"

HOME="$FIXTURE_HOME" "$AGENTSIGHT_BIN" report --local | tee "$REPORT_OUT"
grep -Fq "agent_native_session session" "$REPORT_OUT"
grep -Fq "gpt-ci-codex" "$REPORT_OUT"
grep -Fq "claude-ci" "$REPORT_OUT"
grep -Fq "gemini-ci" "$REPORT_OUT"
grep -Fq "15 tokens" "$REPORT_OUT"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
        echo "### AgentSight top fixture smoke"
        echo '```'
        sed -n '1,80p' "$OUT"
        echo '```'
        echo "### AgentSight local session report smoke"
        echo '```'
        sed -n '1,80p' "$REPORT_OUT"
        echo '```'
    } >> "$GITHUB_STEP_SUMMARY"
fi
