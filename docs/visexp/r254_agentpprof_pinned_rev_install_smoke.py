#!/usr/bin/env python3
"""R254: pinned-revision GitHub agentpprof public-fixture smoke.

R220 verifies a clean local clone and R248 verifies `cargo install --path`.
R253 verifies the GitHub branch install path. R254 removes branch mutability
from that claim by installing `agentpprof` from a pinned Git revision with
`cargo install --git --rev`, then running the installed binary on the committed
public Codex fixture. It deliberately avoids private session discovery, live LLM
tagging, participant responses, and human labels.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import r248_agentpprof_install_smoke as r248


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
RUN_ID = "R254"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "agentpprof-pinned-rev-install-r254"
DEFAULT_GIT_URL = "https://github.com/eunomia-bpf/agentsight"
PROJECT_NAME = "agentsight-public-fixture"

FORBIDDEN_SUMMARY_PATTERNS = [
    re.compile(r"/tmp/[^\s,;\"'<>)]*"),
    re.compile(r"/var/tmp/[^\s,;\"'<>)]*"),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sanitize_text(text: str, tmp_root: Path | None = None) -> str:
    sanitized = r248.sanitize_text(text)
    if tmp_root is not None:
        sanitized = sanitized.replace(str(tmp_root), "<tmp-r254>")
    for pattern in FORBIDDEN_SUMMARY_PATTERNS:
        sanitized = pattern.sub("<redacted-path>", sanitized)
    return sanitized


def git(args: list[str]) -> str | None:
    return r248.git(args)


def output_meta(path: Path) -> dict[str, Any]:
    return r248.output_meta(path)


def summary_forbidden_hits(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.stat().st_size > 5_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_SUMMARY_PATTERNS:
            if pattern.search(text):
                hits.append({"path": r248.rel(path), "pattern": pattern.pattern})
    return hits


def render_markdown(summary: dict[str, Any]) -> str:
    view_rows = "\n".join(
        f"| `{name}` | `{view['format']}` | {view['samples']} | {view['unique_stacks']} | `{summary['outputs'][name]['path']}` |"
        for name, view in summary["agentpprof"].items()
    )
    gate_rows = "\n".join(f"| `{name}` | `{value}` |" for name, value in summary["gates"].items())
    return f"""# R254 agentpprof Pinned-Revision Install Smoke

Status: `{summary['status']}`

R254 installs `agentpprof` with `cargo install --git --rev` from a pinned
GitHub revision, runs the installed binary on the committed public Codex fixture,
and checks Go pprof readback plus folded/JSON/SVG projections. It does not read
private Codex/Claude history, does not call a live tagger/model, and does not
add C5/C6 outcome evidence.

## Install Path

- git URL: `{summary['install']['git_url']}`
- revision: `{summary['install']['rev']}`
- install rev matches driver commit: `{summary['install']['rev'] == summary['provenance']['repo_commit']}`
- installed help passed: `{summary['install']['help_returncode'] == 0}`
- fixture: `{summary['fixture']['path']}`
- fixture sha256: `{summary['fixture']['sha256']}`
- driver commit: `{summary['provenance']['repo_commit']}`
- driver dirty before generation: `{summary['provenance']['repo_dirty']}`

## Views

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
{view_rows}

## Gates

| Gate | Passed |
|------|--------|
{gate_rows}

## Boundary

