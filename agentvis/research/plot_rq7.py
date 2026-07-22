#!/usr/bin/env python3
"""Render the RQ7 matched-benchmark readiness audit (no baseline execution)."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


CUTOFF_MS = 1784708569241
PROC_GREP_REVISION = "2e8277003dacaa774b5ef61ba150ae03a4f06693"
EXPECTED_HASHES = {
    "projects.json": "2491c33ac5c5e64c877ea8c998731df2dad2999e37af715e528f997f909dc58b",
    "rq1-artifacts.csv": "8e72aa19b5305b9c455c64cd009b535f45145d67729d9c8b58318e89ef767cc1",
    "rq1-mutations.csv": "3d911332f7827afdee74a1f6a0f85aa002be297379e14909dbba1fee36d88964",
    "rq1-summary.csv": "d04cee570c409ab1a8b1518657683e6ccb417663acb9933690c063adcf61406b",
    "events/academic-writing-skills.json.gz": "f8536f1ab6d73393d993c2cde66e6fc9deff759329f17a12eaa1888a49986db4",
    "events/ActPlane.json.gz": "4ee9fc1aebeee30bc3c2b45117e38a0d63053bda1d167a839466eed630034026",
    "events/agentsight.json.gz": "ebbf3dd94459a6d43db945a41f8b112f3289b5833d09b864a070fbc66a8bbf46",
    "events/agentskill-observability-paper.json.gz": "33b6b1b172027b77ae66695a37025ec41c818df5d0f81c05390568f8fc5c6880",
    "events/bpf-developer-tutorial.json.gz": "88dec6db8a1320c6991fefa236eb6afbfc65e175d62eddbadb80c68ed6a46098",
    "events/eunomia-dev.json.gz": "cf7dfea58a4453b221abe8eaf32ed83fe24842d3cac67010fd23a46f974b4fe9",
}
EVENT_FILES = {
    "agentsight": "events/agentsight.json.gz",
    "ActPlane": "events/ActPlane.json.gz",
    "bpf-developer-tutorial": "events/bpf-developer-tutorial.json.gz",
    "eunomia.dev": "events/eunomia-dev.json.gz",
    "agentskill-observability-paper": "events/agentskill-observability-paper.json.gz",
    "academic-writing-skills": "events/academic-writing-skills.json.gz",
}
SHORT = {
    "agentsight": "AgentSight",
    "ActPlane": "ActPlane",
    "bpf-developer-tutorial": "BPF tutorial",
    "eunomia.dev": "eunomia.dev",
    "agentskill-observability-paper": "AgentSkill paper",
    "academic-writing-skills": "Writing skills",
}
SOURCE_REQUIREMENTS = [
    "normalized_action_spine",
    "normalized_source_linkage",
    "native_prefix_manifest",
    "native_prefix_archive",
    "worktree_revision_manifest",
    "cutoff_untracked_disposition",
]
SOURCE_LABELS = [
    "normalized\naction spine",
    "normalized\nsource linkage",
    "native-prefix\nmanifest",
    "native-prefix\narchive",
    "worktree cutoff\nrevisions",
    "untracked-state\ndisposition",
]
STATUS_CODE = {"N/A": 0, "partial": 1, "present": 2}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_status(root: Path, relative: str) -> tuple[str, str]:
    path = root / relative
    if not path.is_file():
        return "N/A", "frozen file missing"
    actual = sha256(path)
    if actual != EXPECTED_HASHES[relative]:
        return "partial", f"SHA-256 mismatch: {actual[:12]}"
    return "present", f"preregistered SHA-256 {actual[:12]}"


def load_json(path: Path) -> object | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError):
        return None


def rows_for_project(value: object | None, project: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict) and row.get("project") == project]


def contract_status(
    path: Path,
    project: str,
    expected_count: int,
    required: set[str],
) -> tuple[str, str]:
    if not path.is_file():
        return "N/A", f"missing exact contract {path.name}"
    value = load_json(path)
    rows = rows_for_project(value, project)
    valid = [
        row for row in rows
        if required.issubset(row) and int(row.get("cutoff_ms", -1)) == CUTOFF_MS
    ]
    if len(valid) != expected_count:
        return "partial", f"schema/count {len(valid)}/{expected_count}"
    return "present", f"schema/count {len(valid)}/{expected_count}"


def source_contract(root: Path) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    project_status, _ = hash_status(root, "projects.json")
    if project_status != "present":
        raise ValueError("projects.json does not match the authoritative RQ1 hash")
    projects = load_json(root / "projects.json")
    if not isinstance(projects, list):
        raise ValueError("projects.json must contain a list")
    by_project = {str(row["project"]): row for row in projects if isinstance(row, dict)}
    contracts = root / "contracts"
    native_manifest = contracts / "native-prefix-manifest.json"
    worktree_manifest = contracts / "worktree-revisions.json"
    untracked_manifest = contracts / "cutoff-untracked-state.json"
    native_rows = load_json(native_manifest)
    rows: list[dict[str, object]] = []

    for project in EVENT_FILES:
        metadata = by_project[project]
        event_relative = EVENT_FILES[project]
        spine_status, spine_detail = hash_status(root, event_relative)
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[0], "status": spine_status, "detail": spine_detail})

        missing_linkage = 0
        event_count = 0
        if spine_status == "present":
            with gzip.open(root / event_relative, "rt", encoding="utf-8") as stream:
                payload = json.load(stream)
            events = payload.get("events", []) if isinstance(payload, dict) else []
            event_count = len(events)
            required = ("id", "source_call_id", "session_id", "vendor", "ts_ms")
            missing_linkage = sum(any(event.get(field) in (None, "") for field in required) for event in events)
            linkage_status = "present" if missing_linkage == 0 else "partial"
            linkage_detail = f"{event_count - missing_linkage}/{event_count} events carry all linkage fields"
        else:
            linkage_status = "N/A"
            linkage_detail = "normalized spine unavailable"
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[1], "status": linkage_status, "detail": linkage_detail})

        admitted = int(metadata["included_sessions"])
        manifest_status, manifest_detail = contract_status(
            native_manifest,
            project,
            admitted,
            {"project", "vendor", "session_id", "native_path", "admitted_end", "sha256", "archive_member", "cutoff_ms"},
        )
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[2], "status": manifest_status, "detail": manifest_detail})

        archive_path = contracts / "native-prefixes.tar.zst"
        project_native_rows = rows_for_project(native_rows, project)
        if manifest_status == "present" and archive_path.is_file() and all(row.get("archive_member") for row in project_native_rows):
            archive_status, archive_detail = "present", f"archive plus {len(project_native_rows)} declared members"
        elif archive_path.is_file():
            archive_status, archive_detail = "partial", "archive exists without a complete admitted-prefix manifest"
        else:
            archive_status, archive_detail = "N/A", "missing exact contract native-prefixes.tar.zst"
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[3], "status": archive_status, "detail": archive_detail})

        worktree_status, worktree_detail = contract_status(
            worktree_manifest,
            project,
            int(metadata["worktrees"]),
            {"project", "worktree_id", "root", "revision", "cutoff_ms"},
        )
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[4], "status": worktree_status, "detail": worktree_detail})

        untracked_status, untracked_detail = contract_status(
            untracked_manifest,
            project,
            int(metadata["worktrees"]),
            {"project", "worktree_id", "disposition", "cutoff_ms"},
        )
        rows.append({"project": project, "requirement": SOURCE_REQUIREMENTS[5], "status": untracked_status, "detail": untracked_detail})
    return rows, by_project


def exact_contract(path: Path, required: set[str]) -> tuple[bool, str]:
    value = load_json(path)
    if not isinstance(value, dict):
        return False, f"missing/invalid {path.name}"
    missing = sorted(required - set(value))
    return (not missing), ("schema present" if not missing else f"missing fields: {','.join(missing)}")


def derive_method_rows(root: Path, sources: list[dict[str, object]]) -> list[dict[str, object]]:
    all_spines = all(row["status"] == "present" for row in sources if row["requirement"] == "normalized_action_spine")
    identity_ready = all(hash_status(root, name)[0] == "present" for name in ["rq1-artifacts.csv", "rq1-mutations.csv"])
    all_native = all(row["status"] == "present" for row in sources if row["requirement"] in {"native_prefix_manifest", "native_prefix_archive"})
    all_final = all(row["status"] == "present" for row in sources if row["requirement"] in {"worktree_revision_manifest", "cutoff_untracked_disposition"})

    preflight_ok, _ = exact_contract(root / "contracts" / "procgrep-preflight.json", {"revision", "claude", "codex", "gemini"})
    if preflight_ok:
        value = load_json(root / "contracts" / "procgrep-preflight.json")
        preflight_ok = isinstance(value, dict) and value.get("revision") == PROC_GREP_REVISION and all(value.get(vendor) == "pass" for vendor in ["claude", "codex", "gemini"])
    llm_ok, _ = exact_contract(
        root / "contracts" / "raw-log-llm.json",
        {"model", "provider", "version", "prompt_sha256", "retriever_sha256", "context_bytes", "output_tokens", "retry_policy", "cache_policy", "max_calls", "token_cap", "dollar_cap"},
    )

    return [
        {"method": "Counts (normalized)", "status": "measured" if all_spines else "N/A", "detail": "descriptive counts only; no accuracy oracle" if all_spines else "normalized spine unavailable"},
        {"method": "Artifact Trajectory", "status": "coverage-only" if all_spines and identity_ready else "N/A", "detail": "normalized projection exists; independent matched oracle absent" if all_spines and identity_ready else "trajectory prerequisites unavailable"},
        {"method": "Final State", "status": "measured" if all_final else "N/A", "detail": "cutoff worktree and untracked-state contracts" if all_final else "cutoff worktree/untracked contracts missing"},
        {"method": "ProcGrep", "status": "measured" if all_native and preflight_ok else "N/A", "detail": "matched native prefixes plus 3-vendor pinned preflight" if all_native and preflight_ok else "native prefixes and/or pinned 3-vendor preflight missing"},
        {"method": "Raw-log LLM", "status": "measured" if all_native and llm_ok else "N/A", "detail": "matched native prefixes plus frozen model/retrieval budget" if all_native and llm_ok else "native prefixes and/or frozen model budget missing"},
    ]


def derive_template_rows(methods: list[dict[str, object]]) -> list[dict[str, object]]:
    method_status = {row["method"]: row["status"] for row in methods}
    procgrep = method_status["ProcGrep"] == "measured"
    raw_llm = method_status["Raw-log LLM"] == "measured"
    final_state = method_status["Final State"] == "measured"
    return [
        {"template": "action-only", "status": "N/A", "gate": "not evaluated", "detail": "matched native oracle/ProcGrep/Raw-log unavailable" if not (procgrep and raw_llm) else "question/oracle plan intentionally not run"},
        {"template": "artifact-linked", "status": "N/A", "gate": "not evaluated", "detail": "no independent source-explicit lineage oracle"},
        {"template": "cross-session", "status": "N/A", "gate": "not evaluated", "detail": "no frozen native-prefix oracle contract"},
        {"template": "final-state", "status": "N/A", "gate": "not evaluated", "detail": "cutoff worktree/untracked state unavailable" if not final_state else "question/oracle plan intentionally not run"},
    ]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_result(path: Path, sources: list[dict[str, object]], methods: list[dict[str, object]], templates: list[dict[str, object]]) -> None:
    source_counts = {status: sum(row["status"] == status for row in sources) for status in STATUS_CODE}
    lines = [
        "# RQ7 Matched-Benchmark Readiness Audit",
        "",
        "**MATCHED COMPARISON STOPPED.** This dependency-only audit runs no baseline, builds no question set, and reports no accuracy, coverage advantage, evidence score, latency, token, or cost result.",
        "",
        f"Source-contract cells: {source_counts['present']} present, {source_counts['partial']} partial, {source_counts['N/A']} N/A.",
        "",
        "| Method condition | Status | Meaning |",
        "|---|---|---|",
    ]
    lines.extend(f"| {row['method']} | {row['status']} | {row['detail']} |" for row in methods)
    lines.extend(["", "| Template family | Status | 30×4 gate | Meaning |", "|---|---|---|---|"])
    lines.extend(f"| {row['template']} | {row['status']} | {row['gate']} | {row['detail']} |" for row in templates)
    lines.extend(["", "This result is not the canonical RQ7 answer and is not evidence that Artifact Trajectory outperforms any baseline."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot(output: Path, sources: list[dict[str, object]], methods: list[dict[str, object]], templates: list[dict[str, object]]) -> None:
    projects = list(EVENT_FILES)
    fig = plt.figure(figsize=(7.05, 7.25))
    grid = fig.add_gridspec(3, 1, height_ratios=[2.4, 2.0, 1.65], hspace=0.56)
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42

    source_axis = fig.add_subplot(grid[0, 0])
    matrix = np.zeros((len(projects), len(SOURCE_REQUIREMENTS)))
    for i, project in enumerate(projects):
        for j, requirement in enumerate(SOURCE_REQUIREMENTS):
            row = next(row for row in sources if row["project"] == project and row["requirement"] == requirement)
            matrix[i, j] = STATUS_CODE[str(row["status"])]
    cmap = ListedColormap(["#d9d9d9", "#e7b75f", "#64a878"])
    source_axis.imshow(matrix, aspect="auto", vmin=-0.5, vmax=2.5, cmap=cmap)
    source_axis.set_yticks(range(len(projects)), [SHORT[project] for project in projects], fontsize=7)
    source_axis.set_xticks(range(len(SOURCE_LABELS)), SOURCE_LABELS, fontsize=7)
    source_axis.set_title("A. Frozen source contract by project", loc="left", fontsize=9, fontweight="bold")
    cell_label = {0: "N/A", 1: "partial", 2: "present"}
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            source_axis.text(j, i, cell_label[int(matrix[i, j])], ha="center", va="center", fontsize=7, color="#202020")

    method_axis = fig.add_subplot(grid[1, 0])
    method_axis.axis("off")
    method_axis.set_title("B. Matched method admission (readiness, not performance)", loc="left", fontsize=9, fontweight="bold")
    method_colors = {"measured": "#64a878", "coverage-only": "#e7b75f", "N/A": "#d9d9d9"}
    for index, row in enumerate(methods):
        y = 0.83 - index * 0.18
        method_axis.add_patch(plt.Rectangle((0.0, y - 0.045), 0.18, 0.105, transform=method_axis.transAxes, facecolor=method_colors[str(row["status"])], edgecolor="#777777", linewidth=0.6))
        method_axis.text(0.09, y + 0.008, str(row["status"]), transform=method_axis.transAxes, ha="center", va="center", fontsize=7, fontweight="bold")
        method_axis.text(0.205, y + 0.008, str(row["method"]), transform=method_axis.transAxes, ha="left", va="center", fontsize=7.5, fontweight="bold")
        method_axis.text(0.43, y + 0.008, str(row["detail"]), transform=method_axis.transAxes, ha="left", va="center", fontsize=7)

    template_axis = fig.add_subplot(grid[2, 0])
    template_axis.axis("off")
    template_axis.set_title("C. Template-family gate", loc="left", fontsize=9, fontweight="bold")
    for index, row in enumerate(templates):
        y = 0.82 - index * 0.18
        template_axis.text(0.0, y, str(row["template"]), transform=template_axis.transAxes, ha="left", va="center", fontsize=7.5, fontweight="bold")
        template_axis.text(0.19, y, "N/A · 30×4 not evaluated", transform=template_axis.transAxes, ha="left", va="center", fontsize=7, color="#555555")
        template_axis.text(0.45, y, str(row["detail"]), transform=template_axis.transAxes, ha="left", va="center", fontsize=7)
    template_axis.text(0.5, -0.02, "MATCHED COMPARISON STOPPED", transform=template_axis.transAxes, ha="center", va="center", fontsize=9, fontweight="bold", color="#9a3f35")
    template_axis.text(0.5, -0.15, "No baseline, oracle, question set, accuracy, advantage, or cost result was produced.", transform=template_axis.transAxes, ha="center", va="center", fontsize=7, color="#9a3f35")

    fig.subplots_adjust(top=0.98, bottom=0.11, left=0.18, right=0.985)
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures / "rq7-benchmark-readiness.pdf")
    fig.savefig(figures / "rq7-benchmark-readiness.png", dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources, _ = source_contract(args.rq1_root)
    methods = derive_method_rows(args.rq1_root, sources)
    templates = derive_template_rows(methods)
    write_csv(args.output / "raw" / "rq7-source-contract.csv", sources)
    write_csv(args.output / "raw" / "rq7-method-readiness.csv", methods)
    write_csv(args.output / "raw" / "rq7-template-readiness.csv", templates)
    write_result(args.output / "result.md", sources, methods, templates)
    plot(args.output, sources, methods, templates)


if __name__ == "__main__":
    main()
