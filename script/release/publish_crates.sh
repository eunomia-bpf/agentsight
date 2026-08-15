#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: publish_crates.sh RELEASE_VERSION SESSION_VERSION" >&2
  exit 2
fi

VERSION="$1"
SESSION_VERSION="$2"
CRATES_IO_USER_AGENT="agentsight-release-ci (${GITHUB_SERVER_URL:-local}/${GITHUB_REPOSITORY:-eunomia-bpf/agentsight}; run ${GITHUB_RUN_ID:-manual})"

if [[ -z "${CARGO_REGISTRY_TOKEN:-}" ]]; then
  echo "CARGO_REGISTRY_TOKEN is not set" >&2
  exit 1
fi

exists() {
  local crate="$1" version="$2" status
  status="$(curl --retry 3 --retry-delay 2 -A "$CRATES_IO_USER_AGENT" -sS -o /dev/null -w '%{http_code}' \
    "https://crates.io/api/v1/crates/${crate}/${version}" || true)"
  case "$status" in
    200) return 0 ;;
    404) return 1 ;;
    *) echo "crates.io returned HTTP ${status} for ${crate} ${version}" >&2; exit 1 ;;
  esac
}

publish_one() {
  local crate="$1" manifest="$2" version="$3"
  if exists "$crate" "$version"; then
    echo "$crate $version already exists; skipping"
    return
  fi
  CARGO_TARGET_DIR="/tmp/agentsight-package-${crate}" cargo package --manifest-path "$manifest"
  cargo publish --manifest-path "$manifest"
  for attempt in 1 2 3 4 5 6; do
    if exists "$crate" "$version"; then
      return
    fi
    sleep $((attempt * 10))
  done
  echo "$crate $version was not visible after publish" >&2
  exit 1
}

# Dependency order matters for crates.io resolution of path dependencies.
publish_one agent-session          ext/session/Cargo.toml          "$SESSION_VERSION"
publish_one agentsight-capture     agentsight-capture/Cargo.toml   "$VERSION"
publish_one agentsight-ext-runtime ext/runtime/Cargo.toml          "$VERSION"
publish_one agentsight-analysis    ext/analysis/Cargo.toml         "$VERSION"
publish_one agentvis               ext/vis/Cargo.toml              "$VERSION"
publish_one agentpprof             ext/pprof/Cargo.toml            "$VERSION"
publish_one agentsight             collector/Cargo.toml            "$VERSION"
