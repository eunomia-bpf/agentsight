#!/usr/bin/env python3
"""R248: installed agentpprof public-fixture smoke.

This experiment verifies the installable `agentpprof` path with a committed
public Codex fixture. It intentionally avoids private agent-history discovery,
LLM tagging, and any C5/C6 human-outcome claim.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
RUN_ID = "R248"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "agentpprof-install-r248"
FIXTURE = REPO_ROOT / "agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl"
PROJECT_NAME = "agentsight-public-fixture"

FORBIDDEN_OUTPUT_STRINGS = [
    "Profile the repository and find repeated test and network effects",
    "Compare the test command with the network command",
    "/.codex/",
    "/.claude/",
    str(Path.home()),
]


def sanitize_text(text: str) -> str:
    sanitized = text
    replacements = [
        (str(REPO_ROOT), "<repo>"),
        (str(Path.home()), "<home>"),
    ]
    for needle, replacement in replacements:
        if needle:
            sanitized = sanitized.replace(needle, replacement)
    return sanitized


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def run_cmd(
    cmd: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: int = 240,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    ended = datetime.now(timezone.utc)
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "elapsed_s": round((ended - started).total_seconds(), 3),
    }


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_stdout_json(result: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"agentpprof stdout was not JSON: {exc}: {result['stdout'][:500]}") from exc


def folded_total(path: Path) -> int:
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        stack, weight = line.rsplit(" ", 1)
        total += int(weight)
    return total


def read_folded_map(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        stack, weight = line.rsplit(" ", 1)
        out[stack] = int(weight)
    return out


def json_total(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return int(payload["profile"]["summary"]["total_weight"])


def pprof_total_samples(text: str) -> int | None:
    match = re.search(r"of\s+(\d+)\s+total", text)
    return int(match.group(1)) if match else None


def output_meta(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
    }


def scan_forbidden(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.stat().st_size > 5_000_000:
            continue
        if path.suffix == ".gz":
            data = gzip.decompress(path.read_bytes()).decode("utf-8", errors="ignore")
        else:
            data = path.read_text(encoding="utf-8", errors="ignore")
        for needle in FORBIDDEN_OUTPUT_STRINGS:
            if needle and needle in data:
                hits.append({"path": rel(path), "needle": needle})
    return hits


def expected_projection_checks(profile_dir: Path) -> dict[str, bool]:
    tools = read_folded_map(profile_dir / "tools.folded")
    files = read_folded_map(profile_dir / "files.folded")
    network = read_folded_map(profile_dir / "network.folded")
    tokens = json.loads((profile_dir / "tokens.json").read_text(encoding="utf-8"))
    token_stacks = {row["stack"]: int(row["weight"]) for row in tokens["profile"]["summary"]["top"]}

    expected_tools = {
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:test;call:tool/shell;process:rg;effect:read;path:readme.md;status:ok": 1,
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:test;call:tool/shell;process:rg;effect:read;path:agentpprof/src/main.rs;status:ok": 1,
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:profile;call:tool/shell;process:cargo;effect:test;path:agentpprof/cargo.toml;status:ok": 1,
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:profile;call:tool/shell;process:curl;effect:network;domain:github.com;status:ok": 1,
    }
    expected_files = {
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:test;path:readme.md;effect:read;status:ok": 1,
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:test;path:agentpprof/src/main.rs;effect:read;status:ok": 1,
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:profile;path:agentpprof/cargo.toml;effect:test;status:ok": 1,
    }
    expected_network = {
        "project:agentsight-public-fixture;agent:codex;session:profile;prompt:profile;domain:github.com;process:curl;status:ok": 1,
    }
    expected_tokens = {
        "project:agentsight-public-fixture;agent:codex;model:gpt-5-codex-fixture;kind:input;session:profile;prompt:profile;call:llm/debug": 120,
        "project:agentsight-public-fixture;agent:codex;model:gpt-5-codex-fixture;kind:output;session:profile;prompt:profile;call:llm/debug": 45,
    }
    return {
        "tools_exact_expected": tools == expected_tools,
        "files_exact_expected": files == expected_files,
        "network_exact_expected": network == expected_network,
        "token_reported_components_expected": all(
            token_stacks.get(stack) == weight for stack, weight in expected_tokens.items()
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    view_rows = "\n".join(
        f"| `{name}` | `{view['format']}` | {view['samples']} | {view['unique_stacks']} | `{summary['outputs'][name]['path']}` |"
        for name, view in summary["agentpprof"].items()
    )
    gate_rows = "\n".join(f"| `{name}` | `{value}` |" for name, value in summary["gates"].items())
    return f"""# R248 agentpprof Install Smoke

