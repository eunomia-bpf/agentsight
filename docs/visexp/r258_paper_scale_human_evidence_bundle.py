#!/usr/bin/env python3
"""R258: unified paper-scale human-evidence launch bundle.

R249 makes paper-scale C5 participant packets, R252 makes paper-scale C6
labeler packets, and R255 verifies the R249 assignment path through R195. R258
packages those collection inputs into one sendable bundle and verifies the
return-file contract. It is logistics only: it adds no participant responses,
no human labels, and no weak-accept evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
RUN_ID = "R258"

R249_DIR = OUT_DIR / "user-task-paper-r249"
R249_MANIFEST = R249_DIR / "manifest.json"
R252_DIR = OUT_DIR / "tag-adequacy-paper-r252"
R252_MANIFEST = R252_DIR / "manifest.json"
R255_JSON = OUT_DIR / "human-evidence-paper-bridge-r255" / "paper-scale-r195-bridge-r255.json"
R257_JSON = OUT_DIR / "osdi-gate-review-r257.json"

DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-paper-scale-bundle-r258"
PACKAGE_ROOT = "agentflame-paper-scale-human-evidence-r258"
PACKAGE_NAME = f"{PACKAGE_ROOT}.tar.gz"

C5_RESPONSE = "c5/user-task-response-template-r249-paper.csv"
C5_ASSIGNMENT = "c5/user-task-assignments-r249-paper.csv"
C6_RETURN_FILES = [
    ("c6/L01/r124-labeler-1.csv", "r124-labeler-1.csv", "C6 tag adequacy", "yes"),
    ("c6/L02/r124-labeler-2.csv", "r124-labeler-2.csv", "C6 tag adequacy", "yes"),
    ("c6/L01/r190-labeler-1.csv", "r190-labeler-1.csv", "canonicalization quality", "if claiming merge quality"),
    ("c6/L02/r190-labeler-2.csv", "r190-labeler-2.csv", "canonicalization quality", "if claiming merge quality"),
    ("c6/L01/r203-labeler-1.csv", "r203-labeler-1.csv", "long-tail promotion quality", "if claiming regenerated-tag promotion"),
    ("c6/L02/r203-labeler-2.csv", "r203-labeler-2.csv", "long-tail promotion quality", "if claiming regenerated-tag promotion"),
]

FORBIDDEN_TEXT = [
    "/home/",
    "/tmp/",
    ".codex/sessions",
    ".claude",
    "ANTHROPIC_API",
    "OPENAI_API",
    "user-task-answer-key.csv",
    "answer_json",
    "oracle_sources",
    "expected_response",
    "correct_response",
    "score_user_task_results.py",
    "synthetic-exports",
    "r244_synthetic_export_smoke",
]
FORBIDDEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"/(?:var/)?tmp/[^\s,;\"'<>)]*", re.IGNORECASE),
    re.compile(r"/private/tmp/[^\s,;\"'<>)]*", re.IGNORECASE),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def csv_row_count(path: Path) -> int:
    rows, _ = read_csv(path)
    return len(rows)


def source_hashes(paths: list[Path]) -> dict[str, str]:
    return {rel(path): sha256_file(path) for path in paths if path.exists()}


def add_file_to_tar(tar: tarfile.TarFile, source: Path, arcname: str) -> None:
    info = tar.gettarinfo(str(source), arcname=arcname)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    with source.open("rb") as handle:
        tar.addfile(info, handle)


def write_tarball(package_path: Path, files: list[tuple[Path, str]]) -> None:
    package_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(package_path, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for source, arcname in sorted(files, key=lambda item: item[1]):
            add_file_to_tar(tar, source, arcname)


def tar_members(package_path: Path) -> list[dict[str, Any]]:
    with tarfile.open(package_path, "r:gz") as tar:
        return [
            {
                "name": member.name,
                "size": member.size,
                "type": "file" if member.isfile() else "other",
            }
            for member in tar.getmembers()
        ]


def scan_text(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if path.suffix.lower() not in {".csv", ".html", ".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TEXT:
            if token.lower() in text.lower():
                hits.append({"path": rel(path), "token": token})
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                hits.append({"path": rel(path), "pattern": pattern.pattern})
    return {"hits": hits, "passed": not hits}


def scan_tarball(package_path: Path) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    with tarfile.open(package_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            text = extracted.read().decode("utf-8", errors="replace")
            for token in FORBIDDEN_TEXT:
                if token.lower() in text.lower():
                    hits.append({"member": member.name, "token": token})
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    hits.append({"member": member.name, "pattern": pattern.pattern})
    return {"hits": hits, "passed": not hits}


def c5_readme() -> str:
    return f"""# C5 Paper-Scale Participant Packets

