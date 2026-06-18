#!/usr/bin/env python3
"""R220: fresh-clone agentpprof community smoke.

This experiment verifies the user-facing Rust `agentpprof` entrypoint from a
clean temporary clone. It uses a public synthetic Codex session fixture, the
deterministic regex tagger, and standard `go tool pprof` for protobuf readback.

The script intentionally does not read local `.codex` or `.claude` histories,
does not call any LLM, and does not synthesize C5/C6 human outcomes.
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
RUN_ID = "R220"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "fresh-clone-agentpprof-r220"
PUBLIC_PROJECT_NAME = "agentsight-public-fixture"
FORBIDDEN_OUTPUT_STRINGS = [
    "Profile the repository and find repeated test and network effects",
    "Compare the test command with the network command",
    "/.codex/",
    str(Path.home()),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(
    cmd: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: int = 180,
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


def git(args: list[str], cwd: Path = REPO_ROOT) -> str:
    proc = run_cmd(["git", *args], cwd, timeout=60)
    if proc["returncode"] != 0:
        raise RuntimeError(proc["stderr"].strip() or f"git {' '.join(args)} failed")
    return proc["stdout"].strip()


def parse_stdout_json(result: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"agentpprof did not print JSON: {exc}: {result['stdout'][:500]}") from exc


def codex_line(entry_type: str, payload: dict[str, Any], timestamp: str) -> str:
    return json.dumps(
        {"timestamp": timestamp, "type": entry_type, "payload": payload},
        sort_keys=True,
    )


def write_public_codex_fixture(path: Path, project_root: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        codex_line(
            "session_meta",
            {
                "type": "session_meta",
                "id": "r220-public-fixture-session",
                "session_id": "r220-public-fixture-session",
                "model": "gpt-5-codex-fixture",
                "cwd": str(project_root),
            },
            "2026-06-18T10:00:00Z",
        ),
        codex_line(
            "turn_context",
            {
                "type": "turn_context",
                "model": "gpt-5-codex-fixture",
                "cwd": str(project_root),
            },
            "2026-06-18T10:00:01Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "user_message",
                "content": "Profile the repository and find repeated test and network effects.",
            },
            "2026-06-18T10:00:02Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-rg-read",
                "arguments": json.dumps({"cmd": "rg -n TODO README.md agentpprof/src/main.rs"}),
            },
            "2026-06-18T10:00:03Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-rg-read",
                "output": "Process exited with code 0\nagentpprof/src/main.rs:1:TODO public fixture",
            },
            "2026-06-18T10:00:04Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "The read command touched the profile CLI."}],
            },
            "2026-06-18T10:00:05Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "user_message",
                "content": "Compare the test command with the network command and produce pprof outputs.",
            },
            "2026-06-18T10:00:06Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-cargo-test",
                "arguments": json.dumps(
                    {"cmd": "cargo test --manifest-path agentpprof/Cargo.toml pprof_writer_emits_gzip_profile"}
                ),
            },
            "2026-06-18T10:00:07Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-cargo-test",
                "output": "Process exited with code 0\n1 test passed",
            },
            "2026-06-18T10:00:08Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-curl-network",
                "arguments": json.dumps({"cmd": "curl -I https://github.com/eunomia-bpf/agentsight"}),
            },
            "2026-06-18T10:00:09Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-curl-network",
                "output": "Process exited with code 0\nHTTP/2 200",
            },
            "2026-06-18T10:00:10Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Generated task, tools, files, network, and token projections.",
                    }
                ],
            },
            "2026-06-18T10:00:11Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "token_count",
                "usage": {
                    "input_tokens": 120,
                    "output_tokens": 45,
                    "total_tokens": 165,
                },
            },
            "2026-06-18T10:00:12Z",
        ),
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {
        "fixture_rows": len(rows),
        "fixture_sha256": sha256_file(path),
        "fixture_path_shape": ".codex/sessions/2026/06/18/*.jsonl",
        "contains_public_prompts": True,
        "reads_real_agent_history": False,
    }


def folded_total(path: Path) -> int:
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            total += int(line.rsplit(" ", 1)[1])
        except (IndexError, ValueError) as exc:
            raise RuntimeError(f"bad folded line in {path}: {line}") from exc
    return total


def read_folded_map(path: Path) -> dict[str, int]:
    stacks: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            stack, weight = line.rsplit(" ", 1)
            stacks[stack] = int(weight)
        except (IndexError, ValueError) as exc:
            raise RuntimeError(f"bad folded line in {path}: {line}") from exc
    return stacks


def json_total(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return int(payload["profile"]["summary"]["total_weight"])


def expected_projection_checks(artifact_dir: Path) -> dict[str, bool]:
    tools = read_folded_map(artifact_dir / "tools.folded")
    files = read_folded_map(artifact_dir / "files.folded")
    network = read_folded_map(artifact_dir / "network.folded")
    tokens = json.loads((artifact_dir / "tokens.json").read_text(encoding="utf-8"))
    token_stacks = {
        row["stack"]: int(row["weight"])
        for row in tokens["profile"]["summary"]["top"]
    }
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


def pprof_total_samples(text: str) -> int | None:
    match = re.search(r"of\s+(\d+)\s+total", text)
    if match:
        return int(match.group(1))
    return None


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
        for forbidden in FORBIDDEN_OUTPUT_STRINGS:
            if forbidden and forbidden in data:
                hits.append({"path": rel(path), "needle": forbidden})
    return hits


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    gates = summary["gates"]
    paths = summary["outputs"]
    text = f"""# R220 Fresh-Clone agentpprof Smoke

