#!/usr/bin/env python3
"""Update AgentSight distribution/ext versions without duplicated CI sed rules."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PACKAGE_VERSIONS = {
    "collector/Cargo.toml": "release",
    "agentsight-capture/Cargo.toml": "release",
    "agentsight-protocol/Cargo.toml": "release",
    "compat/agentsight-capture/Cargo.toml": "release",
    "ext/analysis/Cargo.toml": "release",
    "ext/runtime/Cargo.toml": "release",
    "ext/vis/Cargo.toml": "release",
    "ext/pprof/Cargo.toml": "release",
    "ext/session/Cargo.toml": "session",
}

EXTENSION_VERSIONS = {
    "ext/analysis/ext.toml": "release",
    "ext/runtime/ext.toml": "release",
    "ext/web/ext.toml": "release",
}

DEPENDENCIES = {
    "agentsight-capture/Cargo.toml": {"agent-session": "session"},
    "compat/agentsight-capture/Cargo.toml": {"agentsight-analysis": "release"},
    "ext/analysis/Cargo.toml": {
        "agentsight-capture-core": "release",
        "agent-session": "session",
    },
    "ext/vis/Cargo.toml": {"agent-session": "session"},
    "ext/pprof/Cargo.toml": {"agent-session": "session"},
    "collector/Cargo.toml": {
        "agentsight-capture": "release",
        "agentsight-protocol": "release",
        "agent-session": "session",
        "agentvis": "release",
    },
}


def replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"could not update {label}")
    return updated


def replace_all(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count < 1:
        raise SystemExit(f"could not update {label}")
    return updated


def update_manifest(path: Path, release: str, session: str) -> None:
    relative = path.relative_to(ROOT).as_posix()
    text = path.read_text()
    version = release if PACKAGE_VERSIONS[relative] == "release" else session
    text = replace_once(
        text,
        r'^(version\s*=\s*")[^"]+("\s*)$',
        rf'\g<1>{version}\2',
        f"package version in {relative}",
    )
    for dependency, kind in DEPENDENCIES.get(relative, {}).items():
        dep_version = release if kind == "release" else session
        pattern = rf'^({re.escape(dependency)}\s*=\s*\{{[^\n]*?version\s*=\s*")[^"]+("[^\n]*\}}\s*)$'
        text = replace_all(
            text,
            pattern,
            rf'\g<1>{dep_version}\2',
            f"{dependency} version in {relative}",
        )
    path.write_text(text)


def update_extension_metadata(path: Path, release: str, session: str) -> None:
    relative = path.relative_to(ROOT).as_posix()
    text = path.read_text()
    version = release if EXTENSION_VERSIONS[relative] == "release" else session
    text = replace_once(
        text,
        r'^(version\s*=\s*")[^"]+("\s*)$',
        rf'\g<1>{version}\2',
        f"extension version in {relative}",
    )
    path.write_text(text)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: set_versions.py RELEASE_VERSION SESSION_VERSION")
    release, session = sys.argv[1:]
    if not re.fullmatch(r"\d+\.\d+\.\d+", release) or not re.fullmatch(r"\d+\.\d+\.\d+", session):
        raise SystemExit("versions must be semver patch versions")
    for relative in PACKAGE_VERSIONS:
        update_manifest(ROOT / relative, release, session)
    for relative in EXTENSION_VERSIONS:
        update_extension_metadata(ROOT / relative, release, session)


if __name__ == "__main__":
    main()
