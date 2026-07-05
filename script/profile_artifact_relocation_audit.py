#!/usr/bin/env python3
"""R343: relocated-checkout audit for historical profile-spec artifacts.

This audit does not fetch, sync, create, or relabel datasets. It checks that
historical profile specs containing the generating worktree's absolute
operation-file paths can still be interpreted from a relocated checkout by the
R342 composition audit and the R338 paper-claim audit.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from pathlib import Path
from typing import Any

import operation_profile_spec_composition_eval as r342
import paper_claim_integrity_audit as r338


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R324_DIR = OUT_ROOT / "operation-rank-feature-r324"
R342_DIR = OUT_ROOT / "operation-profile-spec-composition-r342"
DEFAULT_OUT_DIR = OUT_ROOT / "profile-artifact-relocation-r343"
RUN_ID = "R343"
RELOCATED_ROOT = Path("/tmp/agentsight-relocated-checkout")
ARTIFACT_MARKER = ("docs", "visexp", "out")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def format_value(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return ""
    return value


def git_check(description: str, path: Path, args: list[str]) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def tracked_clean(path: Path) -> bool:
    if not path.exists():
        return False
    git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
    git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
    git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
    return True


def artifact_suffix(value: str) -> Path:
    parts = Path(value).parts
    for index in range(0, len(parts) - len(ARTIFACT_MARKER) + 1):
        if parts[index : index + len(ARTIFACT_MARKER)] == ARTIFACT_MARKER:
            return Path(*parts[index:])
    raise SystemExit(f"path does not contain docs/visexp/out artifact suffix: {value}")


def relocated_probe_path(value: str) -> str:
    return str(RELOCATED_ROOT / artifact_suffix(value))


def check_operation_file_paths(
    r324_report: dict[str, Any],
    r342_report: dict[str, Any],
) -> list[dict[str, Any]]:
    r342_source_set = {r338.normalize_repo_path(path).resolve() for path in r342_report["source_paths"]}
    rows: list[dict[str, Any]] = []
    for detail in r324_report["tasks_detail"]:
        spec_path = ROOT / detail["profile_spec"]
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        raw_operation_files = spec.get("operation_files") or []
        if not raw_operation_files:
            raise SystemExit(f"profile spec has no operation_files: {rel(spec_path)}")
        for raw_value in raw_operation_files:
            expected = ROOT / artifact_suffix(raw_value)
            relocated_value = relocated_probe_path(raw_value)
            r342_current = r342.normalize_repo_path(raw_value)
            r342_relocated = r342.normalize_repo_path(relocated_value)
            r338_current = r338.normalize_repo_path(raw_value)
            r338_relocated = r338.normalize_repo_path(relocated_value)
            expected_resolved = expected.resolve()
            source_tracked_clean = tracked_clean(expected)
            status = (
                expected.exists()
                and source_tracked_clean
                and expected_resolved in r342_source_set
                and r342_current.resolve() == expected_resolved
                and r342_relocated.resolve() == expected_resolved
                and r338_current.resolve() == expected_resolved
                and r338_relocated.resolve() == expected_resolved
            )
            rows.append(
                {
                    "task": detail["task"],
                    "stack_kind": detail["stack_kind"],
                    "profile_spec": rel(spec_path),
                    "raw_operation_file": raw_value,
                    "raw_is_absolute": Path(raw_value).is_absolute(),
                    "relocated_probe": relocated_value,
                    "expected_repo_path": rel(expected),
                    "r342_current_normalized": rel(r342_current),
                    "r342_relocated_normalized": rel(r342_relocated),
                    "r338_current_normalized": rel(r338_current),
                    "r338_relocated_normalized": rel(r338_relocated),
                    "in_r342_source_paths": expected_resolved in r342_source_set,
                    "tracked_clean": source_tracked_clean,
                    "status": "pass" if status else "fail",
                }
            )
    return rows


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# R343 Relocated-Checkout Artifact Audit",
        "",
        f"- overall: `{summary['overall']}`",
        f"- operation file path checks: {summary['operation_file_path_checks_passed']}/{summary['operation_file_path_checks_total']}",
        f"- raw absolute operation files observed: {summary['raw_absolute_operation_files']}",
        f"- R338 source recompute variants/tasks: {summary['r338_recomputed_variants']}/{summary['r338_recomputed_tasks']}",
        f"- network access required: `{payload['source_policy']['network_access_required']}`",
        "",
        "This is a reproducibility audit over existing artifacts. It is not a new dataset, not a new accuracy benchmark, and not a new boundary detector.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row['task']))}</td>"
        f"<td>{html.escape(str(row['stack_kind']))}</td>"
        f"<td>{html.escape(str(row['status']))}</td>"
        f"<td>{html.escape(str(row['expected_repo_path']))}</td>"
        "</tr>"
        for row in payload["path_checks"]
    )
    page = f"""<!doctype html>
