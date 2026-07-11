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

"$ROOT_DIR/collector/target/debug/agentsight" top --plain --once >"$OUT_FILE"
cat "$OUT_FILE"

grep -q "AgentSight top" "$OUT_FILE"
grep -q "note: no eBPF: live kernel probes are Linux-only" "$OUT_FILE"