Status: `{summary['status']}`

R248 installs `agentpprof` from the local package with `cargo install --path`,
runs the installed binary on a committed public Codex fixture, and checks Go
pprof readback plus folded/JSON/SVG projections. It does not read private
Codex/Claude history, does not call a model, and does not add C5/C6 outcome
evidence.

## Package Path

- install command: `cargo install --path agentpprof --locked --force`
- installed help passed: `{summary['install']['help_returncode'] == 0}`
- fixture: `{summary['fixture']['path']}`
- fixture sha256: `{summary['fixture']['sha256']}`
- source commit: `{summary['provenance']['repo_commit']}`
- source dirty before generation: `{summary['provenance']['repo_dirty']}`

## Views

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
{view_rows}

## Gates

| Gate | Passed |
|------|--------|
{gate_rows}

## Boundary

`c7_install_smoke_supported={summary['c7_install_smoke_supported']}` only
means the installed CLI can process the committed public fixture and produce
readable pprof/folded/JSON/SVG artifacts. It does not support developer utility,
tag adequacy, real-history privacy, external-machine adoption, llama.cpp setup,
or weak accept.
"""


def run_r248(args: argparse.Namespace) -> dict[str, Any]:
    repo_commit = git(["rev-parse", "HEAD"])
    repo_dirty = bool(git(["status", "--porcelain"]))

    out_dir = Path(args.out_dir).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = out_dir / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="agentpprof-r248-") as tmp_raw:
        tmp = Path(tmp_raw)
        install_root = tmp / "install-root"
        cargo_target = tmp / "cargo-target"
        env = os.environ.copy()
        env["CARGO_TARGET_DIR"] = str(cargo_target)

        install_result = run_cmd(
            [
                "cargo",
                "install",
                "--path",
                "agentpprof",
                "--locked",
                "--force",
                "--root",
                str(install_root),
            ],
            REPO_ROOT,
            env=env,
            timeout=args.install_timeout,
        )
        installed = install_root / "bin/agentpprof"
        installed_exists = installed.exists()
        help_result = run_cmd([str(installed), "--help"], REPO_ROOT, timeout=60) if installed.exists() else {
            "returncode": 127,
            "stdout": "",
            "stderr": "installed binary missing",
            "elapsed_s": 0,
        }

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
                str(FIXTURE),
                "--tagger",
                "regex",
                "--no-cache",
                "--view",
                view,
                "-o",
                str(output),
            ]
            result = run_cmd(cmd, REPO_ROOT, timeout=args.run_timeout)
            commands[key] = {
                "cmd": [
                    "agentpprof",
                    "--project-root",
                    ".",
                    "--project-name",
                    PROJECT_NAME,
                    "--session-file",
                    rel(FIXTURE),
                    "--tagger",
                    "regex",
                    "--no-cache",
                    "--view",
                    view,
                    "-o",
                    rel(output),
                ],
                "returncode": result["returncode"],
                "elapsed_s": result["elapsed_s"],
                "stderr_tail": sanitize_text(result["stderr"][-1000:]),
            }
            if result["returncode"] != 0:
                raise RuntimeError(f"installed agentpprof {key} failed: {result['stderr']}")
            parsed = parse_stdout_json(result)
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

        pprof_top = out_dir / "pprof-top-r248.txt"
        pprof_result = run_cmd(
            ["go", "tool", "pprof", "-top", "-nodecount=20", str(profile_dir / "tasks.pb.gz")],
            REPO_ROOT,
            timeout=args.pprof_timeout,
        )
        pprof_top.write_text(pprof_result["stdout"] + pprof_result["stderr"], encoding="utf-8")
        outputs["pprof_top"] = output_meta(pprof_top)

    totals = {
        "tasks_pprof_stdout": agentpprof["tasks"]["samples"],
        "tools_folded": folded_total(profile_dir / "tools.folded"),
        "tokens_json": json_total(profile_dir / "tokens.json"),
        "files_folded": folded_total(profile_dir / "files.folded"),
        "network_folded": folded_total(profile_dir / "network.folded"),
        "pprof_top_total": pprof_total_samples(pprof_top.read_text(encoding="utf-8")),
    }
    projection_checks = expected_projection_checks(profile_dir)
    summary_json = out_dir / "agentpprof-install-r248.json"
    summary_md = out_dir / "agentpprof-install-r248.md"
    scan_paths = [profile_dir / filename for filename, _ in view_specs.values()] + [pprof_top]
    forbidden_hits = scan_forbidden(scan_paths)
    source_hashes = {
        rel(FIXTURE): sha256_file(FIXTURE),
        rel(REPO_ROOT / "agentpprof/Cargo.toml"): sha256_file(REPO_ROOT / "agentpprof/Cargo.toml"),
        rel(REPO_ROOT / "agentpprof/src/main.rs"): sha256_file(REPO_ROOT / "agentpprof/src/main.rs"),
        rel(REPO_ROOT / "agentpprof/README.md"): sha256_file(REPO_ROOT / "agentpprof/README.md"),
    }
    gates = {
        "cargo_install_ok": install_result["returncode"] == 0 and installed_exists,
        "installed_help_ok": help_result["returncode"] == 0,
        "committed_fixture_exists": FIXTURE.exists(),
        "fixture_path_is_codex_session_shape": "/codex/sessions/" in str(FIXTURE),
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
            str(Path(meta["path"])).startswith("docs/visexp/out/agentpprof-install-r248")
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
        "cargo_install_ok",
        "installed_help_ok",
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
        "source_command": "python3 docs/visexp/r248_agentpprof_install_smoke.py",
        "fixture": {
            "path": rel(FIXTURE),
            "sha256": sha256_file(FIXTURE),
            "rows": len(FIXTURE.read_text(encoding="utf-8").splitlines()),
            "reads_real_agent_history": False,
        },
        "install": {
            "command": "cargo install --path agentpprof --locked --force",
            "returncode": install_result["returncode"],
            "elapsed_s": install_result["elapsed_s"],
            "stderr_tail": sanitize_text(install_result["stderr"][-2000:]),
            "help_returncode": help_result["returncode"],
        },
        "agentpprof": agentpprof,
        "outputs": outputs,
        "commands": commands,
        "pprof": {
            "returncode": pprof_result["returncode"],
            "top_total_samples": totals["pprof_top_total"],
            "elapsed_s": pprof_result["elapsed_s"],
            "output_path": rel(pprof_top),
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
            "scanned_paths": [rel(path) for path in scan_paths],
        },
        "gates": gates,
        "required_gates": required,
        "source_hashes": source_hashes,
        "provenance": {
            "repo_commit": repo_commit,
            "repo_dirty": repo_dirty,
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
        "c7_install_smoke_supported": all(gates[name] for name in required),
        "c5_supported": False,
        "c6_supported": False,
        "weak_accept_supported": False,
        "boundary": (
            "Installed CLI public-fixture smoke only; no real-history privacy proof, "
            "external-machine adoption, llama.cpp setup, C5 outcomes, or C6 labels."
        ),
    }
    write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")

    scan_paths = scan_paths + [summary_json, summary_md]
    forbidden_hits = scan_forbidden(scan_paths)
    summary["privacy"]["forbidden_hits"] = forbidden_hits
    summary["privacy"]["scanned_paths"] = [rel(path) for path in scan_paths]
    summary["gates"]["privacy_scan"] = forbidden_hits == []
    summary["status"] = "passed" if all(summary["gates"][name] for name in required) else "failed"
    summary["c7_install_smoke_supported"] = all(summary["gates"][name] for name in required)
    write_json(summary_json, summary)
    summary_md.write_text(render_markdown(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--install-timeout", type=int, default=420)
    parser.add_argument("--run-timeout", type=int, default=120)
    parser.add_argument("--pprof-timeout", type=int, default=60)
    args = parser.parse_args()
    summary = run_r248(args)
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": summary["status"],
                "install_ok": summary["gates"]["cargo_install_ok"],
                "tasks_samples": summary["agentpprof"]["tasks"]["samples"],
                "pprof_readback": summary["gates"]["pprof_readback"],
                "weak_accept_supported": summary["weak_accept_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
