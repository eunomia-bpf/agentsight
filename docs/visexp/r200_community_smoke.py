#!/usr/bin/env python3
"""R200: public-safe AgentFlame community smoke.

This smoke intentionally does not read local `.codex` or `.claude` traces. It
generates a tiny synthetic Codex JSONL fixture in a temporary directory, runs
the Rust AgentFlame CLI against that explicit `--session-file`, then reruns the
same command to verify cache behavior. The committed output is a redacted audit
summary; the local AgentFlame report remains under `.agentsight/agentflame`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_JSON = OUT_DIR / "community-smoke-r200.json"
DEFAULT_OUT_MD = OUT_DIR / "community-smoke-r200.md"
DEFAULT_LLAMA_SERVER = Path.home() / "workspace/llama.cpp-latest/build/bin/llama-server"
DEFAULT_MODEL_PATH = Path.home() / "workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf"
REQUIRED_ARTIFACT_KEYS = {
    "dashboard",
    "tag_cache",
    "semantic_system_folded",
    "nonsemantic_system_folded",
    "system_flamegraph",
    "token_flamegraph",
    "prompt_system",
    "session_system",
    "llm_token",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_text(text: str, replacements: list[tuple[str, str]]) -> str:
    out = text
    for old, new in replacements:
        if old:
            out = out.replace(old, new)
    return out


def sanitize_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        return sanitize_text(value, replacements)
    if isinstance(value, list):
        return [sanitize_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_value(item, replacements) for key, item in value.items()}
    return value


def short_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def git_status_paths() -> set[str]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return {f"git_status_failed:{proc.stderr.strip()}"}
    return {line[3:] for line in proc.stdout.splitlines() if len(line) >= 4}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def url_ok(url: str, timeout: float = 1.0) -> bool:
    for path in ("/health", "/v1/models"):
        try:
            with urllib.request.urlopen(url.rstrip("/") + path, timeout=timeout) as response:
                if 200 <= response.status < 500:
                    return True
        except (OSError, urllib.error.URLError):
            continue
    return False


def wait_for_server(url: str, deadline_s: float) -> bool:
    deadline = time.monotonic() + deadline_s
    while time.monotonic() < deadline:
        if url_ok(url, timeout=1.0):
            return True
        time.sleep(0.25)
    return False


def start_llama(args: argparse.Namespace, run_dir: Path) -> tuple[subprocess.Popen[str] | None, str, dict[str, Any]]:
    if args.llama_url:
        return None, args.llama_url.rstrip("/"), {
            "mode": "external",
            "url": args.llama_url.rstrip("/"),
        }

    server = Path(args.llama_server).expanduser()
    model = Path(args.model_path).expanduser()
    port = int(args.port) if args.port else free_port()
    url = f"http://127.0.0.1:{port}"
    info = {
        "mode": "managed",
        "server": str(server),
        "server_exists": server.exists(),
        "model_path": str(model),
        "model_exists": model.exists(),
        "model_sha256": sha256_file(model),
        "url": url,
    }
    if not server.exists() or not model.exists():
        return None, url, info | {"status": "missing_llama_or_model"}

    log_path = run_dir / "llama-server-r200.log"
    log_handle = log_path.open("w", encoding="utf-8")
    cmd = [
        str(server),
        "-m",
        str(model),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--ctx-size",
        str(args.ctx_size),
        "--reasoning",
        "off",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    info.update(
        {
            "cmd": cmd,
            "pid": proc.pid,
            "log_path": str(log_path),
            "status": "starting",
        }
    )
    if not wait_for_server(url, args.load_timeout):
        info["status"] = "startup_timeout"
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_handle.close()
        return None, url, info
    info["status"] = "ready"
    return proc, url, info


def codex_line(entry_type: str, payload: dict[str, Any], timestamp: str, **extra: Any) -> str:
    row: dict[str, Any] = {"timestamp": timestamp, "type": entry_type, "payload": payload}
    row.update(extra)
    return json.dumps(row, sort_keys=True)


def write_public_codex_fixture(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        codex_line(
            "session_meta",
            {
                "type": "session_meta",
                "originator": "codex-cli",
                "session_id": "r200-public-fixture",
                "model": "fixture-model",
            },
            "2026-06-15T12:00:00Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "user_message",
                "content": "Inspect the public sample project and identify repeated tests.",
            },
            "2026-06-15T12:00:01Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-rg",
                "arguments": json.dumps({"cmd": "rg -n TODO README.md src"}),
            },
            "2026-06-15T12:00:02Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-rg",
                "output": "Process exited with code 0\nREADME.md:3:TODO add example",
            },
            "2026-06-15T12:00:03Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-test",
                "arguments": json.dumps({"cmd": "cargo test --manifest-path sample/Cargo.toml"}),
            },
            "2026-06-15T12:00:04Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-test",
                "output": "Process exited with code 0\n2 passed",
            },
            "2026-06-15T12:00:05Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "message",
                "content": "The sample project has one TODO and the test suite passes.",
            },
            "2026-06-15T12:00:06Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "user_message",
                "content": "Check whether the example release link touches a network domain.",
            },
            "2026-06-15T12:01:00Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call",
                "name": "exec_command",
                "call_id": "call-curl",
                "arguments": json.dumps({"cmd": "curl -I https://github.com/example/project"}),
            },
            "2026-06-15T12:01:01Z",
        ),
        codex_line(
            "response_item",
            {
                "type": "function_call_output",
                "call_id": "call-curl",
                "output": "Process exited with code 0\nHTTP/2 200",
            },
            "2026-06-15T12:01:02Z",
        ),
        codex_line(
            "event_msg",
            {
                "type": "token_count",
                "info": {
                    "total_token_usage": {
                        "input_tokens": 1200,
                        "output_tokens": 180,
                        "cached_input_tokens": 64,
                    }
                },
            },
            "2026-06-15T12:01:03Z",
        ),
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {
        "schema": "r200-public-codex-fixture-v1",
        "path": str(path),
        "line_count": len(rows),
        "sha256": sha256_file(path),
        "contains_real_trace": False,
        "contains_private_prompt": False,
    }


def run_command(cmd: list[str], *, timeout: int) -> dict[str, Any]:
    start = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    elapsed = time.monotonic() - start
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "elapsed_s": round(elapsed, 3),
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def folded_total(path: Path) -> int:
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += int(line.rsplit(" ", 1)[1])
    return total


def verify_agentflame_output(out_dir: Path) -> dict[str, Any]:
    report_path = out_dir / "agentflame.json"
    tags_path = out_dir / "tags.json"
    report = read_json(report_path)
    artifacts = report.get("artifacts") or {}
    missing_keys = sorted(REQUIRED_ARTIFACT_KEYS - set(artifacts))
    missing_files = []
    for key in sorted(REQUIRED_ARTIFACT_KEYS & set(artifacts)):
        candidate = out_dir / str(artifacts[key])
        if not candidate.exists():
            missing_files.append(str(candidate))
    semantic_total = folded_total(out_dir / str(artifacts["semantic_system_folded"]))
    nonsemantic_total = folded_total(out_dir / str(artifacts["nonsemantic_system_folded"]))
    token_total = folded_total(out_dir / str(artifacts["semantic_token_folded"]))
    summary = report.get("summary") or {}
    system_weight = int((summary.get("system") or {}).get("total_weight") or 0)
    if missing_keys or missing_files:
        raise AssertionError(f"missing AgentFlame artifacts keys={missing_keys} files={missing_files}")
    if semantic_total != system_weight or nonsemantic_total != system_weight:
        raise AssertionError(
            f"folded system totals mismatch semantic={semantic_total} nonsemantic={nonsemantic_total} expected={system_weight}"
        )
    previews = report.get("prompt_tags") or []
    non_redacted_previews = [
        row.get("prompt_hash")
        for row in previews
        if row.get("preview") not in {None, "", "redacted"}
    ]
    if non_redacted_previews:
        raise AssertionError(f"prompt previews leaked in report: {non_redacted_previews[:5]}")
    return {
        "report_path": rel(report_path),
        "tags_path": rel(tags_path),
        "required_artifact_keys": sorted(REQUIRED_ARTIFACT_KEYS),
        "session_count": summary.get("session_count"),
        "raw_tool_events": summary.get("raw_tool_events"),
        "raw_llm_events": summary.get("raw_llm_events"),
        "system_observations": system_weight,
        "semantic_system_total": semantic_total,
        "nonsemantic_system_total": nonsemantic_total,
        "token_total": token_total,
        "llm_tagger": report.get("llm_tagger") or {},
        "prompt_preview_rows": len(previews),
        "non_redacted_prompt_preview_count": len(non_redacted_previews),
        "artifacts": {key: rel(out_dir / value) for key, value in artifacts.items()},
    }


def build_command(out_dir: Path, fixture: Path, llama_url: str, model: str, timeout_s: int) -> list[str]:
    return [
        "cargo",
        "run",
        "--manifest-path",
        "agentflame/Cargo.toml",
        "--",
        "run",
        "--project-root",
        str(REPO_ROOT),
        "--project-name",
        "agentsight-public-fixture",
        "--out",
        str(out_dir),
        "--session-file",
        str(fixture),
        "--llama-url",
        llama_url,
        "--model",
        model,
        "--timeout",
        str(timeout_s),
        "--scan-files",
        "1",
        "--max-sessions",
        "1",
    ]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R200 Community Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Run Summary",
        "",
        f"- Clean run return code: `{payload['runs']['clean']['returncode']}`.",
        f"- Cached run return code: `{payload['runs']['cached']['returncode']}`.",
        f"- Clean llama.cpp calls: `{payload['agentflame']['clean']['llm_tagger'].get('llm_calls')}`.",
        f"- Cached llama.cpp calls: `{payload['agentflame']['cached']['llm_tagger'].get('llm_calls')}`.",
        f"- Cached cache hits: `{payload['agentflame']['cached']['llm_tagger'].get('cache_hits')}`.",
        f"- System observations: `{payload['agentflame']['cached']['system_observations']}`.",
        "",
        "## Privacy",
        "",
        f"- Reads real `.codex`/`.claude` traces: `{payload['privacy']['reads_real_agent_traces']}`.",
        f"- Fixture contains private prompts: `{payload['fixture']['contains_private_prompt']}`.",
        f"- Non-redacted prompt previews in committed report: `{payload['agentflame']['cached']['non_redacted_prompt_preview_count']}`.",
        "",
        "## Gate",
        "",
        f"- C7 artifact smoke passed: `{payload['claim_gate']['c7_artifact_smoke_passed']}`.",
        f"- Community adoption supported: `{payload['claim_gate']['community_adoption_supported']}`.",
        f"- C5/C6 supported: `{payload['claim_gate']['c5_or_c6_supported']}`.",
        "",
        "## Boundary",
        "",
        "R200 is a public-safe artifact smoke over a generated fixture. It does not replace full-history traces, C5 participant evidence, or C6 human tag labels.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    before_dirty = git_status_paths()
    run_label = datetime.now(timezone.utc).strftime("r200-%Y%m%d-%H%M%S")
    local_out = REPO_ROOT / ".agentsight/agentflame" / run_label
    local_out.mkdir(parents=True, exist_ok=True)
    proc: subprocess.Popen[str] | None = None
    with tempfile.TemporaryDirectory(prefix="agentsight-r200-") as tmp:
        tmpdir = Path(tmp)
        fixture = tmpdir / "public-fixture/codex/sessions/2026/06/15/r200-public-codex.jsonl"
        fixture_info = write_public_codex_fixture(fixture)
        proc, llama_url, llama_info = start_llama(args, local_out)
        if llama_info.get("status") not in {None, "ready"} and not args.llama_url:
            return {
                "schema_version": 1,
                "run_id": "R200",
                "status": "blocked_no_llama",
                "generated_at": now_iso(),
                "fixture": fixture_info,
                "llama": llama_info,
                "claim_gate": {
                    "c7_artifact_smoke_passed": False,
                    "community_adoption_supported": False,
                    "c5_or_c6_supported": False,
                },
                "claim_boundary": "R200 could not run because a llama.cpp server/model was unavailable. This is not C7 evidence.",
            }
        try:
            command = build_command(local_out, fixture, llama_url, args.model_name, args.timeout)
            clean = run_command(command, timeout=args.command_timeout)
            if clean["returncode"] != 0:
                status = "agentflame_clean_failed"
                cached = {
                    "cmd": command,
                    "returncode": None,
                    "elapsed_s": None,
                    "stdout_tail": "",
                    "stderr_tail": "clean run failed; cached run skipped",
                }
                clean_report = {}
                cached_report = {}
            else:
                clean_report = verify_agentflame_output(local_out)
                clean_json = local_out / "agentflame.clean.json"
                clean_json.write_text((local_out / "agentflame.json").read_text(encoding="utf-8"), encoding="utf-8")
                cached = run_command(command, timeout=args.command_timeout)
                if cached["returncode"] != 0:
                    status = "agentflame_cached_failed"
                    cached_report = {}
                else:
                    cached_report = verify_agentflame_output(local_out)
                    clean_calls = int((clean_report.get("llm_tagger") or {}).get("llm_calls") or 0)
                    cached_calls = int((cached_report.get("llm_tagger") or {}).get("llm_calls") or 0)
                    cached_requests = int((cached_report.get("llm_tagger") or {}).get("requests") or 0)
                    cached_hits = int((cached_report.get("llm_tagger") or {}).get("cache_hits") or 0)
                    status = (
                        "community_smoke_passed"
                        if clean_calls > 0 and cached_calls == 0 and cached_hits == cached_requests
                        else "community_smoke_failed_cache_gate"
                    )
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)

    after_dirty = git_status_paths()
    new_dirty = sorted(after_dirty - before_dirty)
    raw_trace_dirty = [
        path
        for path in new_dirty
        if ".codex/" in path or ".claude/" in path or path.endswith(".jsonl")
    ]
    if raw_trace_dirty and status == "community_smoke_passed":
        status = "community_smoke_failed_raw_trace_dirty"

    payload = {
        "schema_version": 1,
        "run_id": "R200",
        "status": status,
        "generated_at": now_iso(),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(after_dirty),
            "script": rel(Path(__file__)),
            "script_sha256": sha256_file(Path(__file__)),
        },
        "fixture": {
            **fixture_info,
            "path": "temporary public Codex fixture removed after run",
        },
        "llama": llama_info,
        "runs": {
            "clean": clean,
            "cached": cached,
        },
        "agentflame": {
            "local_out": rel(local_out),
            "clean": clean_report,
            "cached": cached_report,
        },
        "privacy": {
            "reads_real_agent_traces": False,
            "session_file_explicit": True,
            "generated_fixture_removed": True,
            "new_dirty_raw_trace_paths": raw_trace_dirty,
            "committed_summary_contains_raw_prompts": False,
            "local_agentflame_report_public_release_ready": False,
        },
        "write_set": {
            "new_git_dirty_paths": new_dirty,
            "new_dirty_raw_trace_paths": raw_trace_dirty,
            "local_output_under_agentsight": rel(local_out),
        },
        "claim_gate": {
            "c7_artifact_smoke_passed": status == "community_smoke_passed",
            "community_adoption_supported": False,
            "c5_or_c6_supported": False,
            "requires_external_developer_feedback": True,
            "requires_real_human_outcomes_for_c5_c6": True,
        },
        "claim_boundary": (
            "R200 verifies a public-safe generated-fixture AgentFlame run, output completeness, "
            "prompt redaction, and fixed-input cache behavior. It is C7 artifact-hygiene evidence only; "
            "it does not support C5 developer utility, C6 tag adequacy, full-history exact lineage, or community adoption."
        ),
    }
    replacements = [
        (str(REPO_ROOT), "<repo>"),
        (str(tmpdir), "<tmp>"),
        (str(Path.home()), "~"),
    ]
    return sanitize_value(payload, replacements)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--llama-url", default="")
    parser.add_argument("--llama-server", default=str(DEFAULT_LLAMA_SERVER))
    parser.add_argument("--model-path", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--model-name", default="r200-local")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ctx-size", type=int, default=2048)
    parser.add_argument("--load-timeout", type=int, default=240)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--command-timeout", type=int, default=240)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(args)
    write_json(args.out_json, payload)
    if payload["status"] != "blocked_no_llama":
        write_markdown(args.out_md, payload)
    else:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(
            "# R200 Community Smoke\n\n"
            "Status: `blocked_no_llama`\n\n"
            "A llama.cpp server/model was not available, so no C7 artifact smoke evidence was produced.\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "c7_artifact_smoke_passed": payload["claim_gate"]["c7_artifact_smoke_passed"],
                "community_adoption_supported": payload["claim_gate"]["community_adoption_supported"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
