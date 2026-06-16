#!/usr/bin/env python3
"""Prepare the R193 human-evidence collection package.

R193 is logistics only. It packages blank R124 adequacy label sheets, blank R190
merge-risk label sheets, blank R203 long-tail promotion sheets, and pointers to
the already frozen R142 pilot launch materials. It must not fabricate labels,
responses, adjudications, map updates, or outcome claims.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "human-evidence-r193"
DEFAULT_R124_BLINDED = SCRIPT_DIR / "out" / "tag-adequacy-blinded-label-sheet-r124.csv"
DEFAULT_R124_JOIN = SCRIPT_DIR / "out" / "tag-adequacy-label-join-r124.json"
DEFAULT_R190_PACKET = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190" / "merge-risk-audit-packet-r190.csv"
DEFAULT_R190_SCORE = SCRIPT_DIR / "out" / "tag-consolidation-audit-r190" / "merge-risk-audit-results-r190.json"
DEFAULT_R203_PACKET = SCRIPT_DIR / "out" / "long-tail-promotion-r203" / "long-tail-promotion-packet-r203.csv"
DEFAULT_R203_SCORE = SCRIPT_DIR / "out" / "long-tail-promotion-r203" / "long-tail-promotion-r203.json"
DEFAULT_R142_LAUNCH = SCRIPT_DIR / "out" / "user-task-pilot-r142" / "launch"

R124_FIELDS = [
    "row_id",
    "fragment_index",
    "fragment_level",
    "redacted_preview",
    "candidate_tag",
    "rubric",
    "label",
    "notes",
]
R190_FIELDS = [
    "audit_id",
    "audit_type",
    "dimension",
    "raw_tag",
    "canonical_tag",
    "reason",
    "confidence",
    "profile_similarity",
    "support",
    "risk_reasons",
    "raw_top_processes",
    "raw_top_effects",
    "raw_top_paths",
    "raw_top_prompts",
    "raw_top_sessions",
    "audit_label",
    "audit_notes",
]
R203_FIELDS = [
    "promotion_id",
    "dimension",
    "raw_tag",
    "canonical_tag",
    "governance_action",
    "governance_reasons",
    "support",
    "top_processes",
    "top_effects",
    "top_context_tags",
    "regeneration_context_hash",
    "regenerated_tag",
    "grammar_valid",
    "changed_from_raw",
    "proposed_action",
    "promotion_label",
    "promotion_notes",
]
R124_LABEL_VALUES = ("adequate", "generic_noisy", "misleading")
R190_LABEL_VALUES = ("acceptable", "overmerge", "undermerge", "unclear")
R203_LABEL_VALUES = ("promote", "keep_raw", "reject", "split", "unclear")
SENSITIVE_RE = re.compile(
    r"/home/[A-Za-z0-9._-]+|Bearer|api[_-]?key|sk-[A-Za-z0-9]{20,}|ANTHROPIC_API|OPENAI_API",
    re.IGNORECASE,
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def scan_sensitive(path: Path) -> dict[str, Any]:
    findings = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        match = SENSITIVE_RE.search(line)
        if match:
            findings.append({"line": line_no, "match": match.group(0)})
    return {"status": "ok" if not findings else "fail", "findings": findings[:20]}


def validate_blank_columns(rows: list[dict[str, str]], fields: tuple[str, ...], path: Path) -> None:
    nonblank = []
    for row in rows:
        for field in fields:
            if (row.get(field) or "").strip():
                nonblank.append({"row": row, "field": field})
                break
    if nonblank:
        raise AssertionError(f"{path} contains nonblank collection fields: {nonblank[:3]}")


def validate_fields(actual: list[str], expected: list[str], path: Path) -> None:
    if actual != expected:
        raise AssertionError(f"{path} fields differ from expected contract: {actual}")


def package_r124(source: Path, out_dir: Path) -> dict[str, Any]:
    rows, fields = read_csv(source)
    validate_fields(fields, R124_FIELDS, source)
    validate_blank_columns(rows, ("label", "notes"), source)
    out_paths = {
        "labeler_1": out_dir / "r124-tag-adequacy-labeler-1.csv",
        "labeler_2": out_dir / "r124-tag-adequacy-labeler-2.csv",
    }
    for path in out_paths.values():
        copy_file(source, path)
        scan = scan_sensitive(path)
        if scan["status"] != "ok":
            raise AssertionError(f"{path} failed sensitive-text scan: {scan['findings']}")
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# R124 Tag Adequacy Labeling",
                "",
                "Give `r124-tag-adequacy-labeler-1.csv` and `r124-tag-adequacy-labeler-2.csv` to two independent labelers.",
                "Labelers should fill only `label` and `notes`.",
                "",
                "Allowed labels:",
                "- `adequate`: the tag preserves the main intent well enough for navigation.",
                "- `generic_noisy`: the tag is grammatical but too broad or visually noisy.",
                "- `misleading`: the tag points to the wrong task, object, or action.",
                "",
                "After both sheets are frozen, join and score:",
                "",
                "```bash",
                "python3 docs/visexp/r124_join_blinded_labels.py \\",
                "  --labeler-1 docs/visexp/out/human-evidence-r193/r124/r124-tag-adequacy-labeler-1.csv \\",
                "  --labeler-2 docs/visexp/out/human-evidence-r193/r124/r124-tag-adequacy-labeler-2.csv",
                "python3 docs/visexp/score_tag_adequacy.py \\",
                "  --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "row_count": len(rows),
        "label_values": list(R124_LABEL_VALUES),
        "source": {"path": rel(source), "sha256": sha256_file(source)},
        "outputs": {key: {"path": rel(path), "sha256": sha256_file(path)} for key, path in out_paths.items()},
        "readme": rel(readme),
        "human_labels_collected": 0,
        "claim_boundary": "R193 packages blank R124 sheets only; C6 remains unsupported until labels are collected and scored.",
    }


def package_r190(source: Path, score_path: Path, out_dir: Path) -> dict[str, Any]:
    rows, fields = read_csv(source)
    validate_fields(fields, R190_FIELDS, source)
    validate_blank_columns(rows, ("audit_label", "audit_notes"), source)
    out_paths = {
        "labeler_1": out_dir / "r190-merge-risk-labeler-1.csv",
        "labeler_2": out_dir / "r190-merge-risk-labeler-2.csv",
    }
    for path in out_paths.values():
        copy_file(source, path)
        scan = scan_sensitive(path)
        if scan["status"] != "ok":
            raise AssertionError(f"{path} failed sensitive-text scan: {scan['findings']}")
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# R190 Merge-Risk Labeling",
                "",
                "Give `r190-merge-risk-labeler-1.csv` and `r190-merge-risk-labeler-2.csv` to two independent labelers.",
                "Labelers should fill only `audit_label` and `audit_notes`.",
                "",
                "Allowed labels:",
                "- `acceptable`: the raw-to-canonical decision is acceptable for display aggregation.",
                "- `overmerge`: an applied merge hides a meaningfully distinct tag.",
                "- `undermerge`: a retained/review-only tag should be merged into the proposed canonical tag.",
                "- `unclear`: the row does not provide enough context for a confident judgment.",
                "",
                "After both sheets are frozen, score:",
                "",
                "```bash",
                "python3 docs/visexp/r190_score_merge_audit.py \\",
                "  --labeler-1 docs/visexp/out/human-evidence-r193/r190/r190-merge-risk-labeler-1.csv \\",
                "  --labeler-2 docs/visexp/out/human-evidence-r193/r190/r190-merge-risk-labeler-2.csv",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    score = json.loads(score_path.read_text(encoding="utf-8"))
    return {
        "row_count": len(rows),
        "label_values": list(R190_LABEL_VALUES),
        "source": {"path": rel(source), "sha256": sha256_file(source)},
        "current_score": {
            "path": rel(score_path),
            "sha256": sha256_file(score_path),
            "status": score.get("status"),
            "final_label_count": score.get("summary", {}).get("final_label_count"),
            "canonicalization_quality_supported": score.get("claim_gate", {}).get("canonicalization_quality_supported"),
        },
        "outputs": {key: {"path": rel(path), "sha256": sha256_file(path)} for key, path in out_paths.items()},
        "readme": rel(readme),
        "human_labels_collected": 0,
        "claim_boundary": "R193 packages blank R190 sheets only; canonicalization quality remains unsupported until labels are collected and scored.",
    }


def package_r203(source: Path, score_path: Path, out_dir: Path) -> dict[str, Any]:
    rows, fields = read_csv(source)
    validate_fields(fields, R203_FIELDS, source)
    validate_blank_columns(rows, ("promotion_label", "promotion_notes"), source)
    out_paths = {
        "labeler_1": out_dir / "r203-long-tail-promotion-labeler-1.csv",
        "labeler_2": out_dir / "r203-long-tail-promotion-labeler-2.csv",
    }
    for path in out_paths.values():
        copy_file(source, path)
        scan = scan_sensitive(path)
        if scan["status"] != "ok":
            raise AssertionError(f"{path} failed sensitive-text scan: {scan['findings']}")
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# R203 Long-Tail Promotion Labeling",
                "",
                "Give `r203-long-tail-promotion-labeler-1.csv` and `r203-long-tail-promotion-labeler-2.csv` to two independent labelers.",
                "Labelers should fill only `promotion_label` and `promotion_notes`.",
                "",
                "Allowed labels:",
                "- `promote`: the regenerated tag is better than the raw tag for display aggregation.",
                "- `keep_raw`: the raw tag should remain the display label.",
                "- `reject`: the regenerated tag is misleading or worse.",
                "- `split`: the row needs a contextual split instead of one replacement label.",
                "- `unclear`: the provided process/effect/context profile is insufficient.",
                "",
                "After both sheets are frozen, score:",
                "",
                "```bash",
                "python3 docs/visexp/r203_long_tail_promotion_gate.py \\",
                "  --labeler-1 docs/visexp/out/human-evidence-r193/r203/r203-long-tail-promotion-labeler-1.csv \\",
                "  --labeler-2 docs/visexp/out/human-evidence-r193/r203/r203-long-tail-promotion-labeler-2.csv",
                "```",
                "",
                "Accepted promotion labels still do not update the canonical map. A later reviewed display-map diff is required.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    score = json.loads(score_path.read_text(encoding="utf-8"))
    return {
        "row_count": len(rows),
        "label_values": list(R203_LABEL_VALUES),
        "source": {"path": rel(source), "sha256": sha256_file(source)},
        "current_score": {
            "path": rel(score_path),
            "sha256": sha256_file(score_path),
            "status": score.get("status"),
            "final_label_count": score.get("summary", {}).get("final_label_count"),
            "long_tail_promotion_review_supported": score.get("claim_gate", {}).get(
                "long_tail_promotion_review_supported"
            ),
            "canonical_map_updated": score.get("claim_gate", {}).get("canonical_map_updated"),
        },
        "outputs": {key: {"path": rel(path), "sha256": sha256_file(path)} for key, path in out_paths.items()},
        "readme": rel(readme),
        "human_labels_collected": 0,
        "claim_boundary": "R193 packages blank R203 sheets only; regenerated tags remain candidates until paired/adjudicated labels and a later reviewed map diff exist.",
    }


def package_r142(source_dir: Path, out_dir: Path) -> dict[str, Any]:
    manifest = source_dir / "manifest.json"
    readme = source_dir / "README.md"
    response_template = source_dir / "responses" / "user-task-response-template-r142-pilot.csv"
    for path in (manifest, readme, response_template):
        if not path.exists():
            raise AssertionError(f"missing R142 launch artifact: {path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    pointer = out_dir / "README.md"
    pointer.write_text(
        "\n".join(
            [
                "# R142 User-Task Pilot",
                "",
                "R142 launch materials are already frozen by R187. Use the participant packets under:",
                "",
                f"- `{rel(source_dir / 'participants')}`",
                "",
                "Collect completed response rows in a copy of:",
                "",
                f"- `{rel(response_template)}`",
                "",
                "Then score the completed CSV with:",
                "",
                "```bash",
                "python3 docs/visexp/score_user_task_results.py \\",
                "  --responses <completed-pilot-response.csv> \\",
                "  --bundle docs/visexp/out/user-task-benchmark.json \\",
                "  --answer-key docs/visexp/out/user-task-answer-key.csv \\",
                "  --assignments docs/visexp/out/user-task-assignments.csv \\",
                "  --out docs/visexp/out/user-task-pilot-r142",
                "```",
                "",
                "Do not distribute answer keys or scoring artifacts to participants.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    launch_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        "source_dir": rel(source_dir),
        "manifest": {"path": rel(manifest), "sha256": sha256_file(manifest)},
        "response_template": {"path": rel(response_template), "sha256": sha256_file(response_template)},
        "participant_count": launch_manifest.get("participant_count", 0),
        "real_response_count": launch_manifest.get("real_response_count", 0),
        "readme": rel(pointer),
        "claim_boundary": "R193 points to R142 launch materials only; C5 remains unsupported until real participant responses are scored.",
    }


def write_top_readme(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                "# R193 Human Evidence Collection Package",
                "",
                "This package contains blank collection materials only. It records no human labels and no participant responses.",
                "",
                "## Contents",
                "",
                f"- R124 tag adequacy sheets: `{manifest['r124']['outputs']['labeler_1']['path']}`, `{manifest['r124']['outputs']['labeler_2']['path']}`",
                f"- R190 merge-risk sheets: `{manifest['r190']['outputs']['labeler_1']['path']}`, `{manifest['r190']['outputs']['labeler_2']['path']}`",
                f"- R203 long-tail promotion sheets: `{manifest['r203']['outputs']['labeler_1']['path']}`, `{manifest['r203']['outputs']['labeler_2']['path']}`",
                f"- R142 pilot pointer: `{manifest['r142']['readme']}`",
                "",
                "## Evidence Boundary",
                "",
                "- R193 does not support C5 or C6.",
                "- R193 does not support canonicalization quality or long-tail promotion decisions.",
                "- Only completed, frozen, independent human sheets or participant responses can change those gates.",
                "",
                "## Next Commands",
                "",
                "Use the per-subdirectory READMEs for exact join/score commands after real data is collected.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir
    r124 = package_r124(args.r124_blinded, out_dir / "r124")
    r190 = package_r190(args.r190_packet, args.r190_score, out_dir / "r190")
    r203 = package_r203(args.r203_packet, args.r203_score, out_dir / "r203")
    r142 = package_r142(args.r142_launch, out_dir / "r142")
    manifest = {
        "schema_version": 1,
        "run_id": "R193",
        "status": "ready_for_human_collection",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "r124": r124,
        "r190": r190,
        "r203": r203,
        "r142": r142,
        "human_evidence_counts": {
            "r124_final_labels": 0,
            "r190_final_labels": 0,
            "r203_final_labels": 0,
            "r142_real_responses": r142.get("real_response_count", 0),
        },
        "claim_gate": {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "canonical_map_updated": False,
            "requires_real_human_data": True,
        },
        "claim_boundary": (
            "R193 is a collection logistics artifact. It does not contain or imply "
            "human adequacy labels, merge-risk labels, long-tail promotion labels, participant responses, "
            "canonical-map updates, or OSDI weak-accept evidence."
        ),
        "artifacts": {
            "manifest_json": rel(out_dir / "manifest.json"),
            "readme": rel(out_dir / "README.md"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    write_top_readme(out_dir / "README.md", manifest)
    write_json(out_dir / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "out": rel(out_dir)}, indent=2))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--r124-blinded", type=Path, default=DEFAULT_R124_BLINDED)
    parser.add_argument("--r124-join", type=Path, default=DEFAULT_R124_JOIN)
    parser.add_argument("--r190-packet", type=Path, default=DEFAULT_R190_PACKET)
    parser.add_argument("--r190-score", type=Path, default=DEFAULT_R190_SCORE)
    parser.add_argument("--r203-packet", type=Path, default=DEFAULT_R203_PACKET)
    parser.add_argument("--r203-score", type=Path, default=DEFAULT_R203_SCORE)
    parser.add_argument("--r142-launch", type=Path, default=DEFAULT_R142_LAUNCH)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