Status: `{summary["status"]}`

R220 clones the repository into a temporary clean checkout, creates a public
synthetic Codex fixture under `.codex/sessions/...`, and runs the real Rust
`agentpprof` CLI with the deterministic regex tagger. It does not read local
Codex/Claude histories, does not call an LLM, and does not create C5/C6 human
evidence.

## Main Results

- Source commit: `{summary["source"]["head"]}` on `{summary["source"]["branch"]}`
- Clone clean before fixture: `{gates["clone_clean_before_fixture"]}`
- `agentpprof` views passed: `{gates["all_views_nonzero"]}`
- `go tool pprof` readback passed: `{gates["pprof_readback"]}`
- Fixture expected-stack checks passed: `{gates["fixture_projection_expected_stacks"]}`
- Output containment passed: `{gates["output_containment"]}`
- Redaction scan passed: `{gates["privacy_scan"]}`
- Weak accept supported: `{summary["weak_accept_supported"]}`

## View Samples

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
"""
    for view, result in summary["agentpprof"].items():
        out = paths[view]
        text += (
            f"| `{view}` | `{result['format']}` | {result['samples']} | "
            f"{result['unique_stacks']} | `{out['path']}` |\n"
        )
    text += f"""
## Boundaries

- This is a community-tool smoke and C7 artifact-usability result, not a user
  study.
- It validates regex-tagged, public-fixture `agentpprof` operation from a clean
  clone; it does not validate llama.cpp setup, real-history privacy, external
  machine adoption, C5 developer task outcomes, or C6 tag adequacy.
- Parent worktree dirtiness is not a pass gate; the clean-clone oracle is the
  temporary clone status before fixture creation.