This directory contains twelve blinded participant packets, `P01` through
`P12`, and the response template for the coordinator's private completed
response file.

Participants should receive only their assigned packet. The coordinator should
copy `{C5_RESPONSE}`, fill one row per task from real participant responses,
and then score the completed private CSV through the R195 pipeline with the
R249 assignment file.

These packets contain no answer key. Blank templates are not evidence.
"""


def c5_files(c5_readme_path: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = [
        (c5_readme_path, f"{PACKAGE_ROOT}/c5/README.md"),
        (R249_DIR / "user-task-assignments-r249-paper.csv", f"{PACKAGE_ROOT}/{C5_ASSIGNMENT}"),
        (R249_DIR / "responses" / "user-task-response-template-r249-paper.csv", f"{PACKAGE_ROOT}/{C5_RESPONSE}"),
    ]
    for participant_id in [f"P{i:02d}" for i in range(1, 13)]:
        files.extend(
            [
                (
                    R249_DIR / "participants" / f"{participant_id}.md",
                    f"{PACKAGE_ROOT}/c5/participants/{participant_id}.md",
                ),
                (
                    R249_DIR / "participants" / f"{participant_id}.json",
                    f"{PACKAGE_ROOT}/c5/participants/{participant_id}.json",
                ),
            ]
        )
    return files


def c6_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = [
        (R252_DIR / "README.md", f"{PACKAGE_ROOT}/c6/README.md"),
    ]
    for source_rel, _, _, _ in C6_RETURN_FILES:
        source = R252_DIR / "labeler-packets" / source_rel.removeprefix("c6/")
        files.append((source, f"{PACKAGE_ROOT}/{source_rel}"))
    for name in [
        "r124-labeler-1.csv",
        "r124-labeler-2.csv",
        "r190-labeler-1.csv",
        "r190-labeler-2.csv",
        "r203-labeler-1.csv",
        "r203-labeler-2.csv",
    ]:
        files.append((R252_DIR / "blank-r195-inbox-template" / name, f"{PACKAGE_ROOT}/r195-inbox-template/{name}"))
    return files


def return_checklist_rows(r249: dict[str, Any], r252: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "return_file": "user-task-response-template-r249-paper.csv",
            "package_path": C5_RESPONSE,
            "destination": "private/completed-paper-scale-c5/user-task-response-template-r249-paper.csv",
            "row_count": r249.get("response_template", {}).get("row_count", 168),
            "claim_gate": "C5 developer utility",
            "required_for_weak_accept": "yes",
            "notes": (
                "Coordinator fills this private copy with real P01-P12 responses, then passes it to "
                "r195_human_evidence_pipeline.py using --r142-responses and the R249 assignment file."
            ),
        },
        {
            "return_file": "user-task-assignments-r249-paper.csv",
            "package_path": C5_ASSIGNMENT,
            "destination": "docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv",
            "row_count": r249.get("assignment_metrics", {}).get("assignment_count", 168),
            "claim_gate": "C5 scoring contract",
            "required_for_weak_accept": "yes",
            "notes": "Use this nondefault assignment file with R195; R255 verifies the old R142 assignment is rejected.",
        },
    ]
    for source_rel, return_name, claim_gate, required in C6_RETURN_FILES:
        rows.append(
            {
                "return_file": return_name,
                "package_path": source_rel,
                "destination": f"docs/visexp/out/human-evidence-r195/inbox/{return_name}",
                "row_count": csv_row_count(R252_DIR / "labeler-packets" / source_rel.removeprefix("c6/")),
                "claim_gate": claim_gate,
                "required_for_weak_accept": required,
                "notes": "Collect independent human labels; do not fill these with an LLM.",
            }
        )
    rows.append(
        {
            "return_file": "r195-inbox-template/*",
            "package_path": "r195-inbox-template/",
            "destination": "docs/visexp/out/human-evidence-r195/inbox/",
            "row_count": r252.get("total_independent_label_decisions_required", 1002),
            "claim_gate": "C6 filename contract",
            "required_for_weak_accept": "template only",
            "notes": "Blank filename template for coordinator setup; blank files are not evidence.",
        }
    )
    return rows


def package_readme(rows: list[dict[str, Any]]) -> str:
    table = "\n".join(
        f"| `{row['return_file']}` | `{row['package_path']}` | {row['row_count']} | `{row['required_for_weak_accept']}` |"
        for row in rows
    )
    return f"""# AgentFlame Paper-Scale Human Evidence Bundle R258

