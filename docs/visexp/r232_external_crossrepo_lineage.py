#!/usr/bin/env python3
"""Run R232 external cross-repo exact-lineage replication.

R232 reuses the R114/R229 scoped lineage oracle, but moves the target workloads
out of the AgentSight repository. Each non-network task runs in a fresh external
git repository under the work directory. The network task reuses the R191 fixed
target HTTP probe shape, also outside the AgentSight repo.

The committed artifact is a scrubbed summary. Raw SQLite DBs, snapshots, and
per-event lineage CSVs remain in the local work directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import r114_live_record_suite as r114
import r191_target_network_lineage as r191


DEFAULT_WORK = Path("/tmp/agentsight-r232-external-crossrepo")
WORK_MARKER = ".agentsight-r232-external-crossrepo"
DEFAULT_OUT = r114.DEFAULT_OUT / "external-crossrepo-lineage-r232"


R232_TASKS = [
    r114.Task(
        "r232-ext-read",
        "repo-read",
        (
            "Read README.md and answer exactly one line: project=<project name>. "
            "Do not modify files."
        ),
        sandbox="read-only",
        workspace="external_read",
    ),
    r114.Task(
        "r232-ext-python-fix",
        "edit-test",
        (
            "Fix calc.py so `python3 -m unittest` passes. You may edit files in "
            "the current directory only. After running the test, answer exactly "
            "one line: tests=<passed|failed>."
        ),
        sandbox="workspace-write",
        workspace="external_python_bug",
    ),
    r114.Task(
        "r232-ext-json-write",
        "write",
        (
            "Create result.json with exactly {\"status\":\"ok\",\"run\":\"r232\"}. "
            "You may edit files in the current directory only. Answer exactly "
            "one line: result_json=<created|missing>."
        ),
        sandbox="workspace-write",
        workspace="external_json_write",
    ),
    r114.Task(
        "r232-ext-shell-fix",
        "edit-test",
        (
            "Run `bash check.sh`, fix the script so it exits 0, then answer "
            "exactly one line: check=<passed|failed>."
        ),
        sandbox="workspace-write",
        workspace="external_shell_fix",
    ),
]


R232_HTTP_PROBE = r"""from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, threading, time, urllib.request

