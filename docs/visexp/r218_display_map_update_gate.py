#!/usr/bin/env python3
"""R218: reviewed display-map update gate for long-tail compaction.

This run exercises the promotion/update mechanism, not label quality. It reads
the generated R209 display map, selects real pending profile/regeneration
candidate rows, and applies synthetic review fixtures to a preview map. Only
final consensus/adjudicated `promote` rows with valid one-word display tags are
accepted. Unsafe rows are rejected. The canonical map and raw traces are not
modified.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "display-map-update-gate-r218"

FIXTURE_FIELDS = [
    "case",
    "dimension",
    "raw_tag",
    "from_display_tag",
    "to_display_tag",
    "review_label",
    "review_source",
    "label_state",
    "candidate_valid",
    "expected_result",
    "reason",
]

DIFF_FIELDS = [
    "case",
    "dimension",
    "raw_tag",
    "from_display_tag",
    "to_display_tag",
    "support",
    "diff_source",
    "review_source",
    "reason",
]

REJECT_FIELDS = [
    "case",
    "dimension",
    "raw_tag",
    "from_display_tag",
    "to_display_tag",
    "review_label",
    "review_source",
    "label_state",
    "candidate_valid",
    "reject_reason",
]

PREVIEW_FIELDS = [
    "dimension",
    "raw_tag",
    "original_display_tag",
    "preview_display_tag",
    "support",
    "diff_case",
]

ONE_WORD = re.compile(r"^[a-z][a-z0-9]*$")
FORBIDDEN_DISPLAY_TAGS = {"other", "others"}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def valid_display_tag(tag: str) -> bool:
    normalized = str(tag or "").strip()
    return bool(ONE_WORD.fullmatch(normalized)) and normalized not in FORBIDDEN_DISPLAY_TAGS


def strong_review(row: dict[str, str]) -> bool:
    return (
        row.get("review_label") == "promote"
        and row.get("review_source") in {"consensus", "adjudicated"}
        and row.get("label_state") == "final"
        and as_bool(row.get("candidate_valid"))
    )


def select_candidate(
    display_rows: list[dict[str, str]],
    source: str,
    used: set[tuple[str, str]],
) -> dict[str, str]:
    for row in display_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        candidate = row.get("candidate_display_tag", "")
        if (
            row.get("candidate_source") == source
            and candidate
            and candidate != row.get("active_display_tag")
            and key not in used
        ):
            used.add(key)
            return row
    raise AssertionError(f"no R209 candidate row found for {source}")


def fixture_row(
    *,
    case: str,
    source: dict[str, str],
    to_display_tag: str | None = None,
    review_label: str = "promote",
    review_source: str = "consensus",
    label_state: str = "final",
    candidate_valid: bool = True,
    expected_result: str = "accepted",
    reason: str,
) -> dict[str, Any]:
    return {
        "case": case,
        "dimension": source.get("dimension", ""),
        "raw_tag": source.get("raw_tag", ""),
        "from_display_tag": source.get("active_display_tag", ""),
        "to_display_tag": to_display_tag if to_display_tag is not None else source.get("candidate_display_tag", ""),
        "review_label": review_label,
        "review_source": review_source,
        "label_state": label_state,
        "candidate_valid": candidate_valid,
        "expected_result": expected_result,
        "reason": reason,
    }


def build_review_fixtures(display_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    used: set[tuple[str, str]] = set()
    profile_accept = select_candidate(display_rows, "r189_profile_guarded_merge_candidate", used)
    regen_accept = select_candidate(display_rows, "r202_llama_candidate", used)
    profile_unclear = select_candidate(display_rows, "r189_profile_guarded_merge_candidate", used)
    regen_weak = select_candidate(display_rows, "r202_llama_candidate", used)
    profile_other = select_candidate(display_rows, "r189_profile_guarded_merge_candidate", used)
    missing_source = {
        "dimension": "prompt",
        "raw_tag": "__missing_raw_tag__",
        "active_display_tag": "__missing_raw_tag__",
        "candidate_display_tag": "review",
    }
    return [
        fixture_row(
            case="accept_reviewed_profile_merge",
            source=profile_accept,
            reason="final consensus promote row for an existing profile-merge candidate",
        ),
        fixture_row(
            case="accept_reviewed_llm_regeneration",
            source=regen_accept,
            review_source="adjudicated",
            reason="final adjudicated promote row for an LLM-regenerated candidate",
        ),
        fixture_row(
            case="reject_unclear_profile_merge",
            source=profile_unclear,
            review_label="unclear",
            expected_result="rejected",
            reason="unclear rows remain pending",
        ),
        fixture_row(
            case="reject_single_label_regeneration",
            source=regen_weak,
            review_source="single_label",
            label_state="weak_final",
            expected_result="rejected",
            reason="single-label review is insufficient for default display promotion",
        ),
        fixture_row(
            case="reject_hidden_other_bucket",
            source=profile_other,
            to_display_tag="other",
            expected_result="rejected",
            reason="display updates cannot create hidden other buckets",
        ),
        fixture_row(
            case="reject_missing_source_row",
            source=missing_source,
            expected_result="rejected",
            reason="review rows must reference an existing R209 raw tag row",
        ),
    ]


def reviewed_display_diff_rows(
    display_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key = {
        (row.get("dimension", ""), row.get("raw_tag", "")): row
        for row in display_rows
    }
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in review_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        source = by_key.get(key)
        reject_reason = ""
        if source is None:
            reject_reason = "missing_source_row"
        elif row.get("from_display_tag") != source.get("active_display_tag"):
            reject_reason = "stale_from_display_tag"
        elif not strong_review(row):
            reject_reason = "review_not_final_consensus_or_adjudicated_promote"
        elif not valid_display_tag(row.get("to_display_tag", "")):
            reject_reason = "invalid_or_forbidden_display_tag"
        elif row.get("to_display_tag") == source.get("active_display_tag"):
            reject_reason = "noop_display_tag"

        if reject_reason:
            rejected.append({**row, "reject_reason": reject_reason})
            continue

        accepted.append(
            {
                "case": row.get("case", ""),
                "dimension": row.get("dimension", ""),
                "raw_tag": row.get("raw_tag", ""),
                "from_display_tag": source.get("active_display_tag", ""),
                "to_display_tag": row.get("to_display_tag", ""),
                "support": as_int(source.get("support")),
                "diff_source": "r218_reviewed_display_map_diff_preview",
                "review_source": row.get("review_source", ""),
                "reason": row.get("reason", ""),
            }
        )
    return accepted, rejected


def preview_rows(
    display_rows: list[dict[str, str]],
    diff_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key = {
        (row["dimension"], row["raw_tag"]): row
        for row in diff_rows
    }
    rows: list[dict[str, Any]] = []
    for source in display_rows:
        key = (source.get("dimension", ""), source.get("raw_tag", ""))
        diff = by_key.get(key)
        rows.append(
            {
                "dimension": source.get("dimension", ""),
                "raw_tag": source.get("raw_tag", ""),
                "original_display_tag": source.get("active_display_tag", ""),
                "preview_display_tag": diff["to_display_tag"] if diff else source.get("active_display_tag", ""),
                "support": as_int(source.get("support")),
                "diff_case": diff["case"] if diff else "",
            }
        )
    return rows


def summarize(
    display_rows: list[dict[str, str]],
    fixture_rows: list[dict[str, Any]],
    diff_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    preview: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_accepts = sum(1 for row in fixture_rows if row.get("expected_result") == "accepted")
    expected_rejects = sum(1 for row in fixture_rows if row.get("expected_result") == "rejected")
    raw_keys = {(row.get("dimension", ""), row.get("raw_tag", "")) for row in display_rows}
    preview_keys = {(row.get("dimension", ""), row.get("raw_tag", "")) for row in preview}
    original_total = sum(as_int(row.get("support")) for row in display_rows)
    preview_total = sum(as_int(row.get("support")) for row in preview)
    hidden_other_rows = sum(
        1 for row in preview if str(row.get("preview_display_tag", "")).lower() in FORBIDDEN_DISPLAY_TAGS
    )
    return {
        "fixture_rows": len(fixture_rows),
        "expected_accepts": expected_accepts,
        "expected_rejects": expected_rejects,
        "accepted_diff_rows": len(diff_rows),
        "rejected_rows": len(rejected_rows),
        "profile_merge_accepts": sum(
            1 for row in diff_rows if row.get("case") == "accept_reviewed_profile_merge"
        ),
        "llm_regeneration_accepts": sum(
            1 for row in diff_rows if row.get("case") == "accept_reviewed_llm_regeneration"
        ),
        "original_display_rows": len(display_rows),
        "preview_rows": len(preview),
        "original_total_support": original_total,
        "preview_total_support": preview_total,
        "support_preserved": original_total == preview_total,
        "raw_key_coverage_preserved": raw_keys == preview_keys,
        "preview_changed_rows": sum(
            1 for row in preview if row.get("original_display_tag") != row.get("preview_display_tag")
        ),
        "hidden_other_rows": hidden_other_rows,
        "canonical_map_updated": False,
        "raw_tags_preserved": True,
        "expected_results_matched": expected_accepts == len(diff_rows) and expected_rejects == len(rejected_rows),
    }


def claim_gate(summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "reviewed_display_map_update_gate_supported": bool(
            summary["expected_results_matched"]
            and summary["accepted_diff_rows"] == 2
            and summary["rejected_rows"] == 4
            and summary["support_preserved"]
            and summary["raw_key_coverage_preserved"]
            and summary["hidden_other_rows"] == 0
        ),
        "profile_merge_promotion_previewed": summary["profile_merge_accepts"] == 1,
        "llm_regeneration_promotion_previewed": summary["llm_regeneration_accepts"] == 1,
        "unsafe_promotions_rejected": summary["rejected_rows"] == 4,
        "raw_tags_preserved": bool(summary["raw_tags_preserved"]),
        "support_preserved": bool(summary["support_preserved"]),
        "reads_generated_artifacts_only": True,
        "synthetic_review_fixtures_only": True,
        "raw_trace_read": False,
        "llm_called": False,
        "canonical_map_updated": False,
        "semantic_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "long_tail_promotion_quality_supported": False,
        "developer_utility_supported": False,
        "community_adoption_supported": False,
    }


def write_markdown(path: Path, payload: dict[str, Any], diff_rows: list[dict[str, Any]], rejected_rows: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R218 Display-Map Update Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Reads generated R209 display-map artifacts only.",
        "- Uses synthetic review fixtures over real R209 candidate rows.",
        "- Previews a reviewed display-map diff but does not update the canonical map.",
        "- Rejects unclear, weak, hidden-`other`, and missing-source promotion rows.",
        "- Does not prove merge quality, regenerated-label quality, semantic adequacy, developer utility, or community adoption.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "|---|---:|",
        f"| fixture rows | {summary['fixture_rows']} |",
        f"| accepted diff rows | {summary['accepted_diff_rows']} |",
        f"| rejected rows | {summary['rejected_rows']} |",
        f"| preview changed rows | {summary['preview_changed_rows']} |",
        f"| support preserved | {summary['support_preserved']} |",
        f"| raw key coverage preserved | {summary['raw_key_coverage_preserved']} |",
        f"| hidden other rows | {summary['hidden_other_rows']} |",
        "",
        "## Accepted Preview Diff",
        "",
        "| case | dimension | raw tag | from | to | support |",
        "|---|---|---|---|---|---:|",
    ]
    for row in diff_rows:
        lines.append(
            f"| {row['case']} | {row['dimension']} | `{row['raw_tag']}` | "
            f"`{row['from_display_tag']}` | `{row['to_display_tag']}` | {row['support']} |"
        )
    lines.extend(
        [
            "",
            "## Rejected Rows",
            "",
            "| case | reason |",
            "|---|---|",
        ]
    )
    for row in rejected_rows:
        lines.append(f"| {row['case']} | {row['reject_reason']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R218 supports a reviewed display-map update gate: active display membership "
            "can change only in a preview diff when promotion rows are final and "
            "reviewed, while unsafe rows remain pending. It does not support any "
            "claim that the accepted fixture labels are semantically correct.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    r209_json = args.r209_dir / "reversible-display-map-r209.json"
    display_csv = args.r209_dir / "active-display-map-r209.csv"
    drilldown_csv = args.r209_dir / "display-drilldown-r209.csv"
    for path in [r209_json, display_csv, drilldown_csv]:
        if not path.exists():
            raise FileNotFoundError(f"missing R218 input artifact: {rel(path)}")

    r209 = read_json(r209_json)
    display_rows = read_csv(display_csv)
    fixture_rows = build_review_fixtures(display_rows)
    diff_rows, rejected_rows = reviewed_display_diff_rows(
        display_rows,
        [{key: str(value) for key, value in row.items()} for row in fixture_rows],
    )
    preview = preview_rows(display_rows, diff_rows)
    summary = summarize(display_rows, fixture_rows, diff_rows, rejected_rows, preview)
    payload = {
        "run_id": "R218",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "display_map_update_gate_ready_synthetic_review_only",
        "claim": "C3 versioned display-map update mechanism; C6 protocol/gate only",
        "claim_boundary": (
            "R218 tests the reviewed display-map update gate over generated R209 rows. "
            "It uses synthetic review fixtures and therefore supports mechanism behavior "
            "only, not merge quality, regenerated-label quality, semantic adequacy, "
            "developer utility, or community adoption."
        ),
        "input": {
            "r209_json": rel(r209_json),
            "r209_json_sha256": sha256_file(r209_json),
            "display_csv": rel(display_csv),
            "display_csv_sha256": sha256_file(display_csv),
            "drilldown_csv": rel(drilldown_csv),
            "drilldown_csv_sha256": sha256_file(drilldown_csv),
        },
        "method": {
            "review_source": "synthetic fixtures selected from real R209 pending candidate rows",
            "accept_policy": "promote + final + consensus/adjudicated + valid lowercase ASCII display tag + source row exists",
            "reject_policy": "unclear, weak/single-label, invalid/other, missing-source, stale, or no-op rows remain pending",
            "preview_policy": "write a diff and preview rows only; do not update canonical map or raw tags",
            "r209_status": r209.get("status"),
        },
        "summary": summary,
        "claim_gate": claim_gate(summary),
        "outputs": {
            "summary_json": rel(args.out_dir / "display-map-update-gate-r218.json"),
            "summary_md": rel(args.out_dir / "display-map-update-gate-r218.md"),
            "review_fixture_csv": rel(args.out_dir / "review-fixture-r218.csv"),
            "accepted_diff_csv": rel(args.out_dir / "accepted-display-map-diff-r218.csv"),
            "rejected_rows_csv": rel(args.out_dir / "rejected-display-map-updates-r218.csv"),
            "preview_rows_csv": rel(args.out_dir / "preview-display-map-r218.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, fixture_rows, diff_rows, rejected_rows, preview


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, fixture_rows, diff_rows, rejected_rows, preview = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "display-map-update-gate-r218.json", payload)
    write_markdown(args.out_dir / "display-map-update-gate-r218.md", payload, diff_rows, rejected_rows)
    write_csv(args.out_dir / "review-fixture-r218.csv", fixture_rows, FIXTURE_FIELDS)
    write_csv(args.out_dir / "accepted-display-map-diff-r218.csv", diff_rows, DIFF_FIELDS)
    write_csv(args.out_dir / "rejected-display-map-updates-r218.csv", rejected_rows, REJECT_FIELDS)
    write_csv(args.out_dir / "preview-display-map-r218.csv", preview, PREVIEW_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}, sort_keys=True))


if __name__ == "__main__":
    main()
