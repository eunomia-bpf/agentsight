#!/usr/bin/env python3
"""R247: build a sendable human-evidence collection bundle.

This is a logistics artifact, not outcome evidence. It packages the R243 static
forms into a single offline tarball, writes a return-file checklist for R195,
and verifies that the package excludes answer keys, scorer scripts, raw traces,
and R244 synthetic exports.
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

KIT_DIR = OUT_DIR / "human-evidence-collection-kit-r243"
R243_MANIFEST = KIT_DIR / "collection-kit-r243.json"
R244_MANIFEST = OUT_DIR / "human-evidence-collection-kit-export-smoke-r244" / "collection-kit-export-smoke-r244.json"
R207_MANIFEST = OUT_DIR / "human-evidence-launch-r207" / "human-evidence-launch-r207.json"
R195_MANIFEST = OUT_DIR / "human-evidence-pipeline-r195.json"
R246_REVIEW = OUT_DIR / "osdi-gate-review-r246.json"

DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-distribution-r247"
PACKAGE_ROOT = "agentflame-human-evidence-r247"
PACKAGE_NAME = "agentflame-human-evidence-r247.tar.gz"

FORBIDDEN_TOKENS = [
    "/home/",
    ".codex/sessions",
    ".claude",
    "user-task-answer-key.csv",
    "answer_json",
    "expected_response",
    "correct_response",
    "score_user_task_results.py",
    "synthetic-exports",
    "r244_synthetic_export_smoke",
]


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def csv_row_count(path: Path) -> int:
    rows, _ = read_csv(path)
    return len(rows)


def source_hashes(paths: list[Path]) -> dict[str, str]:
    return {rel(path) or str(path): sha256_file(path) for path in paths if path.exists()}


def required_kit_files(manifest: dict[str, Any]) -> list[Path]:
    files = [
        KIT_DIR / "index.html",
        KIT_DIR / "README.md",
    ]
    forms = manifest.get("forms", {})
    for group in ["participant_forms", "labeler_forms", "coordinator_forms"]:
        for form in forms.get(group, []):
            files.append(REPO_ROOT / form["html_path"])
    return sorted({path.resolve() for path in files})


def return_checklist_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    forms = manifest.get("forms", {})
    rows: list[dict[str, Any]] = [
        {
            "return_file": "r142-pilot-responses.csv",
            "source": "coordinator/r142-merge.html",
            "row_count": 70,
            "r195_group": "C5 developer utility",
            "required_for_weak_accept": "yes",
            "destination": "docs/visexp/out/human-evidence-r195/inbox/r142-pilot-responses.csv",
            "notes": "Merge P01-P05 participant exports with the coordinator page; do not submit individual participant CSVs to R195.",
        }
    ]
    for form in forms.get("labeler_forms", []):
        group = form["group"]
        if group == "r124":
            r195_group = "C6 tag adequacy"
            required = "yes"
        elif group == "r190":
            r195_group = "canonicalization quality"
            required = "if claiming merge quality"
        else:
            r195_group = "long-tail promotion quality"
            required = "if claiming regenerated-tag promotion"
        rows.append(
            {
                "return_file": form["output_name"],
                "source": form["relative_link"],
                "row_count": form["row_count"],
                "r195_group": r195_group,
                "required_for_weak_accept": required,
                "destination": f"docs/visexp/out/human-evidence-r195/inbox/{form['output_name']}",
                "notes": "Two independent labelers are required before scoring; adjudication may be needed for disagreements.",
            }
        )
    return rows


def package_readme(checklist_rows: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| `{row['return_file']}` | `{row['source']}` | {row['row_count']} | {row['required_for_weak_accept']} |"
        for row in checklist_rows
    )
    return f"""# AgentFlame Human Evidence Bundle R247

This offline bundle contains static HTML forms for the R142 participant pilot
and R124/R190/R203 human label collection. It contains no answer key, scorer
script, raw agent trace, or synthetic smoke export.

Open `index.html` in a browser. Participant forms export per-participant CSVs.
Use `coordinator/r142-merge.html` to merge P01-P05 exports into the R195-ready
`r142-pilot-responses.csv` file.

Returned files:

| File | Source form | Rows | Required gate |
|------|-------------|------|---------------|
{rows}