<meta charset="utf-8">
<title>R343 Relocated-Checkout Artifact Audit</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 0.35rem; text-align: left; }}
</style>
<h1>R343 Relocated-Checkout Artifact Audit</h1>
<p>Overall: <strong>{html.escape(str(summary['overall']))}</strong></p>
<p>Path checks: {summary['operation_file_path_checks_passed']}/{summary['operation_file_path_checks_total']}</p>
<table>
<thead><tr><th>Task</th><th>Stack</th><th>Status</th><th>Expected path</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""
    path.write_text(page, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    r324_report_path = R324_DIR / "rank-feature-report.json"
    r342_report_path = R342_DIR / "profile-spec-composition-report.json"
    r324_report = json.loads(r324_report_path.read_text(encoding="utf-8"))
    r342_report = json.loads(r342_report_path.read_text(encoding="utf-8"))
    path_checks = check_operation_file_paths(r324_report, r342_report)
    r338_variants, r338_tasks = r338.build_r342_rows_from_sources(r342_report)
    source_paths = sorted(
        {
            rel(r324_report_path),
            rel(r342_report_path),
            rel(R324_DIR / "rank-feature-summary.csv"),
            rel(R342_DIR / "profile-spec-composition-variants.csv"),
            rel(R342_DIR / "profile-spec-composition-tasks.csv"),
            *[row["profile_spec"] for row in path_checks],
            *[row["expected_repo_path"] for row in path_checks],
        }
    )
    passed = sum(row["status"] == "pass" for row in path_checks)
    overall = (
        "pass"
        if passed == len(path_checks)
        and len(r338_variants) == 12
        and len(r338_tasks) == 6
        and sum(row["profile_spec_composes_pipeline"] for row in r338_variants) == 12
        else "fail"
    )
    summary = {
        "overall": overall,
        "operation_file_path_checks_total": len(path_checks),
        "operation_file_path_checks_passed": passed,
        "raw_absolute_operation_files": sum(row["raw_is_absolute"] for row in path_checks),
        "r338_recomputed_variants": len(r338_variants),
        "r338_recomputed_tasks": len(r338_tasks),
        "r338_recomputed_composition_variants": sum(
            row["profile_spec_composes_pipeline"] for row in r338_variants
        ),
        "network_access_required": False,
    }
    return {
        "run_id": RUN_ID,
        "schema": "agentsight.profile-artifact-relocation-audit.v1",
        "source_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "hidden_label_use": "none; this audit checks artifact path portability only",
        },
        "source_paths": source_paths,
        "summary": summary,
        "path_checks": path_checks,
        "non_claims": [
            "R343 is not a new empirical accuracy result.",
            "R343 is not a human or agent analyst study.",
            "R343 does not claim automatic boundary discovery.",
            "R343 does not add a profiler abstraction beyond operation and operation stack.",
        ],
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "relocation-audit-report.json", payload)
    write_csv(
        out_dir / "relocation-checks.csv",
        payload["path_checks"],
        [
            "task",
            "stack_kind",
            "profile_spec",
            "raw_operation_file",
            "raw_is_absolute",
            "relocated_probe",
            "expected_repo_path",
            "r342_current_normalized",
            "r342_relocated_normalized",
            "r338_current_normalized",
            "r338_relocated_normalized",
            "in_r342_source_paths",
            "tracked_clean",
            "status",
        ],
    )
    build_markdown(out_dir / "relocation-audit-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": payload["schema"],
            "summary": payload["summary"],
        },
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