`c7_pinned_rev_install_smoke_supported={summary['c7_pinned_rev_install_smoke_supported']}`
only means a GitHub-installed CLI from this exact revision can process the
committed public fixture and produce readable pprof/folded/JSON/SVG artifacts.
It does not support developer utility, tag adequacy, real-history privacy,
external-machine adoption, llama.cpp setup, crates.io release, or weak accept.
"""


def run_r254(args: argparse.Namespace) -> dict[str, Any]:
    repo_commit = git(["rev-parse", "HEAD"])
    install_rev = args.rev or repo_commit
    if not install_rev:
        raise RuntimeError("could not resolve pinned revision")
    repo_dirty = bool(git(["status", "--porcelain"]))
    out_dir = Path(args.out_dir).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = out_dir / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="agentpprof-r254-") as tmp_raw:
        tmp = Path(tmp_raw)
        install_root = tmp / "install-root"
        cargo_target = tmp / "cargo-target"
        env = os.environ.copy()
        env["CARGO_TARGET_DIR"] = str(cargo_target)

        install_cmd = [
            "cargo",
            "install",
            "--git",
            args.git_url,
            "--rev",
            install_rev,
            "--locked",
            "--force",
            "--root",
            str(install_root),
            "agentpprof",
        ]
        install_result = r248.run_cmd(install_cmd, REPO_ROOT, env=env, timeout=args.install_timeout)
        installed = install_root / "bin/agentpprof"
        installed_exists = installed.exists()
        help_result = (
            r248.run_cmd([str(installed), "--help"], REPO_ROOT, timeout=60)
            if installed_exists
            else {
                "returncode": 127,
                "stdout": "",
                "stderr": "installed binary missing",
                "elapsed_s": 0,
            }
        )

        view_specs = {
            "tasks": ("tasks.pb.gz", "tasks"),
            "tools": ("tools.folded", "tools"),
            "tokens": ("tokens.json", "tokens"),
            "files": ("files.folded", "files"),
            "network": ("network.folded", "network"),
            "tools_svg": ("tools.svg", "tools"),
        }
        commands: dict[str, dict[str, Any]] = {}
        agentpprof: dict[str, dict[str, Any]] = {}
        outputs: dict[str, dict[str, Any]] = {}

        for key, (filename, view) in view_specs.items():
            output = profile_dir / filename
            cmd = [
                str(installed),
                "--project-root",
                str(REPO_ROOT),
                "--project-name",
                PROJECT_NAME,
                "--session-file",
                str(r248.FIXTURE),
                "--tagger",
                "regex",
                "--no-cache",
                "--view",
                view,
                "-o",
                str(output),
            ]
            result = r248.run_cmd(cmd, REPO_ROOT, timeout=args.run_timeout)
            commands[key] = {
                "cmd": [
                    "agentpprof",
                    "--project-root",
                    ".",
                    "--project-name",
                    PROJECT_NAME,
                    "--session-file",
                    r248.rel(r248.FIXTURE),
                    "--tagger",
                    "regex",
                    "--no-cache",
                    "--view",
                    view,
                    "-o",
                    r248.rel(output),
                ],
                "returncode": result["returncode"],
                "elapsed_s": result["elapsed_s"],
                "stderr_tail": sanitize_text(result["stderr"][-1000:], tmp),
            }
            if result["returncode"] != 0:
                raise RuntimeError(f"Git-installed agentpprof {key} failed: {result['stderr']}")
            parsed = r248.parse_stdout_json(result)
            agentpprof[key] = {
                "format": parsed["format"],
                "view": parsed["view"],
                "sample_type": parsed["sample_type"],
                "unit": parsed["unit"],
                "sessions": int(parsed["sessions"]),
                "samples": int(parsed["samples"]),
                "unique_stacks": int(parsed["unique_stacks"]),
                "warnings": parsed.get("warnings", []),
            }
            outputs[key] = output_meta(output)

        pprof_top = out_dir / "pprof-top-r254.txt"
        pprof_result = r248.run_cmd(
            ["go", "tool", "pprof", "-top", "-nodecount=20", str(profile_dir / "tasks.pb.gz")],
            REPO_ROOT,
            timeout=args.pprof_timeout,
        )
        pprof_top.write_text(pprof_result["stdout"] + pprof_result["stderr"], encoding="utf-8")
        outputs["pprof_top"] = output_meta(pprof_top)

        install_summary = {
            "command": (
                "cargo install --git "
                f"{args.git_url} --rev {install_rev} --locked --force agentpprof"
            ),
            "git_url": args.git_url,
            "rev": install_rev,
            "returncode": install_result["returncode"],
            "elapsed_s": install_result["elapsed_s"],
            "stderr_tail": sanitize_text(install_result["stderr"][-2000:], tmp),
            "stdout_tail": sanitize_text(install_result["stdout"][-1000:], tmp),
            "installed_binary_exists": installed_exists,
            "help_returncode": help_result["returncode"],
        }

    totals = {
        "tasks_pprof_stdout": agentpprof["tasks"]["samples"],
        "tools_folded": r248.folded_total(profile_dir / "tools.folded"),
        "tokens_json": r248.json_total(profile_dir / "tokens.json"),
        "files_folded": r248.folded_total(profile_dir / "files.folded"),
        "network_folded": r248.folded_total(profile_dir / "network.folded"),
        "pprof_top_total": r248.pprof_total_samples(pprof_top.read_text(encoding="utf-8")),
    }
    projection_checks = r248.expected_projection_checks(profile_dir)
    summary_json = out_dir / "agentpprof-pinned-rev-install-r254.json"
    summary_md = out_dir / "agentpprof-pinned-rev-install-r254.md"
    scan_paths = [profile_dir / filename for filename, _ in view_specs.values()] + [pprof_top]
    forbidden_hits = r248.scan_forbidden(scan_paths)
    source_hashes = {
        r248.rel(r248.FIXTURE): r248.sha256_file(r248.FIXTURE),
        r248.rel(REPO_ROOT / "agentpprof/Cargo.toml"): r248.sha256_file(REPO_ROOT / "agentpprof/Cargo.toml"),
        r248.rel(REPO_ROOT / "agentpprof/src/main.rs"): r248.sha256_file(REPO_ROOT / "agentpprof/src/main.rs"),
        r248.rel(REPO_ROOT / "agentpprof/README.md"): r248.sha256_file(REPO_ROOT / "agentpprof/README.md"),
    }
    gates = {
        "cargo_git_install_ok": install_summary["returncode"] == 0 and install_summary["installed_binary_exists"],
        "installed_help_ok": install_summary["help_returncode"] == 0,
        "install_rev_matches_driver_commit": install_summary["rev"] == repo_commit,
        "committed_fixture_exists": r248.FIXTURE.exists(),
        "fixture_path_is_codex_session_shape": "/codex/sessions/" in str(r248.FIXTURE),
        "all_views_nonzero": all(view["samples"] > 0 for view in agentpprof.values()),
        "all_outputs_exist": all(meta["exists"] and meta["size_bytes"] > 0 for meta in outputs.values()),
        "pprof_readback": pprof_result["returncode"] == 0 and totals["pprof_top_total"] == totals["tasks_pprof_stdout"],
        "folded_json_totals_match_stdout": (
            totals["tools_folded"] == agentpprof["tools"]["samples"]
            and totals["tokens_json"] == agentpprof["tokens"]["samples"]
            and totals["files_folded"] == agentpprof["files"]["samples"]
            and totals["network_folded"] == agentpprof["network"]["samples"]
        ),
        "fixture_projection_expected_stacks": all(projection_checks.values()),
        "output_containment": all(
            str(Path(meta["path"])).startswith("docs/visexp/out/agentpprof-pinned-rev-install-r254")
            for meta in outputs.values()
        ),
        "privacy_scan": forbidden_hits == [],
        "explicit_session_file_only": all("--session-file" in command["cmd"] for command in commands.values()),
        "no_llm_calls": True,
        "no_private_history_discovery": True,
        "c5_supported": False,
        "c6_supported": False,
    }
    required = [
        "cargo_git_install_ok",
        "installed_help_ok",
        "install_rev_matches_driver_commit",
        "committed_fixture_exists",
        "fixture_path_is_codex_session_shape",
        "all_views_nonzero",
        "all_outputs_exist",
        "pprof_readback",
        "folded_json_totals_match_stdout",
        "fixture_projection_expected_stacks",
        "output_containment",
        "privacy_scan",
        "explicit_session_file_only",
        "no_llm_calls",
        "no_private_history_discovery",
    ]
    summary = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": "passed" if all(gates[name] for name in required) else "failed",
        "generated_at": now_iso(),
        "source_command": "python3 docs/visexp/r254_agentpprof_pinned_rev_install_smoke.py",
        "fixture": {
            "path": r248.rel(r248.FIXTURE),
            "sha256": r248.sha256_file(r248.FIXTURE),
            "rows": len(r248.FIXTURE.read_text(encoding="utf-8").splitlines()),
            "reads_real_agent_history": False,
        },
        "install": install_summary,
        "agentpprof": agentpprof,
        "outputs": outputs,
        "commands": commands,
        "pprof": {
            "returncode": pprof_result["returncode"],
            "top_total_samples": totals["pprof_top_total"],
            "elapsed_s": pprof_result["elapsed_s"],
            "output_path": r248.rel(pprof_top),
        },
        "totals": totals,
        "projection_checks": projection_checks,
        "privacy": {
            "forbidden_hits": forbidden_hits,
            "forbidden_checks": [
                "private prompt text",
                "private Codex/Claude history roots",
                "local home path",
            ],
            "scanned_paths": [r248.rel(path) for path in scan_paths],
        },
        "gates": gates,
        "required_gates": required,
        "source_hashes": source_hashes,
        "install_rev_matches_driver_commit": gates["install_rev_matches_driver_commit"],
        "provenance": {
            "repo_commit": repo_commit,
            "repo_dirty": repo_dirty,
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
        "c7_pinned_rev_install_smoke_supported": all(gates[name] for name in required),
        "c5_supported": False,
        "c6_supported": False,
        "weak_accept_supported": False,
        "boundary": (
            "Pinned-revision GitHub-installed CLI public-fixture smoke only; no "
            "crates.io release, real-history privacy proof, external-machine "
            "adoption, llama.cpp setup, C5 outcomes, or C6 labels."
        ),
    }
    r248.write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")

    scan_paths = scan_paths + [summary_json, summary_md]
    forbidden_hits = r248.scan_forbidden(scan_paths)
    summary_hits = summary_forbidden_hits([summary_json, summary_md])
    summary["privacy"]["forbidden_hits"] = forbidden_hits
    summary["privacy"]["summary_path_hits"] = summary_hits
    summary["privacy"]["scanned_paths"] = [r248.rel(path) for path in scan_paths]
    summary["gates"]["privacy_scan"] = forbidden_hits == [] and summary_hits == []
    summary["status"] = "passed" if all(summary["gates"][name] for name in required) else "failed"
    summary["c7_pinned_rev_install_smoke_supported"] = all(summary["gates"][name] for name in required)
    r248.write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--git-url", default=DEFAULT_GIT_URL)
    parser.add_argument("--rev", default=None)
    parser.add_argument("--install-timeout", type=int, default=900)
    parser.add_argument("--run-timeout", type=int, default=120)
    parser.add_argument("--pprof-timeout", type=int, default=60)
    args = parser.parse_args()
    summary = run_r254(args)
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": summary["status"],
                "install_ok": summary["gates"]["cargo_git_install_ok"],
                "tasks_samples": summary["agentpprof"]["tasks"]["samples"],
                "pprof_readback": summary["gates"]["pprof_readback"],
                "weak_accept_supported": summary["weak_accept_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