os.chdir(Path(__file__).resolve().parent)
nonce = "r232-http-probe"
Path("payload.txt").write_text(nonce, encoding="utf-8")
server = ThreadingHTTPServer(("127.0.0.1", 0), SimpleHTTPRequestHandler)
port = int(server.server_address[1])
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
started = time.time()
body = urllib.request.urlopen(f"http://127.0.0.1:{port}/payload.txt", timeout=5).read().decode("utf-8")
server.shutdown()
server.server_close()
thread.join(timeout=5)
result = {
    "status": "ok",
    "probe": "http",
    "port": port,
    "bytes": len(body),
    "body": body,
    "elapsed_ms": int((time.time() - started) * 1000),
}
Path("r191_result.json").write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
"""


R232_NETWORK_TASKS = [
    r191.NetworkTask(
        task_id="r232-ext-http-probe",
        script_name="r232_http_probe.py",
        script_body=R232_HTTP_PROBE,
        expected_probe="http",
        expected_body="r232-http-probe",
    )
]


def prepare_work_dir(work_dir: Path) -> None:
    resolved = work_dir.resolve()
    default_resolved = DEFAULT_WORK.resolve()
    if work_dir.exists():
        marker = work_dir / WORK_MARKER
        if resolved != default_resolved and not marker.exists() and any(work_dir.iterdir()):
            raise SystemExit(
                f"refusing to remove non-empty unmarked work dir: {work_dir}. "
                f"Use an empty directory or one containing {WORK_MARKER}."
            )
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / WORK_MARKER).write_text(
        "owned by docs/visexp/r232_external_crossrepo_lineage.py\n",
        encoding="utf-8",
    )


def init_external_repo(path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / ".r232-external-repo").write_text(name + "\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=False)
    subprocess.run(["git", "config", "user.email", "r232@example.invalid"], cwd=path, check=False)
    subprocess.run(["git", "config", "user.name", "R232"], cwd=path, check=False)


def r232_workspace_for_task(task: r114.Task, work_dir: Path) -> Path:
    path = work_dir / "external-repos" / task.task_id
    init_external_repo(path, task.workspace)
    if task.workspace == "external_read":
        (path / "README.md").write_text(
            "# external-r232-read\n\nThis repository is outside the AgentSight checkout.\n",
            encoding="utf-8",
        )
    elif task.workspace == "external_python_bug":
        (path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        (path / "test_calc.py").write_text(
            "import unittest\nfrom calc import add\n\n"
            "class CalcTest(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(2, 3), 5)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )
    elif task.workspace == "external_json_write":
        (path / "README.md").write_text("Create result.json for R232 here.\n", encoding="utf-8")
    elif task.workspace == "external_shell_fix":
        (path / "check.sh").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (path / "check.sh").chmod(0o755)
    else:
        raise SystemExit(f"unknown R232 external workspace: {task.workspace}")
    subprocess.run(["git", "add", "."], cwd=path, check=False)
    subprocess.run(["git", "commit", "-q", "-m", "seed r232 fixture"], cwd=path, check=False)
    return path


def replication_gate(aggregate: dict[str, Any], task_count: int) -> bool:
    target_statuses = aggregate.get("target_statuses") or {}
    return (
        aggregate.get("tasks") == task_count
        and target_statuses.get("completed", 0) == task_count
        and aggregate.get("negative_control_tasks_observed", 0) == task_count
        and aggregate.get("negative_effect_events_observed", 0) > 0
        and aggregate.get("negative_joined_effect_events", 0) == 0
        and aggregate.get("precision_pct", 0.0) >= 98.0
        and aggregate.get("recall_pct", 0.0) >= 95.0
        and aggregate.get("in_scope_effect_events", 0) > 0
    )


def network_gate(aggregate: dict[str, Any], task_count: int) -> bool:
    expected = sum(r191.EXPECTED_TARGET_ACTIONS.values()) * task_count
    return (
        task_count == 0
        or (
            aggregate.get("tasks") == task_count
            and (aggregate.get("task_statuses") or {}).get("ok", 0) == task_count
            and aggregate.get("target_network_effect_events") == expected
            and aggregate.get("joined_target_network_effect_events") == expected
            and aggregate.get("orphan_target_network_effect_events") == 0
            and aggregate.get("target_network_actions")
            == {key: value * task_count for key, value in r191.EXPECTED_TARGET_ACTIONS.items()}
            and aggregate.get("target_network_process_comms") == {"python3": expected}
            and aggregate.get("negative_effect_events_observed", 0) > 0
            and aggregate.get("negative_joined_effect_events", 0) == 0
            and aggregate.get("precision_pct", 0.0) >= 98.0
            and aggregate.get("recall_pct", 0.0) >= 95.0
        )
    )


def category_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("category") or "network") for row in rows))


def workspace_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    out: Counter[str] = Counter()
    for row in rows:
        workspace = str(row.get("workspace") or "network_probe")
        if workspace.startswith("/"):
            workspace = Path(workspace).name or "external_path"
        out[workspace] += 1
    return dict(out)


def combined_aggregate(normal: dict[str, Any], network: dict[str, Any]) -> dict[str, Any]:
    tp = int(normal.get("true_positives") or 0) + int(network.get("true_positives") or 0)
    fp = int(normal.get("false_positives") or 0) + int(network.get("false_positives") or 0)
    fn = int(normal.get("false_negatives") or 0) + int(network.get("false_negatives") or 0)
    return {
        "normal_tasks": int(normal.get("tasks") or 0),
        "network_tasks": int(network.get("tasks") or 0),
        "tasks": int(normal.get("tasks") or 0) + int(network.get("tasks") or 0),
        "in_scope_effect_events": int(normal.get("in_scope_effect_events") or 0),
        "out_of_scope_effect_events": int(normal.get("out_of_scope_effect_events") or 0),
        "effect_events": int(normal.get("effect_events") or 0),
        "joined_effect_events": int(normal.get("joined_effect_events") or 0),
        "target_network_effect_events": int(network.get("target_network_effect_events") or 0),
        "joined_target_network_effect_events": int(network.get("joined_target_network_effect_events") or 0),
        "orphan_target_network_effect_events": int(network.get("orphan_target_network_effect_events") or 0),
        "negative_effect_events_observed": int(normal.get("negative_effect_events_observed") or 0)
        + int(network.get("negative_effect_events_observed") or 0),
        "negative_joined_effect_events": int(normal.get("negative_joined_effect_events") or 0)
        + int(network.get("negative_joined_effect_events") or 0),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision_pct": round(100.0 * tp / (tp + fp), 3) if (tp + fp) else 0.0,
        "recall_pct": round(100.0 * tp / (tp + fn), 3) if (tp + fn) else 0.0,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    normal = result["normal_aggregate"]
    network = result["network_aggregate"]
    combined = result["aggregate"]
    lines = [
        "# R232 External Cross-Repo Lineage",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r232_external_crossrepo_lineage.py`",
        f"Completeness: {result['status']}",
        "",
        "R232 reruns controlled Codex command-mode lineage tasks outside the",
        "AgentSight repository. Non-network workloads use fresh external git",
        "repositories; the network workload uses a local Python HTTP probe.",
        "",
        "Raw DBs, snapshots, external workspaces, and per-event lineage CSVs stay",
        "in the local work directory and are not committed.",
        "",
        "## Aggregate",
        "",
        f"- Normal tasks: {normal.get('tasks', 0)}; network tasks: {network.get('tasks', 0)}.",
        f"- Combined scoped precision/recall: {combined['precision_pct']}%/{combined['recall_pct']}%.",
        f"- Normal in-scope effects: {normal.get('in_scope_effect_events', 0)}; negative joins: {normal.get('negative_joined_effect_events', 0)}/{normal.get('negative_effect_events_observed', 0)}.",
        f"- Target network effects: {network.get('joined_target_network_effect_events', 0)}/{network.get('target_network_effect_events', 0)} joined; negative joins: {network.get('negative_joined_effect_events', 0)}/{network.get('negative_effect_events_observed', 0)}.",
        f"- External workload categories: {result['category_distribution']}.",
        f"- External workspace kinds: {result['workspace_distribution']}.",
        f"- Gates: normal={result['normal_gate']}, network={result['network_gate']}, external_crossrepo={result['external_crossrepo_lineage_supported']}.",
        "",
        "## Normal Tasks",
        "",
        "| Task | Cat | Workspace | Target | Lineage | In scope | Neg observed | Neg joined | Answer |",
        "|------|-----|-----------|--------|---------|---------:|-------------:|-----------:|--------|",
    ]
    for row in result["normal_tasks"]:
        pr = row.get("precision_recall") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:100]
        lines.append(
            f"| `{row['task_id']}` | {row.get('category')} | {row.get('workspace')} | "
            f"{row.get('target_status')} | {row.get('lineage_status')} | "
            f"{pr.get('in_scope_effect_events', 0)} | {pr.get('negative_effect_events_observed', 0)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | {answer} |"
        )
    lines.extend(
        [
            "",
            "## Network Tasks",
            "",
            "| Task | Status | Probe | Target network | Neg joined | Precision/Recall | Answer |",
            "|------|--------|-------|---------------:|-----------:|------------------:|--------|",
        ]
    )
    for row in result["network_tasks"]:
        net = row.get("network_lineage") or {}
        pr = row.get("precision_recall") or {}
        probe = row.get("probe_result") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| `{row['task_id']}` | {row.get('status')} | {probe.get('probe')}:{probe.get('status')} | "
            f"{net.get('joined_target_network_effect_events', 0)}/{net.get('target_network_effect_events', 0)} | "
            f"{pr.get('negative_joined_effect_events', 0)} | "
            f"{pr.get('precision_pct', 0.0)}%/{pr.get('recall_pct', 0.0)}% | {answer} |"
        )
    lines.extend(["", "## Claim Boundary", "", result["boundary"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)
    agentsight_bin = Path(r114.resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = r114.resolve_executable(args.codex_bin, "codex")

    selected = R232_TASKS[: args.task_limit]
    selected_network = R232_NETWORK_TASKS[: args.network_task_limit]
    if args.print_manifest:
        payload = {
            "schema_version": 1,
            "run_id": "R232",
            "tasks": r114.manifest_rows(selected),
            "network_tasks": [
                {"task_id": task.task_id, "script": task.script_name, "probe": task.expected_probe}
                for task in selected_network
            ],
        }
        print(json.dumps(payload, indent=2))
        return payload

    network_rows = [
        r191.run_task(task, agentsight_bin, codex_bin, work_dir, args.timeout, args.network_negative_mode)
        for task in selected_network
    ]

    original_workspace_for_task = r114.workspace_for_task
    r114.workspace_for_task = r232_workspace_for_task
    try:
        normal_rows = [
            r114.record_task(task, agentsight_bin, codex_bin, work_dir, args.timeout, args.negative_mode)
            for task in selected
        ]
    finally:
        r114.workspace_for_task = original_workspace_for_task
    normal_aggregate = r114.aggregate(normal_rows)
    network_aggregate = r191.aggregate(network_rows)
    normal_ok = replication_gate(normal_aggregate, len(normal_rows))
    network_ok = network_gate(network_aggregate, len(network_rows))
    combined = combined_aggregate(normal_aggregate, network_aggregate)
    passed = normal_ok and network_ok
    status = "ok" if passed else "partial"
    boundary = (
        "R232 supports C4/RQ3 beyond the AgentSight repository for this controlled "
        "external-repo workload: scoped effects and target network rows join to "
        "the target Codex task, while negative controls remain unattributed. It "
        "does not prove arbitrary repositories, arbitrary network workloads, "
        "strict full-history prompt-row lineage, C5 developer utility, or C6 tag adequacy."
        if passed
        else "R232 is partial: external cross-repo lineage, target network, or negative-control gates did not all pass."
    )
    result = {
        "schema_version": 1,
        "run_id": "R232",
        "status": status,
        "scope": "external_crossrepo_codex_record_lineage_with_target_network_probe",
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": r114.rel(agentsight_bin),
        "codex_bin": r114.scrub(codex_bin, limit=400),
        "task_limit": len(normal_rows),
        "network_task_limit": len(network_rows),
        "negative_mode": args.negative_mode,
        "network_negative_mode": args.network_negative_mode,
        "normal_gate": normal_ok,
        "network_gate": network_ok,
        "external_crossrepo_lineage_supported": passed,
        "manifest": r114.manifest_rows(selected),
        "network_manifest": [
            {"task_id": task.task_id, "script": task.script_name, "probe": task.expected_probe}
            for task in selected_network
        ],
        "category_distribution": category_distribution(normal_rows + network_rows),
        "workspace_distribution": workspace_distribution(normal_rows + network_rows),
        "aggregate": combined,
        "normal_aggregate": normal_aggregate,
        "network_aggregate": network_aggregate,
        "normal_tasks": normal_rows,
        "network_tasks": network_rows,
        "boundary": boundary,
        "artifact_boundary": (
            "Raw SQLite DBs, exported snapshots, external workspaces, and per-event lineage CSVs stay "
            "in the local work dir; committed artifacts contain scrubbed task-level summaries only."
        ),
    }
    result = r114.scrub_artifact_value(result)
    json_path = out_dir / "external-crossrepo-lineage-r232.json"
    md_path = out_dir / "external-crossrepo-lineage-r232.md"
    result["outputs"] = {
        "json": r114.rel(json_path),
        "markdown": r114.rel(md_path),
    }
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(md_path, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "normal_gate": result["normal_gate"],
                "network_gate": result["network_gate"],
                "aggregate": result["aggregate"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--agentsight-bin", default=str(r114.REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--task-limit", type=int, default=len(R232_TASKS))
    parser.add_argument("--network-task-limit", type=int, default=len(R232_NETWORK_TASKS))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--negative-mode", choices=("wrapper", "external"), default="wrapper")
    parser.add_argument("--network-negative-mode", choices=("wrapper", "none"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
