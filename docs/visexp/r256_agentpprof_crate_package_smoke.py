#!/usr/bin/env python3
"""R256: agentpprof crate package smoke.

R248/R253/R254 verify installed CLI paths. R256 verifies the crates-package
boundary: `cargo package --list` includes only the intended package files, and
`cargo package` can verify the crate with registry-resolved dependencies. It is
not a crates.io publish, external-machine install, user study, or tag-adequacy
result.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import r248_agentpprof_install_smoke as r248


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
RUN_ID = "R256"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "agentpprof-crate-package-r256"
MANIFEST = REPO_ROOT / "agentpprof/Cargo.toml"
PACKAGE_NAME = "agentpprof"
PACKAGE_VERSION = "0.2.0"
CRATE_FILE = f"{PACKAGE_NAME}-{PACKAGE_VERSION}.crate"

REQUIRED_PACKAGE_FILES = {
    ".cargo_vcs_info.json",
    "Cargo.lock",
    "Cargo.toml",
    "Cargo.toml.orig",
    "README.md",
    "examples/README.md",
    "examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl",
    "src/main.rs",
}

FORBIDDEN_PACKAGE_PATTERNS = [
    re.compile(r"(^|/)target(/|$)"),
    re.compile(r"(^|/)docs/visexp/out(/|$)"),
    re.compile(r"(^|/)\.agentsight(/|$)"),
    re.compile(r"(^|/)\.codex(/|$)"),
    re.compile(r"(^|/)\.claude(/|$)"),
    re.compile(r"(^|/)collector(/|$)"),
    re.compile(r"(^|/)frontend(/|$)"),
    re.compile(r"(^|/)bpf(/|$)"),
]

FORBIDDEN_SUMMARY_PATTERNS = [
    re.compile(r"/tmp/[^\s,;\"'<>)]*"),
    re.compile(r"/var/tmp/[^\s,;\"'<>)]*"),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return r248.rel(path)


def git(args: list[str]) -> str | None:
    return r248.git(args)


def write_json(path: Path, payload: Any) -> None:
    r248.write_json(path, payload)


def sanitize_text(text: str, tmp_root: Path | None = None) -> str:
    sanitized = r248.sanitize_text(text)
    if tmp_root is not None:
        sanitized = sanitized.replace(str(tmp_root), "<tmp-r256>")
    for pattern in FORBIDDEN_SUMMARY_PATTERNS:
        sanitized = pattern.sub("<redacted-path>", sanitized)
    return sanitized


def package_files_from_list(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def crate_archive_files(crate_path: Path) -> list[str]:
    prefix = f"{PACKAGE_NAME}-{PACKAGE_VERSION}/"
    files: list[str] = []
    with tarfile.open(crate_path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            name = member.name
            if name.startswith(prefix):
                name = name[len(prefix) :]
            files.append(name)
    return sorted(files)


def forbidden_package_hits(files: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for file_name in files:
        for pattern in FORBIDDEN_PACKAGE_PATTERNS:
            if pattern.search(file_name):
                hits.append({"path": file_name, "pattern": pattern.pattern})
    return hits


def summary_forbidden_hits(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.stat().st_size > 5_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_SUMMARY_PATTERNS:
            if pattern.search(text):
                hits.append({"path": rel(path), "pattern": pattern.pattern})
    return hits


def parse_package_size(stderr: str) -> dict[str, str | None]:
    match = re.search(r"Packaged\s+\d+\s+files,\s+([^()]+)\(([^)]+)\)", stderr)
    if not match:
        return {"uncompressed": None, "compressed": None}
    return {
        "uncompressed": match.group(1).strip(),
        "compressed": match.group(2).strip(),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    file_rows = "\n".join(f"| `{file_name}` |" for file_name in summary["package"]["files"])
    gate_rows = "\n".join(f"| `{name}` | `{value}` |" for name, value in summary["gates"].items())
    return f"""# R256 agentpprof Crate Package Smoke

Status: `{summary['status']}`

R256 runs `cargo package --list` and `cargo package` for `agentpprof` on a clean
repository snapshot, then records the crate file set and verification result.
This checks local crate-package readiness only. It does not publish to crates.io,
run on an external machine, collect user feedback, call a model, or add C5/C6
outcome evidence.

