#!/usr/bin/env python3
"""Reviewed Harness Bench checkpoint/fork experiment driver.

`--prepare-only` is deliberately model-free. It verifies the pinned benchmark,
builds a two-session checkpoint fixture, constructs the Rust source store,
starts each broker in dry verification mode, independently recomputes every
Trajectory dry response, and proves stable fork-visible state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any


BENCHMARK_REVISION = "1025086a446653702b80cfb48babbeec35db6b2c"
CHECKPOINT_SCHEMA = "agent-nebula-harness-checkpoint-v1"
SELECTED_TASKS = (
    "057-interruption-resume",
    "058-multiday-project-state",
    "059-event-update-replan",
    "060-task-cancellation-cleanup",
    "103-policy-update-replan-diff",
    "105-partial-batch-resume-ledger",
)
SUPERVISOR_ARGS = (
    "--seed", "20260721",
    "--context-tokens", "65536",
    "--reserve-output-tokens", "2048",
    "--evidence-tokens", "16384",
    "--evidence-bytes", "65536",
    "--response-tokens", "2048",
    "--response-bytes", "8192",
    "--max-tool-calls", "24",
    "--timeout-seconds", "1200",
)

NEUTRAL_ADVICE_OPEN = "<automatic_supervisor_advice>"
NEUTRAL_ADVICE_CLOSE = "</automatic_supervisor_advice>"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print("[prepare]", " ".join(command), flush=True)
    return subprocess.run(command, cwd=cwd, text=True, check=True, capture_output=False)


def git_revision(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()


def load_harness(benchmark: Path) -> tuple[dict[str, Any], Any]:
    sys.path.insert(0, str(benchmark / "src"))
    from harnessbench.grading.task_outcome_llm_weights import (  # type: ignore
        outcome_llm_weight_for_task,
    )
    from harnessbench.tasks import load_tasks  # type: ignore

    return load_tasks(benchmark / "tasks"), outcome_llm_weight_for_task


def validate_benchmark(benchmark: Path) -> dict[str, Any]:
    if git_revision(benchmark) != BENCHMARK_REVISION:
        raise RuntimeError("Harness Bench revision does not match the registered plan")
    tasks, outcome_weight = load_harness(benchmark)
    hashes: dict[str, Any] = {}
    for task_id in SELECTED_TASKS:
        task = tasks.get(task_id)
        if task is None or task.task_dir is None:
            raise RuntimeError(f"missing registered Harness Bench task {task_id}")
        if float(outcome_weight(task_id)) != 0.0:
            raise RuntimeError(f"registered task has nonzero LLM outcome weight: {task_id}")
        paths = [
            task.task_dir / "task.yaml",
            task.task_dir / task.oracle_module,
            task.task_dir / task.hooks_module,
        ] + [task.task_dir / name for name in (task.prompt_files or [task.prompt_file])]
        for path in paths:
            if not path.is_file():
                raise RuntimeError(f"registered benchmark asset is missing: {path}")
        hashes[task_id] = {
            str(path.relative_to(benchmark)): sha256_file(path) for path in paths
        }
    return hashes


def manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        row: dict[str, Any] = {
            "path": relative,
            "type": (
                "symlink"
                if stat.S_ISLNK(info.st_mode)
                else "directory"
                if stat.S_ISDIR(info.st_mode)
                else "file"
                if stat.S_ISREG(info.st_mode)
                else "other"
            ),
            "mode": info.st_mode,
            "mtime_ns": info.st_mtime_ns,
        }
        if row["type"] == "file":
            row["size"] = info.st_size
            row["sha256"] = sha256_file(path)
        elif row["type"] == "symlink":
            row["target"] = os.readlink(path)
        rows.append(row)
    return rows


def write_snapshot(root: Path, files: dict[str, str], *, symlink: bool = False) -> None:
    tree = root / "tree"
    tree.mkdir(parents=True)
    for name, content in files.items():
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if symlink:
        (tree / "latest").symlink_to("results.json")
    write_json(root / "manifest.json", manifest(tree))


def capture_snapshot(workspace: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"snapshot already exists: {destination}")
    shutil.copytree(workspace, destination / "tree", symlinks=True, copy_function=shutil.copy2)
    write_json(destination / "manifest.json", manifest(destination / "tree"))


def sanitized_codex_config(workspace: Path, sandbox: Path, real_codex: Path) -> str:
    def quoted(value: Path | str) -> str:
        return json.dumps(str(value), ensure_ascii=False)

    tool_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    return "\n".join(
        [
            'default_permissions = "experiment"',
            'approval_policy = "never"',
            "",
            "[permissions.experiment.filesystem]",
            '":minimal" = "read"',
            f"{quoted(real_codex)} = \"read\"",
            f"{quoted(workspace)} = \"write\"",
            f"{quoted(sandbox)} = \"none\"",
            "",
            "[permissions.experiment.network]",
            "enabled = false",
            "",
            "[shell_environment_policy]",
            'inherit = "none"',
            "set = { "
            + f"PATH = {quoted(tool_path)}, "
            + f"HOME = {quoted('/unavailable')}, "
            + f"CODEX_HOME = {quoted('/unavailable')}, "
            + f"WORKSPACE = {quoted(workspace)}, "
            + f"TMPDIR = {quoted(workspace / '.tmp')} "
            + "}",
            "",
            "[features]",
            "apps = false",
            "enable_mcp_apps = false",
            "plugins = false",
            "hooks = false",
            "browser_use = false",
            "image_generation = false",
            "multi_agent = false",
            "standalone_web_search = false",
            "",
        ]
    )


def make_ephemeral_codex_source(
    original_config: Path, workspace: Path, sandbox: Path, real_codex: Path
) -> tempfile.TemporaryDirectory[str]:
    temporary = tempfile.TemporaryDirectory(prefix="agent-nebula-codex-")
    root = Path(temporary.name)
    (root / "config.toml").write_text(
        sanitized_codex_config(workspace, sandbox, real_codex), encoding="utf-8"
    )
    source_home = original_config.expanduser().resolve().parent
    copied = 0
    for name in ("auth.json", "credentials.json", "organization.json"):
        source = source_home / name
        if source.is_file():
            shutil.copy2(source, root / name)
            os.chmod(root / name, 0o600)
            copied += 1
    if copied == 0:
        temporary.cleanup()
        raise RuntimeError("no Codex credential file is available for the trusted controller")
    return temporary


def purge_runtime_credentials(sandbox: Path) -> None:
    """Remove controller credentials that Codex may copy into its runtime home."""
    codex_home = sandbox / ".codex"
    for name in ("auth.json", "credentials.json", "organization.json"):
        path = codex_home / name
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def worker_model_config(
    wrapper: Path, user_config: Path, model: str, reasoning_effort: str
) -> dict[str, Any]:
    return {
        "adapter": "codex",
        "command": str(wrapper),
        "user_config": str(user_config),
        "model": model,
        "model_reasoning_effort": reasoning_effort,
        "sandbox": "workspace-write",
        # Codex 0.144.6 reads approval_policy from strict config; its exec CLI
        # no longer accepts Harness Bench's legacy --ask-for-approval flag.
        "ask_for_approval": "",
        "json": True,
        "stream_to_console": False,
        "config_overrides": [],
        "extra_args": ["--strict-config", "--ignore-rules"],
    }


def expected_adapter_command(
    wrapper: Path, workspace: Path, sandbox: Path, model: str
) -> list[str]:
    return [
        str(wrapper), "exec", "--cd", str(workspace), "--skip-git-repo-check",
        "--sandbox", "workspace-write", "--output-last-message",
        str(sandbox / "codex-last-message.txt"), "--json", "--model", model,
        "--strict-config", "--ignore-rules", "-",
    ]


def synthetic_session(round_index: int, path: str) -> str:
    timestamp = f"2026-07-21T0{round_index}:00:0"
    patch = (
        'const patch = "*** Begin Patch\\n*** Update File: '
        f'/workspace/{path}\\n@@\\n-old\\n+new\\n*** End Patch"; '
        "tools.apply_patch(patch)"
    )
    rows = [
        {
            "timestamp": timestamp + "0Z",
            "type": "session_meta",
            "payload": {"id": f"fixture-session-{round_index}", "cwd": "/workspace"},
        },
        {
            "timestamp": timestamp + "1Z",
            "type": "turn_context",
            "payload": {"model": "gpt-5.6-sol", "cwd": "/workspace"},
        },
        {
            "timestamp": timestamp + "2Z",
            "type": "event_msg",
            "payload": {"type": "user_message", "message": f"round {round_index}"},
        },
        {
            "timestamp": timestamp + "3Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "exec",
                "call_id": f"call-{round_index}",
                "input": patch,
            },
        },
        {
            "timestamp": timestamp + "4Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "call_id": f"call-{round_index}",
                "output": [{"type": "input_text", "text": "Script completed\nOutput:\n{}"}],
            },
        },
    ]
    return "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows)


def create_fixture_checkpoint(root: Path) -> Path:
    if root.exists():
        shutil.rmtree(root)
    (root / "sessions").mkdir(parents=True)
    (root / "prompts").mkdir()
    (root / "logs").mkdir()
    (root / "snapshots").mkdir()
    (root / "sessions/round-001.jsonl").write_text(
        synthetic_session(1, "README.md"), encoding="utf-8"
    )
    (root / "sessions/round-002.jsonl").write_text(
        synthetic_session(2, "results.json"), encoding="utf-8"
    )
    (root / "prompts/round-001.txt").write_text("Create the initial state.\n", encoding="utf-8")
    (root / "prompts/round-002.txt").write_text("Update the measured state.\n", encoding="utf-8")
    (root / "prompts/next.txt").write_text(
        "Review the existing work, preserve correct state, and finish the remaining task.\n",
        encoding="utf-8",
    )
    (root / "logs/round-001.jsonl").write_text('{"ok":true,"round":1}\n', encoding="utf-8")
    (root / "logs/round-002.jsonl").write_text('{"ok":true,"round":2}\n', encoding="utf-8")
    write_snapshot(
        root / "snapshots/round-001",
        {"README.md": "old\n", "src/main.rs": "fn main() {}\n"},
    )
    write_snapshot(
        root / "snapshots/round-002",
        {
            "README.md": "new\n",
            "src/main.rs": "fn main() {}\n",
            "results.json": '{"state":"ready"}\n',
        },
        symlink=True,
    )
    rounds = []
    for index in (1, 2):
        scope = f"round-{index:03d}"
        rounds.append(
            {
                "scope_id": scope,
                "session_id": f"fixture-session-{index}",
                "prompt_file": f"prompts/{scope}.txt",
                "session_file": f"sessions/{scope}.jsonl",
                "adapter_logs": [f"logs/{scope}.jsonl"],
                "snapshot_manifest": f"snapshots/{scope}/manifest.json",
                "snapshot_tree": f"snapshots/{scope}/tree",
            }
        )
    write_json(
        root / "checkpoint.json",
        {
            "schema": CHECKPOINT_SCHEMA,
            "episode_id": "fixture-058-prefix",
            "domain": "harness-bench",
            "next_prompt_file": "prompts/next.txt",
            "rounds": rounds,
        },
    )
    return root


def restore_stable_slot(checkpoint: Path, output: Path) -> dict[str, Any]:
    source = checkpoint / "snapshots/round-002/tree"
    slot = output / "stable-slot"
    manifests = []
    prompt_hashes = []
    argv_hashes = []
    env_hashes = []
    prompt = (checkpoint / "prompts/next.txt").read_bytes()
    argv = [
        "codex", "exec", "--cd", "/workspace", "--skip-git-repo-check",
        "--sandbox", "workspace-write", "--strict-config", "-",
    ]
    environment = {
        "HOME": "/sandbox",
        "CODEX_HOME": "/codex-home",
        "WORKSPACE": "/workspace",
        "HARNESSBENCH_WORKSPACE": "/workspace",
        "HARNESSBENCH_SANDBOX": "/sandbox",
        "HARNESSBENCH_PROMPT_FILE": "/prompt",
    }
    for _ in range(4):
        if slot.exists():
            shutil.rmtree(slot)
        shutil.copytree(source, slot, symlinks=True, copy_function=shutil.copy2)
        manifests.append(manifest(slot))
        prompt_hashes.append(sha256_bytes(prompt))
        argv_hashes.append(sha256_bytes(json.dumps(argv, separators=(",", ":")).encode()))
        env_hashes.append(sha256_bytes(json.dumps(environment, sort_keys=True).encode()))
    if not (all(value == manifests[0] for value in manifests[1:])
            and len(set(prompt_hashes)) == len(set(argv_hashes)) == len(set(env_hashes)) == 1):
        raise RuntimeError("stable execution-slot parity failed")
    result = {
        "logical_forks": 4,
        "manifest_sha256": sha256_bytes(json.dumps(manifests[0], sort_keys=True).encode()),
        "prompt_sha256": prompt_hashes[0],
        "argv_sha256": argv_hashes[0],
        "environment_sha256": env_hashes[0],
        "worker_visible_paths": ["/workspace", "/sandbox", "/prompt", "/codex-home"],
    }
    write_json(output / "fork-parity.json", result)
    return result


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def recompute_session_diff(
    boundaries: dict[str, list[dict[str, Any]]], source_ids: set[str], from_scope: str, to_scope: str
) -> dict[str, Any]:
    before = {
        row["path"]: row for row in boundaries[from_scope] if row["type"] != "directory"
    }
    after = {
        row["path"]: row for row in boundaries[to_scope] if row["type"] != "directory"
    }
    changes = []
    for path in sorted(before.keys() | after.keys()):
        left = before.get(path)
        right = after.get(path)
        left_entry = {key: value for key, value in (left or {}).items() if key != "evidence_id"} or None
        right_entry = {key: value for key, value in (right or {}).items() if key != "evidence_id"} or None
        if left_entry == right_entry:
            continue
        relation = "added" if left is None else "removed" if right is None else "changed"
        raw_ids = sorted(
            row["evidence_id"] for row in (left, right) if row is not None
        )
        if not set(raw_ids) <= source_ids:
            raise RuntimeError("session_diff cites an unknown Raw ID")
        changes.append(
            {
                "path": path,
                "relation": relation,
                "before": left_entry,
                "after": right_entry,
                "raw_ids": raw_ids,
            }
        )
    return {"from_session": from_scope, "to_session": to_scope, "changes": changes}


def verify_trajectory_fields(store: Path, verification: Path) -> dict[str, Any]:
    records = load_jsonl(store / "raw.jsonl")
    actions = load_jsonl(store / "actions.jsonl")
    boundaries = json.loads((store / "boundaries.json").read_text(encoding="utf-8"))
    source_ids = {row["id"] for row in records}
    dry = {
        row["tool"]: row for row in json.loads(verification.read_text(encoding="utf-8"))["dry_responses"]
    }
    diff_call = dry["session_diff"]
    expected_diff = recompute_session_diff(
        boundaries,
        source_ids,
        diff_call["arguments"]["from_session"],
        diff_call["arguments"]["to_session"],
    )
    if diff_call["response"]["result"] != expected_diff:
        raise RuntimeError("session_diff failed field-by-field Raw recomputation")

    effect_call = dry.get("effects")
    if effect_call:
        action_id = effect_call["arguments"]["action_id"]
        action = next(row for row in actions if row["id"] == action_id)
        expected_effect = {
            "action_id": action["id"],
            "scope_id": action["scope_id"],
            "closure": action["closure"],
            "effects": action["effects"],
            "raw_ids": action["raw_ids"],
        }
        if effect_call["response"]["result"] != expected_effect:
            raise RuntimeError("effects failed field-by-field Raw recomputation")
        cited = set(action["raw_ids"])
        for effect in action["effects"]:
            cited.update(effect["evidence_ids"])
        if not cited <= source_ids:
            raise RuntimeError("effects cites an unknown Raw ID")

    history_call = dry["artifact_history"]
    path = history_call["arguments"]["path"]
    expected_actions = []
    for action in actions:
        effects = [
            effect for effect in action["effects"]
            if effect["path"] == path or effect.get("previous_path") == path
        ]
        if effects:
            expected_actions.append(
                {
                    "kind": "action", "action_id": action["id"],
                    "scope_id": action["scope_id"], "ts_ns": action["ts_ns"],
                    "end_ns": action["end_ns"], "status": action["status"],
                    "closure": action["closure"], "effects": effects,
                    "raw_ids": action["raw_ids"],
                }
            )
    expected_snapshots = []
    for scope in json.loads((store / "store.json").read_text(encoding="utf-8"))["scopes"]:
        match = next((row for row in boundaries[scope["id"]] if row["path"] == path), None)
        if match:
            entry = {key: value for key, value in match.items() if key != "evidence_id"}
            expected_snapshots.append(
                {"kind": "snapshot_state", "scope_id": scope["id"],
                 "entry": entry, "raw_ids": [match["evidence_id"]]}
            )
    expected_history = {
        "requested_path": path,
        "actions": expected_actions,
        "snapshot_states": expected_snapshots,
    }
    if history_call["response"]["result"] != expected_history:
        raise RuntimeError("artifact_history failed field-by-field Raw recomputation")
    return {
        "raw_records": len(records),
        "actions": len(actions),
        "checked_tools": ["artifact_history", "session_diff", "effects"],
        "unknown_source_ids": 0,
    }


def prepare_only(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    benchmark = args.benchmark.resolve()
    benchmark_hashes = validate_benchmark(benchmark)
    print("[prepare] hashing the pinned supervisor model once", flush=True)
    supervisor_model_sha256 = sha256_file(args.supervisor_model)
    checkpoint = create_fixture_checkpoint(output / "checkpoint-fixture")
    parity = restore_stable_slot(checkpoint, output)
    store = output / "store"
    run([str(args.agentvis_bin), "research-store", "--source", str(checkpoint),
         "--output", str(store), "--verify"])
    broker_outputs: dict[str, Any] = {}
    for condition in ("generic", "raw", "trajectory"):
        destination = output / f"broker-{condition}"
        command = [
            str(args.agentvis_bin), "research-supervisor",
            "--store", str(store), "--condition", condition,
            "--base-url", "http://127.0.0.1:1/v1",
            "--model", str(args.supervisor_model.resolve()),
            "--model-sha256", supervisor_model_sha256,
            *SUPERVISOR_ARGS,
            "--output", str(destination), "--verify-only",
        ]
        run(command)
        broker_outputs[condition] = json.loads(
            (destination / "verification.json").read_text(encoding="utf-8")
        )
    shared = [
        (row["model_sha256"], row["source_store_sha256"], row["raw_ids_sha256"], row["frozen_args"])
        for row in broker_outputs.values()
    ]
    if any(value != shared[0] for value in shared[1:]):
        raise RuntimeError("broker model/source/budget parity failed")
    field_audit = verify_trajectory_fields(
        store, output / "broker-trajectory/verification.json"
    )
    report = {
        "schema": "agent-nebula-harness-prepare-v1",
        "status": "PASS",
        "model_calls": 0,
        "benchmark_calls": 0,
        "benchmark_revision": BENCHMARK_REVISION,
        "benchmark_assets": benchmark_hashes,
        "agentvis_binary": str(args.agentvis_bin.resolve()),
        "agentvis_sha256": sha256_file(args.agentvis_bin),
        "supervisor_model_sha256": supervisor_model_sha256,
        "fork_parity": parity,
        "broker_conditions": broker_outputs,
        "trajectory_field_audit": field_audit,
    }
    write_json(output / "prepare-report.json", report)
    print(f"[prepare] PASS -> {output / 'prepare-report.json'}", flush=True)


def native_session_id(path: Path) -> str:
    for row in load_jsonl(path):
        if row.get("type") != "session_meta":
            continue
        payload = row.get("payload") or {}
        session_id = str(payload.get("id") or "").strip()
        if session_id:
            return session_id
    raise RuntimeError(f"native Codex session has no session_meta id: {path}")


def load_runtime_modules(benchmark: Path) -> dict[str, Any]:
    sys.path.insert(0, str(benchmark / "src"))
    from harnessbench.adapters.codex import CodexAdapter  # type: ignore
    from harnessbench.models import AdapterRunContext  # type: ignore
    from harnessbench.runner import _copy_fixtures, render_prompt_file  # type: ignore
    from harnessbench.tasks import load_hooks, load_tasks, run_oracle  # type: ignore

    return {
        "CodexAdapter": CodexAdapter,
        "AdapterRunContext": AdapterRunContext,
        "copy_fixtures": _copy_fixtures,
        "render_prompt_file": render_prompt_file,
        "load_hooks": load_hooks,
        "load_tasks": load_tasks,
        "run_oracle": run_oracle,
    }


def run_adapter_round(
    runtime: dict[str, Any],
    *,
    task: Any,
    workspace: Path,
    sandbox: Path,
    prompt: str,
    prompt_file: Path,
    session_id: str,
    model_config: dict[str, Any],
    model_id: str,
    real_codex: Path,
    timeout_sec: int,
) -> Any:
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")
    env = {"AGENT_NEBULA_CODEX_REAL": str(real_codex)}
    context = runtime["AdapterRunContext"](
        task=task,
        workspace=workspace,
        sandbox=sandbox,
        prompt=prompt,
        prompt_file=prompt_file,
        session_id=session_id,
        timeout_sec=timeout_sec,
        env=env,
        model_id=model_id,
        model_config=model_config,
        mode="agent-nebula-p0",
    )
    try:
        result = runtime["CodexAdapter"]().run(context)
    finally:
        purge_runtime_credentials(sandbox)
    if not result.ok:
        raise RuntimeError(
            f"official Codex adapter failed: returncode={result.metadata.get('returncode')} "
            f"timed_out={result.metadata.get('timed_out')} stderr={result.stderr[-2000:]}"
        )
    session = Path(str(result.metadata.get("codex_session_file") or ""))
    if not session.is_file():
        raise RuntimeError("official Codex adapter did not retain a native session file")
    return result


def copy_adapter_evidence(result: Any, root: Path, scope: str) -> tuple[str, list[str]]:
    sessions = root / "sessions"
    logs = root / "logs"
    sessions.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    source_session = Path(result.metadata["codex_session_file"])
    session_target = sessions / f"{scope}.jsonl"
    shutil.copy2(source_session, session_target)
    log_targets: list[str] = []
    for key, suffix in (("stdout_log_file", "stdout.jsonl"), ("stderr_log_file", "stderr.log")):
        source = Path(str(result.metadata.get(key) or ""))
        if not source.is_file():
            continue
        target = logs / f"{scope}.{suffix}"
        shutil.copy2(source, target)
        log_targets.append(target.relative_to(root).as_posix())
    return native_session_id(session_target), log_targets


def build_real_prefix(
    args: argparse.Namespace,
    runtime: dict[str, Any],
    task: Any,
    root: Path,
    workspace: Path,
    sandbox: Path,
) -> tuple[Path, str, list[dict[str, Any]], dict[str, Any]]:
    checkpoint = root / "checkpoint"
    checkpoint.mkdir(parents=True)
    (checkpoint / "prompts").mkdir()
    (checkpoint / "snapshots").mkdir()
    args.codex_wrapper.chmod(args.codex_wrapper.stat().st_mode | stat.S_IXUSR)
    runtime["copy_fixtures"](task, workspace)
    hooks = runtime["load_hooks"](task)
    runtime_state: dict[str, Any] = {}
    runtime_env: dict[str, str] = {}
    if hooks and callable(getattr(hooks, "prepare_runtime", None)):
        state = hooks.prepare_runtime({"task": task, "sandbox": sandbox, "workspace": workspace})
        if isinstance(state, dict):
            runtime_state.update(state)
            runtime_env.update({key: value for key, value in state.items() if isinstance(value, str)})

    prompt_names = list(task.prompt_files or []) or [task.prompt_file]
    if len(prompt_names) < 2:
        raise RuntimeError("checkpoint continuation requires at least two fresh rounds")
    round_rows: list[dict[str, Any]] = []
    command_rows: list[dict[str, Any]] = []
    with make_ephemeral_codex_source(
        args.worker_user_config, workspace, sandbox, args.codex_bin
    ) as source_home:
        model_config = worker_model_config(
            args.codex_wrapper, Path(source_home) / "config.toml",
            args.worker_model, args.worker_reasoning_effort,
        )
        for index, prompt_name in enumerate(prompt_names[:-1], start=1):
            scope = f"round-{index:03d}"
            prompt = runtime["render_prompt_file"](
                task, prompt_name, workspace, runtime_env, "codex"
            )
            prompt_target = checkpoint / "prompts" / f"{scope}.txt"
            prompt_target.write_text(prompt, encoding="utf-8")
            result = run_adapter_round(
                runtime,
                task=task,
                workspace=workspace,
                sandbox=sandbox,
                prompt=prompt,
                prompt_file=sandbox / f"prompt-{scope}.txt",
                session_id=f"agent-nebula-{task.task_id}-prefix",
                model_config=model_config,
                model_id=args.worker_model,
                real_codex=args.codex_bin,
                timeout_sec=task.timeout_sec,
            )
            if hooks and callable(getattr(hooks, "after_round", None)):
                state = hooks.after_round(
                    {
                        "task": task,
                        "sandbox": sandbox,
                        "workspace": workspace,
                        "session_id": f"agent-nebula-{task.task_id}-prefix",
                        "round_index": index - 1,
                        "prompt_file": sandbox / f"prompt-{scope}.txt",
                        "prompt_name": prompt_name,
                    },
                    runtime_state,
                    result,
                )
                if isinstance(state, dict):
                    runtime_state.update(state)
                    runtime_env.update({key: value for key, value in state.items() if isinstance(value, str)})
            snapshot = checkpoint / "snapshots" / scope
            capture_snapshot(workspace, snapshot)
            session_id, logs = copy_adapter_evidence(result, checkpoint, scope)
            round_rows.append(
                {
                    "scope_id": scope,
                    "session_id": session_id,
                    "prompt_file": f"prompts/{scope}.txt",
                    "session_file": f"sessions/{scope}.jsonl",
                    "adapter_logs": logs,
                    "snapshot_manifest": f"snapshots/{scope}/manifest.json",
                    "snapshot_tree": f"snapshots/{scope}/tree",
                }
            )
            command_rows.append(
                {
                    "round": index,
                    "session_id": session_id,
                    "command": result.command,
                    "metadata": {
                        "returncode": result.metadata.get("returncode"),
                        "timed_out": result.metadata.get("timed_out"),
                    },
                }
            )
            print(f"[p0] prefix round {index}/{len(prompt_names)-1} complete: {session_id}", flush=True)

    next_prompt = runtime["render_prompt_file"](
        task, prompt_names[-1], workspace, runtime_env, "codex"
    )
    (checkpoint / "prompts" / "next.txt").write_text(next_prompt, encoding="utf-8")
    write_json(
        checkpoint / "checkpoint.json",
        {
            "schema": CHECKPOINT_SCHEMA,
            "episode_id": f"{task.task_id}-p0-prefix",
            "domain": "harness-bench",
            "next_prompt_file": "prompts/next.txt",
            "rounds": round_rows,
        },
    )
    write_json(checkpoint / "prefix-commands.json", command_rows)
    return checkpoint, next_prompt, command_rows, runtime_state


def shell_tool_seen(session: Path) -> bool:
    for row in load_jsonl(session):
        payload = row.get("payload") or {}
        if row.get("type") != "response_item":
            continue
        if payload.get("type") in {"function_call", "custom_tool_call"} and str(
            payload.get("name") or ""
        ) in {"shell_command", "exec", "exec_command"}:
            return True
    return False


def run_isolation_probe(
    args: argparse.Namespace,
    runtime: dict[str, Any],
    task: Any,
    output: Path,
    evidence_store: Path,
) -> dict[str, Any]:
    probe_root = output / "isolation-probe"
    if probe_root.exists():
        shutil.rmtree(probe_root)
    workspace = probe_root / "runtime" / "workspace"
    sandbox = probe_root / "runtime" / "sandbox"
    workspace.mkdir(parents=True)
    forbidden = {
        "benchmark": args.benchmark.resolve(),
        "ground_truth": (task.task_dir / "ground_truth.json").resolve(),
        "oracle": (task.task_dir / task.oracle_module).resolve(),
        "hooks": (task.task_dir / task.hooks_module).resolve(),
        "evidence_store": evidence_store.resolve(),
        "credential": (sandbox / ".codex" / "auth.json").resolve(),
    }
    script = workspace / "isolation_probe.sh"
    script.write_text(
        "#!/bin/sh\nset -u\n"
        "ok=true\n"
        "test -r ./visible.txt || ok=false\n"
        "printf workspace-write > ./write-test.txt || ok=false\n"
        + "\n".join(
            f"test ! -r {json.dumps(str(path))} || ok=false" for path in forbidden.values()
        )
        + "\ngetent hosts github.com >/dev/null 2>&1 && ok=false\n"
        "curl -fsS --connect-timeout 3 https://github.com/ >/dev/null 2>&1 && ok=false\n"
        "curl -fsS --connect-timeout 3 https://raw.githubusercontent.com/ >/dev/null 2>&1 && ok=false\n"
        "curl -fsS --connect-timeout 3 https://example.com/ >/dev/null 2>&1 && ok=false\n"
        "if [ \"$ok\" = true ]; then\n"
        "  printf '%s\\n' '{\"workspace_read\":true,\"workspace_write\":true,\"hidden_paths_unreadable\":true,\"dns_blocked\":true,\"network_blocked\":true}' > isolation-result.json\n"
        "  exit 0\n"
        "fi\n"
        "printf '%s\\n' '{\"workspace_read\":false,\"workspace_write\":false,\"hidden_paths_unreadable\":false,\"dns_blocked\":false,\"network_blocked\":false}' > isolation-result.json\n"
        "exit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    (workspace / "visible.txt").write_text("visible\n", encoding="utf-8")

    with make_ephemeral_codex_source(
        args.worker_user_config, workspace, sandbox, args.codex_bin
    ) as source_home:
        config = worker_model_config(
            args.codex_wrapper, Path(source_home) / "config.toml",
            args.worker_model, args.worker_reasoning_effort,
        )
        result = run_adapter_round(
            runtime,
            task=task,
            workspace=workspace,
            sandbox=sandbox,
            prompt="Run ./isolation_probe.sh exactly once with a shell tool, then stop. Do not inspect other files.",
            prompt_file=sandbox / "prompt-isolation.txt",
            session_id="agent-nebula-isolation-probe",
            model_config=config,
            model_id=args.worker_model,
            real_codex=args.codex_bin,
            timeout_sec=300,
        )
        session = Path(result.metadata["codex_session_file"])
        probe_result = json.loads((workspace / "isolation-result.json").read_text(encoding="utf-8"))
        if not all(probe_result.values()) or not shell_tool_seen(session):
            raise RuntimeError("actual Codex tool-context isolation probe failed")
        direct = subprocess.run(
            [
                str(args.codex_bin), "sandbox", "-P", "experiment", "-C", str(workspace),
                "--", "sh", "-c",
                "test -r visible.txt && ! test -r \"$CODEX_HOME/auth.json\" && "
                "! getent hosts github.com >/dev/null 2>&1 && "
                "! curl -fsS --connect-timeout 3 https://example.com/ >/dev/null 2>&1",
            ],
            env={
                "HOME": str(sandbox),
                "CODEX_HOME": str(sandbox / ".codex"),
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            },
            cwd=workspace,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if direct.returncode != 0:
            raise RuntimeError(f"direct Codex sandbox probe failed: {direct.stderr[-1000:]}")
        retained = probe_root / "retained-session.jsonl"
        shutil.copy2(session, retained)
    report = {
        "status": "PASS",
        "actual_model_turn": True,
        "shell_tool_seen": True,
        "direct_profile_probe": True,
        "checks": probe_result,
        "forbidden_path_names": sorted(forbidden),
        "session_sha256": sha256_file(retained),
    }
    write_json(probe_root / "report.json", report)
    shutil.rmtree(probe_root / "runtime", ignore_errors=True)
    print("[p0] actual worker isolation probe PASS", flush=True)
    return report


def run_supervisor(
    args: argparse.Namespace,
    store: Path,
    condition: str,
    output: Path,
    model_sha256: str,
) -> dict[str, Any]:
    command = [
        str(args.agentvis_bin), "research-supervisor",
        "--store", str(store), "--condition", condition,
        "--base-url", args.supervisor_url,
        "--model", str(args.supervisor_model.resolve()),
        "--model-sha256", model_sha256,
        *SUPERVISOR_ARGS,
        "--output", str(output),
    ]
    print(f"[p0] supervisor {condition}", flush=True)
    subprocess.run(command, check=True, text=True)
    return json.loads((output / "intervention.json").read_text(encoding="utf-8"))


def load_complete_supervisors(root: Path, store: Path) -> tuple[dict[str, Any], str] | None:
    try:
        index = json.loads((store / "store.json").read_text(encoding="utf-8"))
        interventions: dict[str, Any] = {}
        model_hashes: set[str] = set()
        for condition in ("generic", "raw", "trajectory"):
            directory = root / condition
            intervention = json.loads(
                (directory / "intervention.json").read_text(encoding="utf-8")
            )
            ledger = json.loads((directory / "ledger.json").read_text(encoding="utf-8"))
            transcript = (directory / "transcript.jsonl").read_text(encoding="utf-8")
            exposed = set(ledger["exposed_source_ids"])
            if (
                ledger.get("condition") != condition
                or ledger.get("completed") is not True
                or ledger.get("source_store_sha256") != index["source_store_sha256"]
                or ledger.get("raw_ids_sha256") != index["raw_ids_sha256"]
                or not transcript.strip()
                or not set(intervention["source_ids"]) <= exposed
                or intervention["decision"] not in {"INTERVENE", "ABSTAIN"}
            ):
                return None
            model_hashes.add(ledger["model_sha256"])
            interventions[condition] = intervention
        if len(model_hashes) != 1:
            return None
        return interventions, model_hashes.pop()
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


def oracle_twice(
    runtime: dict[str, Any], task: Any, workspace: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    first = runtime["run_oracle"](task, workspace)
    second = runtime["run_oracle"](task, workspace)
    left = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    right = json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if left != right:
        raise RuntimeError("official executable oracle was not deterministic on unchanged state")
    score = float(first.get("outcome_score"))
    if not 0.0 <= score <= 1.0:
        raise RuntimeError(f"official outcome is not finite in [0,1]: {score}")
    return first, [first, second]


def real_p0(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    if output.exists() and not args.resume_p0:
        raise RuntimeError(f"real P0 output already exists: {output}")
    output.mkdir(parents=True, exist_ok=args.resume_p0)
    benchmark = args.benchmark.resolve()
    validate_benchmark(benchmark)
    runtime = load_runtime_modules(benchmark)
    tasks = runtime["load_tasks"](benchmark / "tasks")
    task = tasks.get(args.task)
    if task is None:
        raise RuntimeError(f"unknown Harness Bench task: {args.task}")
    if args.task != "058-multiday-project-state":
        raise RuntimeError("this reviewed P0 admits only task 058-multiday-project-state")

    runtime_root = output / "runtime"
    workspace = runtime_root / "workspace"
    sandbox = runtime_root / "sandbox"
    store = output / "store"
    retained_supervisors: tuple[dict[str, Any], str] | None = None
    if args.resume_p0:
        checkpoint = output / "checkpoint"
        required = [
            checkpoint / "checkpoint.json",
            checkpoint / "prompts" / "next.txt",
            store / "store.json",
            output / "isolation-probe" / "report.json",
        ]
        if not all(path.is_file() for path in required):
            raise RuntimeError("--resume-p0 requires a retained frozen prefix, store, and isolation report")
        next_prompt = (checkpoint / "prompts" / "next.txt").read_text(encoding="utf-8")
        prefix_commands_path = checkpoint / "prefix-commands.json"
        try:
            prefix_commands = json.loads(prefix_commands_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            rows = json.loads((checkpoint / "checkpoint.json").read_text(encoding="utf-8"))["rounds"]
            command = expected_adapter_command(
                args.codex_wrapper, workspace, sandbox, args.worker_model
            )
            prefix_commands = [
                {
                    "round": index,
                    "session_id": row["session_id"],
                    "command": command,
                    "reconstructed_from_frozen_adapter_config": True,
                }
                for index, row in enumerate(rows, start=1)
            ]
            write_json(prefix_commands_path, prefix_commands)
        runtime_state = {}
        isolation = json.loads(
            (output / "isolation-probe" / "report.json").read_text(encoding="utf-8")
        )
        if isolation.get("status") != "PASS":
            raise RuntimeError("retained actual worker isolation probe did not pass")
        stale = output / "supervisors"
        retained_supervisors = load_complete_supervisors(stale, store) if stale.exists() else None
        if stale.exists() and retained_supervisors is None:
            attempts = output / "attempts"
            attempts.mkdir(exist_ok=True)
            os.replace(stale, attempts / f"supervisors-{time.time_ns()}")
        stale_forks = output / "forks"
        if stale_forks.exists():
            attempts = output / "attempts"
            attempts.mkdir(exist_ok=True)
            os.replace(stale_forks, attempts / f"forks-{time.time_ns()}")
        for name in ("p0-report.json", "condition-map.json"):
            stale_file = output / name
            if stale_file.exists():
                attempts = output / "attempts"
                attempts.mkdir(exist_ok=True)
                os.replace(stale_file, attempts / f"{name}-{time.time_ns()}")
        print("[p0] resuming from the retained frozen prefix and PASS isolation probe", flush=True)
    else:
        checkpoint, next_prompt, prefix_commands, runtime_state = build_real_prefix(
            args, runtime, task, output, workspace, sandbox
        )
        run([
            str(args.agentvis_bin), "research-store", "--source", str(checkpoint),
            "--output", str(store), "--verify",
        ])
        isolation = run_isolation_probe(args, runtime, task, output, store)
    round_sessions = [checkpoint / row["session_file"] for row in json.loads(
        (checkpoint / "checkpoint.json").read_text(encoding="utf-8")
    )["rounds"]]
    parsed_ids = [native_session_id(path) for path in round_sessions]
    if len(set(parsed_ids)) != len(parsed_ids):
        raise RuntimeError("prefix rounds did not produce distinct native Codex sessions")

    model_sha256 = sha256_file(args.supervisor_model)
    if retained_supervisors is not None:
        interventions, retained_model_sha256 = retained_supervisors
        if retained_model_sha256 != model_sha256:
            raise RuntimeError("retained supervisors used a different pinned model")
        print("[p0] reusing three complete, provenance-valid supervisor outputs", flush=True)
    else:
        interventions = {
            condition: run_supervisor(
                args, store, condition, output / "supervisors" / condition, model_sha256
            )
            for condition in ("generic", "raw", "trajectory")
        }

    conditions = ["no-intervention", "generic", "raw", "trajectory"]
    random.Random(args.randomization_seed).shuffle(conditions)
    opaque_ids = {condition: f"fork-{uuid.uuid4().hex[:12]}" for condition in conditions}
    final_source = checkpoint / "snapshots" / "round-002" / "tree"
    expected_manifest = manifest(final_source)
    results: dict[str, Any] = {}
    parity_rows: list[dict[str, Any]] = []
    hooks = runtime["load_hooks"](task)
    for condition in conditions:
        if runtime_root.exists():
            shutil.rmtree(runtime_root)
        shutil.copytree(final_source, workspace, symlinks=True, copy_function=shutil.copy2)
        if manifest(workspace) != expected_manifest:
            raise RuntimeError("fork restore does not match the frozen checkpoint")
        sandbox.mkdir(parents=True)
        with make_ephemeral_codex_source(
            args.worker_user_config, workspace, sandbox, args.codex_bin
        ) as source_home:
            model_config = worker_model_config(
                args.codex_wrapper, Path(source_home) / "config.toml",
                args.worker_model, args.worker_reasoning_effort,
            )
            intervention = interventions.get(condition, {"decision": "ABSTAIN", "message": "", "source_ids": []})
            prompt = next_prompt
            if intervention["decision"] == "INTERVENE":
                prompt += (
                    "\n\n" + NEUTRAL_ADVICE_OPEN + "\n" + intervention["message"].strip()
                    + "\n" + NEUTRAL_ADVICE_CLOSE + "\n"
                )
            result = run_adapter_round(
                runtime,
                task=task,
                workspace=workspace,
                sandbox=sandbox,
                prompt=prompt,
                prompt_file=sandbox / "prompt-final.txt",
                session_id=f"agent-nebula-{task.task_id}-final",
                model_config=model_config,
                model_id=args.worker_model,
                real_codex=args.codex_bin,
                timeout_sec=task.timeout_sec,
            )
            if hooks and callable(getattr(hooks, "after_round", None)):
                hooks.after_round(
                    {
                        "task": task,
                        "sandbox": sandbox,
                        "workspace": workspace,
                        "session_id": f"agent-nebula-{task.task_id}-final",
                        "round_index": 2,
                        "prompt_file": sandbox / "prompt-final.txt",
                        "prompt_name": "prompt_day3.txt",
                    },
                    dict(runtime_state),
                    result,
                )
            oracle, oracle_runs = oracle_twice(runtime, task, workspace)
            archive = output / "forks" / opaque_ids[condition]
            archive.mkdir(parents=True)
            capture_snapshot(workspace, archive / "final-workspace")
            shutil.copy2(Path(result.metadata["codex_session_file"]), archive / "worker-session.jsonl")
            (archive / "worker.stdout.jsonl").write_text(result.stdout, encoding="utf-8")
            (archive / "worker.stderr.log").write_text(result.stderr, encoding="utf-8")
            write_json(archive / "oracle.json", oracle)
            write_json(archive / "oracle-runs.json", oracle_runs)
            write_json(archive / "intervention.json", intervention)
            command_hash = sha256_bytes(json.dumps(result.command, separators=(",", ":")).encode())
            env_allowlist = {
                "HOME": str(sandbox),
                "CODEX_HOME": str(sandbox / ".codex"),
                "WORKSPACE": str(workspace),
                "HARNESSBENCH_WORKSPACE": str(workspace),
                "HARNESSBENCH_SANDBOX": str(sandbox),
                "HARNESSBENCH_SESSION_ID": f"agent-nebula-{task.task_id}-final",
                "HARNESSBENCH_PROMPT_FILE": str(sandbox / "prompt-final.txt"),
                "HARNESSBENCH_MODEL_ID": args.worker_model,
            }
            parity_rows.append(
                {
                    "condition": condition,
                    "pre_advice_workspace_manifest_sha256": sha256_bytes(
                        json.dumps(expected_manifest, sort_keys=True).encode()
                    ),
                    "base_prompt_sha256": sha256_bytes(next_prompt.encode()),
                    "command_sha256": command_hash,
                    "environment_sha256": sha256_bytes(
                        json.dumps(env_allowlist, sort_keys=True).encode()
                    ),
                }
            )
            results[condition] = {
                "opaque_id": opaque_ids[condition],
                "decision": intervention["decision"],
                "outcome_score": float(oracle["outcome_score"]),
                "worker_session_sha256": sha256_file(archive / "worker-session.jsonl"),
                "worker_command": result.command,
                "oracle": oracle,
                "oracle_runs_sha256": sha256_bytes(
                    json.dumps(oracle_runs, sort_keys=True, separators=(",", ":")).encode()
                ),
            }
            print(
                f"[p0] {condition} -> outcome={oracle['outcome_score']} "
                f"decision={intervention['decision']}",
                flush=True,
            )

    if len({row["command_sha256"] for row in parity_rows}) != 1:
        raise RuntimeError("final worker argv differs across conditions")
    if len({row["environment_sha256"] for row in parity_rows}) != 1:
        raise RuntimeError("final worker environment allowlist differs across conditions")
    if len({row["pre_advice_workspace_manifest_sha256"] for row in parity_rows}) != 1:
        raise RuntimeError("final worker checkpoints differ across conditions")
    write_json(output / "condition-map.json", opaque_ids)
    report = {
        "schema": "agent-nebula-harness-p0-v1",
        "status": "PASS",
        "benchmark_revision": BENCHMARK_REVISION,
        "task": args.task,
        "randomization_seed": args.randomization_seed,
        "execution_order": conditions,
        "prefix_session_ids": parsed_ids,
        "prefix_commands": prefix_commands,
        "isolation": isolation,
        "supervisor_model_sha256": model_sha256,
        "interventions": interventions,
        "fork_parity": parity_rows,
        "results": results,
        "rubric_provider_requests": 0,
        "official_oracle_runs_per_fork": 2,
    }
    write_json(output / "p0-report.json", report)
    shutil.rmtree(runtime_root, ignore_errors=True)
    print(f"[p0] PASS -> {output / 'p0-report.json'}", flush=True)


def run_headroom_task(
    args: argparse.Namespace,
    runtime: dict[str, Any],
    task: Any,
    task_root: Path,
) -> dict[str, Any]:
    runtime_root = task_root / "runtime"
    workspace = runtime_root / "workspace"
    sandbox = runtime_root / "sandbox"
    checkpoint, next_prompt, prefix_commands, runtime_state = build_real_prefix(
        args, runtime, task, task_root, workspace, sandbox
    )
    checkpoint_data = json.loads(
        (checkpoint / "checkpoint.json").read_text(encoding="utf-8")
    )
    final_round = checkpoint_data["rounds"][-1]
    final_source = checkpoint / final_round["snapshot_tree"]
    expected_manifest = manifest(final_source)
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    shutil.copytree(final_source, workspace, symlinks=True, copy_function=shutil.copy2)
    if manifest(workspace) != expected_manifest:
        raise RuntimeError(f"headroom restore mismatch for {task.task_id}")
    sandbox.mkdir(parents=True)
    prompt_names = list(task.prompt_files or []) or [task.prompt_file]
    hooks = runtime["load_hooks"](task)
    with make_ephemeral_codex_source(
        args.worker_user_config, workspace, sandbox, args.codex_bin
    ) as source_home:
        model_config = worker_model_config(
            args.codex_wrapper, Path(source_home) / "config.toml",
            args.worker_model, args.worker_reasoning_effort,
        )
        result = run_adapter_round(
            runtime,
            task=task,
            workspace=workspace,
            sandbox=sandbox,
            prompt=next_prompt,
            prompt_file=sandbox / "prompt-final.txt",
            session_id=f"agent-nebula-{task.task_id}-headroom",
            model_config=model_config,
            model_id=args.worker_model,
            real_codex=args.codex_bin,
            timeout_sec=task.timeout_sec,
        )
        if hooks and callable(getattr(hooks, "after_round", None)):
            state = hooks.after_round(
                {
                    "task": task,
                    "sandbox": sandbox,
                    "workspace": workspace,
                    "session_id": f"agent-nebula-{task.task_id}-headroom",
                    "round_index": len(prompt_names) - 1,
                    "prompt_file": sandbox / "prompt-final.txt",
                    "prompt_name": prompt_names[-1],
                },
                runtime_state,
                result,
            )
            if isinstance(state, dict):
                runtime_state.update(state)
        oracle, oracle_runs = oracle_twice(runtime, task, workspace)
        final = task_root / "final"
        final.mkdir()
        capture_snapshot(workspace, final / "workspace")
        shutil.copy2(Path(result.metadata["codex_session_file"]), final / "worker-session.jsonl")
        (final / "worker.stdout.jsonl").write_text(result.stdout, encoding="utf-8")
        (final / "worker.stderr.log").write_text(result.stderr, encoding="utf-8")
        write_json(final / "oracle.json", oracle)
        write_json(final / "oracle-runs.json", oracle_runs)
        if hooks and callable(getattr(hooks, "cleanup_runtime", None)):
            hooks.cleanup_runtime(
                {"task": task, "sandbox": sandbox, "workspace": workspace}, runtime_state
            )
    report = {
        "schema": "agent-nebula-headroom-task-v1",
        "status": "PASS",
        "task": task.task_id,
        "benchmark_revision": BENCHMARK_REVISION,
        "worker_model": args.worker_model,
        "worker_reasoning_effort": args.worker_reasoning_effort,
        "prefix_session_ids": [row["session_id"] for row in checkpoint_data["rounds"]],
        "prefix_commands": prefix_commands,
        "checkpoint_manifest_sha256": sha256_bytes(
            json.dumps(expected_manifest, sort_keys=True).encode()
        ),
        "base_prompt_sha256": sha256_bytes(next_prompt.encode()),
        "outcome_score": float(oracle["outcome_score"]),
        "below_0_95": float(oracle["outcome_score"]) < 0.95,
        "official_oracle_runs": 2,
        "oracle_runs_sha256": sha256_bytes(
            json.dumps(oracle_runs, sort_keys=True, separators=(",", ":")).encode()
        ),
        "rubric_provider_requests": 0,
        "worker_session_sha256": sha256_file(final / "worker-session.jsonl"),
    }
    write_json(task_root / "report.json", report)
    shutil.rmtree(runtime_root, ignore_errors=True)
    print(
        f"[headroom] {task.task_id} -> outcome={report['outcome_score']} "
        f"below_0.95={report['below_0_95']}",
        flush=True,
    )
    return report


def headroom_only(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    benchmark = args.benchmark.resolve()
    validate_benchmark(benchmark)
    runtime = load_runtime_modules(benchmark)
    tasks = runtime["load_tasks"](benchmark / "tasks")
    reports: list[dict[str, Any]] = []
    for task_id in SELECTED_TASKS:
        task_root = output / task_id
        report_path = task_root / "report.json"
        try:
            retained = json.loads(report_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            retained = None
        if isinstance(retained, dict) and retained.get("status") == "PASS":
            reports.append(retained)
            print(f"[headroom] reusing complete task {task_id}", flush=True)
            continue
        if task_root.exists():
            attempts = output / "attempts"
            attempts.mkdir(exist_ok=True)
            os.replace(task_root, attempts / f"{task_id}-{time.time_ns()}")
        task = tasks.get(task_id)
        if task is None:
            raise RuntimeError(f"missing fixed headroom task {task_id}")
        task_root.mkdir()
        reports.append(run_headroom_task(args, runtime, task, task_root))
    below = sum(bool(report["below_0_95"]) for report in reports)
    aggregate = {
        "schema": "agent-nebula-headroom-v1",
        "status": "PASS",
        "benchmark_revision": BENCHMARK_REVISION,
        "fixed_tasks": list(SELECTED_TASKS),
        "threshold": 0.95,
        "required_below_threshold": 4,
        "observed_below_threshold": below,
        "full_matrix_admitted": below >= 4,
        "results": {report["task"]: report["outcome_score"] for report in reports},
        "rubric_provider_requests": 0,
    }
    write_json(output / "headroom-report.json", aggregate)
    print(
        f"[headroom] PASS: {below}/6 below 0.95; "
        f"full_matrix_admitted={aggregate['full_matrix_admitted']}",
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--agentvis-bin", type=Path, default=Path("agentvis/target/debug/agentvis"))
    parser.add_argument("--supervisor-model", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--resume-p0", action="store_true")
    parser.add_argument("--headroom-only", action="store_true")
    parser.add_argument("--task", default="058-multiday-project-state")
    parser.add_argument("--checkpoint-before-final-round", action="store_true")
    parser.add_argument("--conditions", default="no-intervention,generic,raw,trajectory")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--worker-model", default="gpt-5.6-sol")
    parser.add_argument("--worker-reasoning-effort", default="medium")
    parser.add_argument("--worker-user-config", type=Path, default=Path("~/.codex/config.toml"))
    parser.add_argument(
        "--codex-bin", type=Path,
        default=Path("/home/yunwei37/.codex/packages/standalone/releases/0.144.6-x86_64-unknown-linux-musl/bin/codex"),
    )
    parser.add_argument(
        "--codex-wrapper", type=Path,
        default=Path("agentvis/research/codex_profile_wrapper.py"),
    )
    parser.add_argument("--supervisor-url", default="http://127.0.0.1:8013/v1")
    parser.add_argument("--supervisor-seed", type=int, default=20260721)
    parser.add_argument("--supervisor-evidence-tokens", type=int, default=16384)
    parser.add_argument("--supervisor-evidence-bytes", type=int, default=65536)
    parser.add_argument("--supervisor-max-tool-calls", type=int, default=24)
    parser.add_argument("--randomization-seed", type=int, default=20260721)
    args = parser.parse_args()
    args.worker_user_config = args.worker_user_config.expanduser()
    args.agentvis_bin = args.agentvis_bin.resolve()
    args.supervisor_model = args.supervisor_model.resolve()
    args.codex_bin = args.codex_bin.resolve()
    args.codex_wrapper = args.codex_wrapper.resolve()
    args.benchmark = args.benchmark.resolve()
    for path, label in (
        (args.agentvis_bin, "agentvis binary"),
        (args.supervisor_model, "supervisor model"),
        (args.benchmark, "benchmark checkout"),
    ):
        if not path.exists():
            parser.error(f"{label} does not exist: {path}")
    if not args.prepare_only:
        if not args.checkpoint_before_final_round:
            parser.error("real benchmark execution requires --checkpoint-before-final-round")
        if not args.headroom_only and (
            args.conditions != "no-intervention,generic,raw,trajectory" or args.repetitions != 1
        ):
            parser.error("real P0 requires the reviewed four conditions and one repetition")
        if (
            args.worker_model != "gpt-5.6-sol"
            or args.worker_reasoning_effort != "medium"
            or args.supervisor_seed != 20260721
            or args.supervisor_evidence_tokens != 16384
            or args.supervisor_evidence_bytes != 65536
            or args.supervisor_max_tool_calls != 24
        ):
            parser.error("real P0 model and supervisor arguments must equal the reviewed frozen plan")
        for path, label in (
            (args.worker_user_config, "worker user config"),
            (args.codex_bin, "Codex binary"),
            (args.codex_wrapper, "Codex wrapper"),
        ):
            if not path.exists():
                parser.error(f"{label} does not exist: {path}")
    return args


if __name__ == "__main__":
    parsed = parse_args()
    if parsed.prepare_only:
        prepare_only(parsed)
    elif parsed.headroom_only:
        headroom_only(parsed)
    else:
        real_p0(parsed)