After real returns exist, place them in `docs/visexp/out/human-evidence-r195/inbox`
using the exact filenames above, then run:

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py
```

Do not treat this bundle, blank forms, synthetic exports, subagent review, or
LLM-filled labels as C5/C6 evidence. Only scored real returns can change those
claim gates.
"""


def html_link_scan(files: list[Path]) -> dict[str, Any]:
    external: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    link_re = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
    for path in files:
        if path.suffix.lower() != ".html":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in link_re.finditer(text):
            link = match.group(1)
            if link.startswith(("http://", "https://", "//")):
                external.append({"path": rel(path) or str(path), "link": link})
            if link.startswith(("#", "data:", "mailto:", "javascript:")):
                continue
            if "://" in link or link.startswith("//"):
                continue
            target = (path.parent / link).resolve()
            if not target.exists():
                missing.append({"path": rel(path) or str(path), "link": link})
    return {
        "external_links": external,
        "missing_relative_links": missing,
        "passed": not external and not missing,
    }


def leak_scan(files: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in files:
        if path.suffix.lower() not in {".html", ".md", ".json", ".csv", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                hits.append({"path": rel(path) or str(path), "token": token})
    return {
        "forbidden_tokens": FORBIDDEN_TOKENS,
        "hits": hits,
        "passed": not hits,
    }


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


def build_bundle(out_dir: Path) -> dict[str, Any]:
    r243 = read_json(R243_MANIFEST)
    r244 = read_json(R244_MANIFEST)
    r207 = read_json(R207_MANIFEST)
    r195 = read_json(R195_MANIFEST)
    r246 = read_json(R246_REVIEW)
    repo_commit = git(["rev-parse", "HEAD"])
    repo_dirty = bool(git(["status", "--porcelain"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    checklist = return_checklist_rows(r243)
    checklist_path = out_dir / "return-checklist-r247.csv"
    readme_path = out_dir / "README-r247.md"
    inner_manifest_path = out_dir / "package-manifest-r247.json"
    package_path = out_dir / PACKAGE_NAME

    write_csv(
        checklist_path,
        checklist,
        ["return_file", "source", "row_count", "r195_group", "required_for_weak_accept", "destination", "notes"],
    )
    write_text(readme_path, package_readme(checklist))

    kit_files = required_kit_files(r243)
    link_check = html_link_scan(kit_files)
    leak_check = leak_scan(kit_files + [checklist_path, readme_path])
    form_counts = {
        "participant_forms": len(r243.get("forms", {}).get("participant_forms", [])),
        "labeler_forms": len(r243.get("forms", {}).get("labeler_forms", [])),
        "coordinator_forms": len(r243.get("forms", {}).get("coordinator_forms", [])),
    }

    inner_manifest = {
        "schema_version": 1,
        "run_id": "R247",
        "package_root": PACKAGE_ROOT,
        "source_artifacts": {
            "r243": rel(R243_MANIFEST),
            "r244": rel(R244_MANIFEST),
            "r207": rel(R207_MANIFEST),
            "r195": rel(R195_MANIFEST),
            "r246": rel(R246_REVIEW),
        },
        "forms": form_counts,
        "return_files": checklist,
        "claim_boundary": (
            "R247 is a sendable distribution bundle for collecting real human "
            "returns. It is not participant evidence, not human-label evidence, "
            "and not a weak-accept result."
        ),
        "claim_gate": {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "weak_accept_supported": False,
            "outcome_evidence_added": False,
            "requires_real_human_returns": True,
        },
    }
    write_json(inner_manifest_path, inner_manifest)

    files_for_package: list[tuple[Path, str]] = []
    for path in kit_files:
        relative = path.relative_to(KIT_DIR.resolve())
        files_for_package.append((path, f"{PACKAGE_ROOT}/{relative}"))
    files_for_package.extend(
        [
            (checklist_path, f"{PACKAGE_ROOT}/return-checklist-r247.csv"),
            (readme_path, f"{PACKAGE_ROOT}/README-r247.md"),
            (inner_manifest_path, f"{PACKAGE_ROOT}/package-manifest-r247.json"),
        ]
    )
    write_tarball(package_path, files_for_package)
    members = tar_members(package_path)

    packaged_paths = {member["name"] for member in members}
    expected_member_count = len(files_for_package)
    tar_leak_tokens = []
    with tarfile.open(package_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            text = extracted.read().decode("utf-8", errors="replace")
            for token in FORBIDDEN_TOKENS:
                if token in text:
                    tar_leak_tokens.append({"member": member.name, "token": token})

    checks = {
        "r243_ready": r243.get("status") == "collection_kit_ready_no_outcomes",
        "r244_export_smoke_passed": r244.get("status") == "collection_kit_export_smoke_passed",
        "r207_launch_ready": r207.get("status") == "launch_ready_no_outcomes",
        "r195_awaiting_inputs": r195.get("status") == "awaiting_human_inputs",
        "r246_gate_passed": r246.get("status") == "post_review_hygiene_passed",
        "form_counts_match": form_counts == {
            "participant_forms": 5,
            "labeler_forms": 6,
            "coordinator_forms": 1,
        },
        "return_checklist_rows": len(checklist) == 7,
        "html_links_local": link_check["passed"],
        "source_leak_scan_passed": leak_check["passed"],
        "tar_member_count_matches": len(members) == expected_member_count,
        "tar_leak_scan_passed": not tar_leak_tokens,
        "no_synthetic_exports_packaged": not any("synthetic-exports" in member for member in packaged_paths),
    }

    package_size = package_path.stat().st_size
    summary = {
        "schema_version": 1,
        "run_id": "R247",
        "status": "distribution_bundle_ready_no_outcomes" if all(checks.values()) else "distribution_bundle_failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "python3 docs/visexp/r247_human_evidence_distribution_bundle.py",
        "package": {
            "path": rel(package_path),
            "sha256": sha256_file(package_path),
            "bytes": package_size,
            "member_count": len(members),
            "members": members,
        },
        "artifacts": {
            "summary_json": rel(out_dir / "human-evidence-distribution-r247.json"),
            "summary_md": rel(out_dir / "human-evidence-distribution-r247.md"),
            "return_checklist": rel(checklist_path),
            "bundle_readme": rel(readme_path),
            "package_manifest": rel(inner_manifest_path),
            "tarball": rel(package_path),
        },
        "forms": form_counts,
        "return_files": checklist,
        "checks": checks,
        "link_check": link_check,
        "leak_check": leak_check,
        "tar_leak_hits": tar_leak_tokens,
        "claim_boundary": inner_manifest["claim_boundary"],
        "claim_gate": inner_manifest["claim_gate"],
        "provenance": {
            "repo_commit": repo_commit,
            "repo_dirty": repo_dirty,
            "generator": rel(Path(__file__)),
            "source_hashes": source_hashes([R243_MANIFEST, R244_MANIFEST, R207_MANIFEST, R195_MANIFEST, R246_REVIEW]),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
    }
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    checks = summary["checks"]
    rows = "\n".join(
        f"| `{row['return_file']}` | `{row['source']}` | {row['row_count']} | {row['required_for_weak_accept']} |"
        for row in summary["return_files"]
    )
    check_rows = "\n".join(
        f"| `{name}` | `{value}` |"
        for name, value in checks.items()
    )
    gate = summary["claim_gate"]
    return f"""# R247 Human Evidence Distribution Bundle

Status: `{summary['status']}`

R247 packages the already-tested R243 static collection kit into one offline
tarball and records the exact R195 return filenames. It does not create or
score human evidence.

## Package

- path: `{summary['package']['path']}`
- sha256: `{summary['package']['sha256']}`
- bytes: `{summary['package']['bytes']}`
- members: `{summary['package']['member_count']}`

## Return Files

| File | Source | Rows | Required gate |
|------|--------|------|---------------|
{rows}

## Checks

| Check | Passed |
|-------|--------|
{check_rows}

## Claim Gate

- weak_accept_supported: `{gate['weak_accept_supported']}`
- c5_supported: `{gate['c5_supported']}`
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
    write_json(args.out_dir / "human-evidence-distribution-r247.json", summary)
    write_text(args.out_dir / "human-evidence-distribution-r247.md", render_markdown(summary))

    if summary["status"] != "distribution_bundle_ready_no_outcomes":
        failed = [name for name, ok in summary["checks"].items() if not ok]
        print(f"R247 distribution bundle failed: {failed}")
        return 1
    print(
        "R247 distribution bundle ready: "
        f"{summary['package']['member_count']} members, {summary['package']['bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