- `go tool pprof` output is saved at `{paths['pprof_top']['path']}`.
"""
    path.write_text(text, encoding="utf-8")


def run_r220(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    source_dirty_paths = git(["status", "--short"]).splitlines()

    source = {
        "branch": git(["branch", "--show-current"]) or "detached",
        "head": git(["rev-parse", "--short", "HEAD"]),
        "driver_worktree_dirty_count": len(source_dirty_paths),
        "driver_worktree_dirty_recorded": False,
        "provenance_note": (
            "R220's clean-clone oracle is the temporary clone status before fixture creation; "
            "the parent worktree may contain the R220 script/artifacts being generated."
        ),
    }

    with tempfile.TemporaryDirectory(prefix="agentpprof-r220-") as tmp_raw:
        tmp = Path(tmp_raw)
        clone = tmp / "agentsight-clone"
        clone_cmd = ["git", "clone", "--quiet", "--local", "--no-hardlinks", str(REPO_ROOT), str(clone)]
        clone_result = run_cmd(clone_cmd, REPO_ROOT, timeout=args.clone_timeout)
        if clone_result["returncode"] != 0:
            raise RuntimeError(clone_result["stderr"])
        clone_head = git(["rev-parse", "--short", "HEAD"], cwd=clone)
        clone_status_before = git(["status", "--short"], cwd=clone).splitlines()

        fixture = clone / ".codex/sessions/2026/06/18/r220-public-fixture.jsonl"
        fixture_info = write_public_codex_fixture(fixture, clone)
        artifact_dir = out_dir / "profiles"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        cargo_target = tmp / "cargo-target"

        env = os.environ.copy()
        env["CARGO_TARGET_DIR"] = str(cargo_target)

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
            output = artifact_dir / filename
            cmd = [
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                str(clone / "agentpprof/Cargo.toml"),
                "--",
                "--project-root",
                str(clone),
                "--project-name",
                PUBLIC_PROJECT_NAME,
                "--session-file",
                str(fixture),
                "--tagger",
                "regex",
                "--no-cache",
                "--view",
                view,
                "-o",
                str(output),
            ]
            result = run_cmd(cmd, clone, env=env, timeout=args.cargo_timeout)
            commands[key] = {
                "cmd": ["cargo", "run", "--manifest-path", "agentpprof/Cargo.toml", "--", "--view", view, "-o", filename],
                "returncode": result["returncode"],
                "elapsed_s": result["elapsed_s"],
                "stderr_tail": result["stderr"][-1000:],
            }
            if result["returncode"] != 0:
                raise RuntimeError(f"agentpprof {key} failed: {result['stderr']}")
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

        pprof_top = out_dir / "pprof-top-r220.txt"
        pprof_result = run_cmd(
            ["go", "tool", "pprof", "-top", "-nodecount=20", str(artifact_dir / "tasks.pb.gz")],
            clone,
            timeout=args.pprof_timeout,
        )
        pprof_top.write_text(pprof_result["stdout"] + pprof_result["stderr"], encoding="utf-8")
        outputs["pprof_top"] = output_meta(pprof_top)

        totals = {
            "tasks_pprof_stdout": agentpprof["tasks"]["samples"],
            "tools_folded": folded_total(artifact_dir / "tools.folded"),
            "tokens_json": json_total(artifact_dir / "tokens.json"),
            "files_folded": folded_total(artifact_dir / "files.folded"),
            "network_folded": folded_total(artifact_dir / "network.folded"),
            "tools_svg_size": (artifact_dir / "tools.svg").stat().st_size,
            "pprof_top_total": pprof_total_samples(pprof_top.read_text(encoding="utf-8")),
        }
        projection_checks = expected_projection_checks(artifact_dir)
        scan_paths = [artifact_dir / name for name, _ in view_specs.values()] + [pprof_top]
        forbidden_hits = scan_forbidden(scan_paths)
        clone_status_after = git(["status", "--short"], cwd=clone).splitlines()

    gates = {
        "source_clone_succeeded": clone_result["returncode"] == 0,
        "clone_clean_before_fixture": clone_status_before == [],
        "clone_head_matches_source": clone_head == source["head"],
        "fixture_public_and_path_shaped": fixture_info["fixture_path_shape"] == ".codex/sessions/2026/06/18/*.jsonl",
        "all_views_nonzero": all(result["samples"] > 0 for result in agentpprof.values()),
        "all_outputs_exist": all(meta["exists"] and meta["size_bytes"] > 0 for meta in outputs.values()),
        "pprof_readback": pprof_result["returncode"] == 0 and totals["pprof_top_total"] == totals["tasks_pprof_stdout"],
        "folded_json_totals_match_stdout": (
            totals["tools_folded"] == agentpprof["tools"]["samples"]
            and totals["tokens_json"] == agentpprof["tokens"]["samples"]
            and totals["files_folded"] == agentpprof["files"]["samples"]
            and totals["network_folded"] == agentpprof["network"]["samples"]
        ),
        "fixture_projection_expected_stacks": all(projection_checks.values()),
        "output_containment": all(str(Path(meta["path"])).startswith("docs/visexp/out/fresh-clone-agentpprof-r220") for meta in outputs.values()),
        "privacy_scan": forbidden_hits == [],
        "no_llm_calls": True,
        "no_real_agent_history_reads": True,
        "c5_supported": False,
        "c6_supported": False,
    }
    smoke_gate_names = [
        "source_clone_succeeded",
        "clone_clean_before_fixture",
        "clone_head_matches_source",
        "fixture_public_and_path_shaped",
        "all_views_nonzero",
        "all_outputs_exist",
        "pprof_readback",
        "folded_json_totals_match_stdout",
        "fixture_projection_expected_stacks",
        "output_containment",
        "privacy_scan",
        "no_llm_calls",
        "no_real_agent_history_reads",
    ]
    status = "passed" if all(gates[name] for name in smoke_gate_names) else "failed"
    summary = {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "status": status,
        "source": source,
        "clone": {
            "head": clone_head,
            "clean_before_fixture": clone_status_before == [],
            "status_after_run": clone_status_after,
        },
        "fixture": fixture_info,
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
            "scanned_paths": [rel(path) for path in scan_paths],
        },
        "gates": gates,
        "smoke_gate_names": smoke_gate_names,
        "c7_fresh_clone_agentpprof_smoke_supported": status == "passed",
        "c5_supported": False,
        "c6_supported": False,
        "weak_accept_supported": False,
        "boundary": (
            "Fresh-clone public-fixture agentpprof smoke only; no llama.cpp setup, "
            "real-history privacy, external-machine adoption, C5 outcomes, or C6 labels."
        ),
    }
    write_json(out_dir / "fresh-clone-agentpprof-r220.json", summary)
    write_markdown(out_dir / "fresh-clone-agentpprof-r220.md", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--clone-timeout", type=int, default=120)
    parser.add_argument("--cargo-timeout", type=int, default=240)
    parser.add_argument("--pprof-timeout", type=int, default=60)
    args = parser.parse_args()
    summary = run_r220(args)
    print(
        json.dumps(
            {
                "run_id": summary["run_id"],
                "status": summary["status"],
                "tasks_samples": summary["agentpprof"]["tasks"]["samples"],
                "tools_samples": summary["agentpprof"]["tools"]["samples"],
                "tokens_samples": summary["agentpprof"]["tokens"]["samples"],
                "pprof_readback": summary["gates"]["pprof_readback"],
                "weak_accept_supported": summary["weak_accept_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