## Package

- package: `{summary['package']['name']} {summary['package']['version']}`
- manifest: `{summary['package']['manifest']}`
- crate archive: `{summary['package']['crate_archive']['path']}`
- crate archive bytes: `{summary['package']['crate_archive']['size_bytes']}`
- cargo-reported size: `{summary['package']['cargo_reported_size']['uncompressed']}` (`{summary['package']['cargo_reported_size']['compressed']}`)
- registry dependency observed: `{summary['package']['registry_dependency_observed']}`
- source commit: `{summary['provenance']['repo_commit']}`
- repo dirty before package: `{summary['provenance']['repo_dirty_before_package']}`

## Files

| Packaged file |
|---------------|
{file_rows}

## Gates

| Gate | Passed |
|------|--------|
{gate_rows}

## Boundary

`c7_crate_package_smoke_supported={summary['c7_crate_package_smoke_supported']}`
only means the crate can be packaged and verified locally with its intended file
set and registry dependency resolution. It is not a crates.io release,
community-adoption result, developer-utility result, tag-adequacy result, or
weak-accept result.
"""


def run_r256(args: argparse.Namespace) -> dict[str, Any]:
    repo_commit = git(["rev-parse", "HEAD"])
    repo_dirty_before_package = bool(git(["status", "--porcelain"]))
    if repo_dirty_before_package and not args.allow_dirty:
        raise RuntimeError(
            "R256 requires a clean working tree before cargo package; "
            "commit or stash local edits, or pass --allow-dirty for an explicitly weaker run."
        )

    with tempfile.TemporaryDirectory(prefix="agentpprof-r256-") as tmp_raw:
        tmp = Path(tmp_raw)
        cargo_target = tmp / "cargo-target"
        env = os.environ.copy()
        env["CARGO_TARGET_DIR"] = str(cargo_target)

        common_package_args = ["cargo", "package", "--manifest-path", str(MANIFEST)]
        if args.allow_dirty:
            common_package_args.append("--allow-dirty")

        list_result = r248.run_cmd([*common_package_args, "--list"], REPO_ROOT, env=env, timeout=args.timeout)
        package_result = r248.run_cmd(common_package_args, REPO_ROOT, env=env, timeout=args.timeout)

        package_files = sorted(package_files_from_list(list_result["stdout"]))
        crate_candidates = sorted(cargo_target.glob(f"package/{CRATE_FILE}"))
        crate_path = crate_candidates[0] if crate_candidates else None
        archive_files = crate_archive_files(crate_path) if crate_path is not None else []
        archive_meta = (
            {
                "path": sanitize_text(str(crate_path), tmp),
                "exists": True,
                "size_bytes": crate_path.stat().st_size,
                "sha256": r248.sha256_file(crate_path),
            }
            if crate_path is not None
            else {"path": None, "exists": False, "size_bytes": 0, "sha256": None}
        )

        sanitized_list_log = sanitize_text(list_result["stdout"] + list_result["stderr"], tmp)
        sanitized_package_log = sanitize_text(package_result["stdout"] + package_result["stderr"], tmp)

    out_dir = Path(args.out_dir).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    package_files_path = out_dir / "package-files-r256.txt"
    package_log_path = out_dir / "cargo-package-r256.txt"
    summary_json = out_dir / "agentpprof-crate-package-r256.json"
    summary_md = out_dir / "agentpprof-crate-package-r256.md"

    package_files_path.write_text("\n".join(package_files) + "\n", encoding="utf-8")
    package_log_path.write_text(
        "## cargo package --list\n\n"
        + sanitized_list_log
        + "\n\n## cargo package\n\n"
        + sanitized_package_log
        + "\n",
        encoding="utf-8",
    )

    missing_required = sorted(REQUIRED_PACKAGE_FILES.difference(package_files))
    unexpected_forbidden = forbidden_package_hits(package_files + archive_files)
    package_verify_text = sanitized_package_log.lower()
    registry_dependency_observed = "agent-session v0.3.3" in package_verify_text
    gates = {
        "repo_clean_before_package": not repo_dirty_before_package,
        "package_list_ok": list_result["returncode"] == 0,
        "cargo_package_ok": package_result["returncode"] == 0,
        "required_files_present": missing_required == [],
        "archive_created": archive_meta["exists"] and archive_meta["size_bytes"] > 0,
        "archive_files_match_list": archive_files == package_files,
        "forbidden_paths_absent": unexpected_forbidden == [],
        "registry_dependency_observed": registry_dependency_observed,
        "crate_verify_observed": f"Verifying {PACKAGE_NAME} v{PACKAGE_VERSION}".lower() in package_verify_text,
        "no_private_history_discovery": True,
        "no_llm_calls": True,
        "c5_supported": False,
        "c6_supported": False,
        "crates_publish_supported": False,
        "weak_accept_supported": False,
    }
    required = [
        "repo_clean_before_package",
        "package_list_ok",
        "cargo_package_ok",
        "required_files_present",
        "archive_created",
        "archive_files_match_list",
        "forbidden_paths_absent",
        "registry_dependency_observed",
        "crate_verify_observed",
        "no_private_history_discovery",
        "no_llm_calls",
    ]

    summary = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": "passed" if all(gates[name] for name in required) else "failed",
        "generated_at": now_iso(),
        "source_command": "python3 docs/visexp/r256_agentpprof_crate_package_smoke.py",
        "package": {
            "name": PACKAGE_NAME,
            "version": PACKAGE_VERSION,
            "manifest": rel(MANIFEST),
            "files": package_files,
            "archive_files": archive_files,
            "missing_required_files": missing_required,
            "forbidden_package_hits": unexpected_forbidden,
            "crate_archive": archive_meta,
            "cargo_reported_size": parse_package_size(sanitized_package_log),
            "registry_dependency_observed": registry_dependency_observed,
            "list_returncode": list_result["returncode"],
            "package_returncode": package_result["returncode"],
            "list_elapsed_s": list_result["elapsed_s"],
            "package_elapsed_s": package_result["elapsed_s"],
            "list_log": rel(package_files_path),
            "package_log": rel(package_log_path),
        },
        "gates": gates,
        "required_gates": required,
        "outputs": {
            "summary_json": rel(summary_json),
            "summary_md": rel(summary_md),
            "package_files": rel(package_files_path),
            "package_log": rel(package_log_path),
        },
        "provenance": {
            "repo_commit": repo_commit,
            "repo_dirty_before_package": repo_dirty_before_package,
            "allow_dirty": args.allow_dirty,
            "raw_trace_read": False,
            "private_agent_history_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
        "c7_crate_package_smoke_supported": all(gates[name] for name in required),
        "c5_supported": False,
        "c6_supported": False,
        "crates_publish_supported": False,
        "external_machine_install_supported": False,
        "developer_utility_supported": False,
        "weak_accept_supported": False,
        "boundary": (
            "Local cargo package dry-run only; no crates.io publish, no external-machine install, "
            "no developer outcome data, no tag-adequacy labels, and no C5/C6 human evidence."
        ),
    }
    write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")

    summary_hits = summary_forbidden_hits([summary_json, summary_md, package_log_path, package_files_path])
    summary["privacy"] = {
        "summary_forbidden_hits": summary_hits,
        "scanned_paths": [rel(path) for path in [summary_json, summary_md, package_log_path, package_files_path]],
    }
    summary["gates"]["summary_privacy_scan"] = summary_hits == []
    summary["required_gates"].append("summary_privacy_scan")
    summary["status"] = "passed" if all(summary["gates"][name] for name in summary["required_gates"]) else "failed"
    summary["c7_crate_package_smoke_supported"] = all(
        summary["gates"][name] for name in summary["required_gates"]
    )
    write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--timeout", type=int, default=480)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    summary = run_r256(args)
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": summary["status"],
                "package_files": len(summary["package"]["files"]),
                "archive_created": summary["gates"]["archive_created"],
                "registry_dependency_observed": summary["gates"]["registry_dependency_observed"],
                "weak_accept_supported": summary["weak_accept_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