This package combines the paper-scale C5 participant packets from R249 and the
paper-scale C6 labeler packets from R252. It contains collection inputs only.
It contains no answer key, scorer script, raw agent trace, participant response,
human label, or synthetic smoke output.

## Collection Flow

1. Send `c5/participants/P01.md` through `P12.md` to the corresponding
   participants.
2. Keep a private completed copy of `{C5_RESPONSE}` and fill one row per task.
3. Send `c6/L01/*.csv` and `c6/L02/*.csv` to two independent labelers.
4. Put completed returned files into the R195 inbox or pass them explicitly to
   `python3 docs/visexp/r195_human_evidence_pipeline.py`.
5. Do not claim C5, C6, or weak accept until R195 scores real completed returns.

## Return Files

| File | Package path | Rows | Required gate |
|------|--------------|------|---------------|
{table}

Blank templates, this tarball, subagent review, synthetic rows, or LLM-filled
labels cannot upgrade any claim gate.
"""


def package_manifest(rows: list[dict[str, Any]], r249: dict[str, Any], r252: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "package_root": PACKAGE_ROOT,
        "source_artifacts": {
            "r249": rel(R249_MANIFEST),
            "r252": rel(R252_MANIFEST),
            "r255": rel(R255_JSON),
            "r257": rel(R257_JSON),
        },
        "collection_inputs": {
            "c5_participant_packets": r249.get("participant_packet_count"),
            "c5_response_rows": r249.get("response_template", {}).get("rows"),
            "c6_labeler_packets": r252.get("labeler_packet_count"),
            "c6_rows_per_labeler": r252.get("rows_per_labeler"),
            "c6_required_label_decisions": r252.get("total_independent_label_decisions_required"),
        },
        "return_files": rows,
        "claim_boundary": (
            "R258 is a unified paper-scale collection bundle. It improves launch "
            "logistics only and adds no real participant responses, no human labels, "
            "no C5 utility evidence, no C6 adequacy evidence, and no weak-accept evidence."
        ),
        "claim_gate": {
            "c5_supported": False,
            "c6_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "weak_accept_supported": False,
            "outcome_evidence_added": False,
            "requires_real_human_returns": True,
        },
    }


def build_bundle(out_dir: Path) -> dict[str, Any]:
    r249 = read_json(R249_MANIFEST)
    r252 = read_json(R252_MANIFEST)
    r255 = read_json(R255_JSON)
    r257 = read_json(R257_JSON)
    repo_commit = git(["rev-parse", "HEAD"])
    repo_dirty = bool(git(["status", "--porcelain"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    checklist = return_checklist_rows(r249, r252)
    checklist_path = out_dir / "return-checklist-r258.csv"
    readme_path = out_dir / "README-r258.md"
    c5_readme_path = out_dir / "c5-README-r258.md"
    inner_manifest_path = out_dir / "package-manifest-r258.json"
    package_path = out_dir / PACKAGE_NAME
    file_list_path = out_dir / "package-files-r258.txt"

    write_csv(
        checklist_path,
        checklist,
        ["return_file", "package_path", "destination", "row_count", "claim_gate", "required_for_weak_accept", "notes"],
    )
    write_text(readme_path, package_readme(checklist))
    write_text(c5_readme_path, c5_readme())
    inner_manifest = package_manifest(checklist, r249, r252)
    write_json(inner_manifest_path, inner_manifest)

    package_files: list[tuple[Path, str]] = []
    package_files.extend(c5_files(c5_readme_path))
    package_files.extend(c6_files())
    package_files.extend(
        [
            (checklist_path, f"{PACKAGE_ROOT}/return-checklist-r258.csv"),
            (readme_path, f"{PACKAGE_ROOT}/README-r258.md"),
            (inner_manifest_path, f"{PACKAGE_ROOT}/package-manifest-r258.json"),
        ]
    )
    missing_files = [rel(source) for source, _ in package_files if not source.exists()]
    if missing_files:
        raise FileNotFoundError(f"missing package inputs: {missing_files[:5]}")

    source_scan = scan_text([source for source, _ in package_files])
    write_tarball(package_path, package_files)
    members = tar_members(package_path)
    member_names = [member["name"] for member in members]
    write_text(file_list_path, "\n".join(member_names) + "\n")
    tar_scan = scan_tarball(package_path)

    c5_response_rows = csv_row_count(R249_DIR / "responses" / "user-task-response-template-r249-paper.csv")
    c5_assignment_rows = csv_row_count(R249_DIR / "user-task-assignments-r249-paper.csv")
    c6_packet_rows = sum(
        csv_row_count(R252_DIR / "labeler-packets" / source_rel.removeprefix("c6/"))
        for source_rel, _, _, _ in C6_RETURN_FILES
    )
    c6_inbox_template_rows = sum(
        csv_row_count(R252_DIR / "blank-r195-inbox-template" / name)
        for name in [
            "r124-labeler-1.csv",
            "r124-labeler-2.csv",
            "r190-labeler-1.csv",
            "r190-labeler-2.csv",
            "r203-labeler-1.csv",
            "r203-labeler-2.csv",
        ]
    )

    expected_member_count = len(package_files)
    expected_participant_files = 12 * 2
    participant_members = [name for name in member_names if "/c5/participants/" in name]

    checks = {
        "r249_ready_no_responses": r249.get("status") == "paper_scale_launch_ready_no_responses"
        and r249.get("real_response_count") == 0
        and r249.get("claim_gate", {}).get("c5_supported") is False,
        "r252_ready_no_labels": r252.get("status") == "paper_scale_label_collection_ready_no_labels"
        and r252.get("actual_human_final_labels") == 0
        and r252.get("claim_gate", {}).get("c6_adequacy_supported") is False,
        "r255_bridge_passed_no_outcomes": r255.get("status") == "passed"
        and r255.get("claim_gate", {}).get("c5_supported") is False
        and r255.get("claim_gate", {}).get("weak_accept_supported") is False,
        "r257_review_gate_passed_no_outcomes": r257.get("status") == "post_r256_review_gate_passed"
        and r257.get("claim_gate", {}).get("weak_accept_supported") is False,
        "participant_packet_count": len(participant_members) == expected_participant_files,
        "c5_response_template_rows": c5_response_rows == 168,
        "c5_assignment_rows": c5_assignment_rows == 168,
        "c6_packet_rows": c6_packet_rows == 1002,
        "c6_inbox_template_rows": c6_inbox_template_rows == 1002,
        "return_checklist_rows": len(checklist) == 9,
        "source_leak_scan_passed": source_scan["passed"],
        "tar_member_count_matches": len(members) == expected_member_count,
        "tar_leak_scan_passed": tar_scan["passed"],
        "no_outcome_evidence_added": True,
    }

    summary = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": "paper_scale_human_evidence_bundle_ready_no_outcomes" if all(checks.values()) else "paper_scale_human_evidence_bundle_failed",
        "generated_at": now_iso(),
        "source_command": "python3 docs/visexp/r258_paper_scale_human_evidence_bundle.py",
        "package": {
            "path": rel(package_path),
            "sha256": sha256_file(package_path),
            "bytes": package_path.stat().st_size,
            "member_count": len(members),
            "members": members,
            "file_list": rel(file_list_path),
        },
        "artifacts": {
            "summary_json": rel(out_dir / "human-evidence-paper-scale-bundle-r258.json"),
            "summary_md": rel(out_dir / "human-evidence-paper-scale-bundle-r258.md"),
            "return_checklist": rel(checklist_path),
            "package_readme": rel(readme_path),
            "c5_readme": rel(c5_readme_path),
            "package_manifest": rel(inner_manifest_path),
            "tarball": rel(package_path),
            "package_file_list": rel(file_list_path),
        },
        "collection_inputs": inner_manifest["collection_inputs"],
        "return_files": checklist,
        "checks": checks,
        "source_leak_scan": source_scan,
        "tar_leak_scan": tar_scan,
        "claim_boundary": inner_manifest["claim_boundary"],
        "claim_gate": inner_manifest["claim_gate"],
        "provenance": {
            "repo_commit": repo_commit,
            "repo_dirty": repo_dirty,
            "generator": rel(Path(__file__)),
            "source_hashes": source_hashes([R249_MANIFEST, R252_MANIFEST, R255_JSON, R257_JSON]),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
    }
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{row['return_file']}` | `{row['package_path']}` | {row['row_count']} | `{row['required_for_weak_accept']}` |"
        for row in summary["return_files"]
    )
    checks = "\n".join(f"| `{name}` | `{value}` |" for name, value in summary["checks"].items())
    gate = summary["claim_gate"]
    inputs = summary["collection_inputs"]
    return f"""# R258 Paper-Scale Human Evidence Bundle

Status: `{summary['status']}`

R258 packages the R249 C5 paper-scale participant materials and R252 C6 labeler
materials into one sendable tarball. It does not create or score outcome data.

## Package

- path: `{summary['package']['path']}`
- sha256: `{summary['package']['sha256']}`
- bytes: `{summary['package']['bytes']}`
- members: `{summary['package']['member_count']}`

## Collection Inputs

- C5 participant packets: `{inputs['c5_participant_packets']}`
- C5 response rows: `{inputs['c5_response_rows']}`
- C6 labeler packets: `{inputs['c6_labeler_packets']}`
- C6 rows per labeler: `{inputs['c6_rows_per_labeler']}`
- C6 required independent decisions: `{inputs['c6_required_label_decisions']}`

## Return Files

| File | Package path | Rows | Required gate |
|------|--------------|------|---------------|
{rows}

## Checks

| Check | Passed |
|-------|--------|
{checks}

## Claim Gate

- weak_accept_supported: `{gate['weak_accept_supported']}`
- c5_supported: `{gate['c5_supported']}`
- c6_supported: `{gate['c6_supported']}`
- c6_adequacy_supported: `{gate['c6_adequacy_supported']}`
- canonicalization_quality_supported: `{gate['canonicalization_quality_supported']}`
- long_tail_promotion_review_supported: `{gate['long_tail_promotion_review_supported']}`
- outcome_evidence_added: `{gate['outcome_evidence_added']}`
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    summary = build_bundle(args.out_dir)
    write_json(args.out_dir / "human-evidence-paper-scale-bundle-r258.json", summary)
    write_text(args.out_dir / "human-evidence-paper-scale-bundle-r258.md", render_markdown(summary))

    if summary["status"] != "paper_scale_human_evidence_bundle_ready_no_outcomes":
        failed = [name for name, ok in summary["checks"].items() if not ok]
        print(f"R258 bundle failed: {failed}")
        return 1
    print(
        "R258 paper-scale human-evidence bundle ready: "
        f"{summary['package']['member_count']} members, {summary['package']['bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
