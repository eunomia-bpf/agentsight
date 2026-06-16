#!/usr/bin/env python3
"""R209: materialize a reversible display map for long-tail compaction.

R189/R196/R202/R203/R205 establish the mechanism pieces: existing canonical
aliases, governance actions, optional llama.cpp regeneration candidates, human
promotion gates, and compaction metrics. R209 makes that mechanism directly
consumable by a UI or paper figure without changing the canonical map.

The active display map only applies deterministic R189 alias rows via R196.
Profile-guarded R189 merges and regenerated tags remain candidates unless a
future reviewed diff promotes them. Raw tags stay visible through the drilldown
index.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R196_DIR = SCRIPT_DIR / "out" / "long-tail-governance-r196"
DEFAULT_R203_DIR = SCRIPT_DIR / "out" / "long-tail-promotion-r203"
DEFAULT_R205_DIR = SCRIPT_DIR / "out" / "long-tail-compaction-r205"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"

DISPLAY_MAP_FIELDS = [
    "dimension",
    "raw_tag",
    "active_display_tag",
    "active_source",
    "canonical_tag",
    "governance_action",
    "governance_reasons",
    "requires_review",
    "is_long_tail",
    "support",
    "candidate_display_tag",
    "candidate_source",
    "candidate_state",
    "promotion_label",
    "promotion_final_source",
    "label_state",
    "raw_drilldown_required",
    "map_update_allowed",
]

DRILLDOWN_FIELDS = [
    "dimension",
    "active_display_tag",
    "raw_tag_count",
    "support",
    "raw_support_pct",
    "review_required_rows",
    "review_required_support",
    "review_required_support_pct",
    "long_tail_rows",
    "long_tail_support",
    "candidate_rows",
    "active_merge_rows",
    "raw_tags",
    "governance_actions",
    "top_processes",
    "top_effects",
    "top_paths",
    "top_context_tags",
]

DIFF_FIELDS = [
    "dimension",
    "raw_tag",
    "from_display_tag",
    "to_display_tag",
    "diff_source",
    "promotion_label",
    "promotion_final_source",
    "label_state",
    "support",
    "reason",
]


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
    return int(float(value))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def compact_counter(counter: Counter[str], limit: int | None = 8) -> str:
    items = counter.most_common(limit) if limit is not None else counter.most_common()
    return "; ".join(f"{key}={value}" for key, value in items)


def parse_profile_counter(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in str(text or "").split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, value = item.rsplit("=", 1)
        key = key.strip()
        try:
            count = int(float(value.strip()))
        except ValueError:
            continue
        if key:
            counter[key] += count
    return counter


def promotion_by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row.get("dimension", ""), row.get("raw_tag", "")): row for row in rows}


def is_accepted_alias_overlay(row: dict[str, str]) -> bool:
    return (
        row.get("governance_action") == "auto_canonicalize_existing"
        and row.get("governance_reasons") == "r189_alias"
    )


def is_unreviewed_canonical_candidate(row: dict[str, str]) -> bool:
    return (
        row.get("governance_action") == "auto_canonicalize_existing"
        and row.get("governance_reasons") != "r189_alias"
        and (row.get("canonical_tag") or row.get("raw_tag", "")) != row.get("raw_tag", "")
    )


def active_source_for(row: dict[str, str], active_tag: str) -> str:
    if is_accepted_alias_overlay(row) and active_tag != row.get("raw_tag"):
        return "r189_alias_overlay"
    return "raw_preserved"


def display_map_row(
    governance_row: dict[str, str],
    promotion_row: dict[str, str] | None = None,
) -> dict[str, Any]:
    raw_tag = governance_row.get("raw_tag", "")
    canonical_tag = governance_row.get("canonical_tag", "") or raw_tag
    action = governance_row.get("governance_action", "")
    active_tag = canonical_tag if is_accepted_alias_overlay(governance_row) else raw_tag

    regenerated = ""
    candidate_source = ""
    candidate_state = "none"
    promotion_label = ""
    promotion_final_source = ""
    label_state = ""
    if is_unreviewed_canonical_candidate(governance_row):
        regenerated = canonical_tag
        candidate_source = "r189_profile_guarded_merge_candidate"
        candidate_state = "pending_merge_review"
    if promotion_row:
        regenerated_candidate = promotion_row.get("regenerated_tag", "")
        promotion_label = promotion_row.get("final_label") or promotion_row.get("promotion_label", "")
        promotion_final_source = promotion_row.get("final_source", "")
        label_state = promotion_row.get("label_state", "")
        if regenerated_candidate and as_bool(promotion_row.get("grammar_valid")):
            regenerated = regenerated_candidate
            candidate_source = "r202_llama_candidate"
            candidate_state = "pending_review"
            if promotion_label:
                candidate_state = f"reviewed_{promotion_label}"
                if promotion_final_source:
                    candidate_state = f"{candidate_state}:{promotion_final_source}"
            if label_state:
                if not promotion_final_source:
                    candidate_state = f"{candidate_state}:{label_state}"
                elif label_state not in {"final", ""}:
                    candidate_state = f"{candidate_state}:{label_state}"

    return {
        "dimension": governance_row.get("dimension", ""),
        "raw_tag": raw_tag,
        "active_display_tag": active_tag,
        "active_source": active_source_for(governance_row, active_tag),
        "canonical_tag": canonical_tag,
        "governance_action": action,
        "governance_reasons": governance_row.get("governance_reasons", ""),
        "requires_review": as_bool(governance_row.get("requires_review")),
        "is_long_tail": as_bool(governance_row.get("is_long_tail")),
        "support": as_int(governance_row.get("support")),
        "candidate_display_tag": regenerated,
        "candidate_source": candidate_source,
        "candidate_state": candidate_state,
        "promotion_label": promotion_label,
        "promotion_final_source": promotion_final_source,
        "label_state": label_state,
        "raw_drilldown_required": True,
        "map_update_allowed": False,
    }


def build_display_map(
    governance_rows: list[dict[str, str]],
    promotion_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    promotions = promotion_by_key(promotion_rows)
    rows = [
        display_map_row(row, promotions.get((row.get("dimension", ""), row.get("raw_tag", ""))))
        for row in governance_rows
    ]
    rows.sort(key=lambda row: (row["dimension"], row["active_display_tag"], row["raw_tag"]))
    return rows


def build_reviewed_diff(display_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diff_rows: list[dict[str, Any]] = []
    for row in display_rows:
        label = str(row.get("promotion_label") or "")
        candidate = str(row.get("candidate_display_tag") or "")
        final_source = str(row.get("promotion_final_source") or "")
        label_state = str(row.get("label_state") or "")
        strong_review = final_source in {"consensus", "adjudicated"} and label_state == "final"
        if label != "promote" or not strong_review or not candidate or candidate == row.get("active_display_tag"):
            continue
        diff_rows.append(
            {
                "dimension": row["dimension"],
                "raw_tag": row["raw_tag"],
                "from_display_tag": row["active_display_tag"],
                "to_display_tag": candidate,
                "diff_source": "r203_reviewed_promotion",
                "promotion_label": label,
                "promotion_final_source": final_source,
                "label_state": label_state,
                "support": row.get("support", 0),
                "reason": "reviewed regenerated candidate; raw tag remains drilldown-visible",
            }
        )
    return diff_rows


def build_drilldown_rows(
    governance_rows: list[dict[str, str]],
    display_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    governance_by_key = {
        (row.get("dimension", ""), row.get("raw_tag", "")): row
        for row in governance_rows
    }
    total_support = sum(as_int(row.get("support")) for row in display_rows)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in display_rows:
        groups[(row["dimension"], row["active_display_tag"])].append(row)

    out: list[dict[str, Any]] = []
    for (dimension, display_tag), rows in sorted(groups.items()):
        support = sum(as_int(row.get("support")) for row in rows)
        review_support = sum(as_int(row.get("support")) for row in rows if as_bool(row.get("requires_review")))
        long_tail_support = sum(as_int(row.get("support")) for row in rows if as_bool(row.get("is_long_tail")))
        action_counts = Counter(str(row.get("governance_action") or "unknown") for row in rows)
        raw_support = Counter({str(row["raw_tag"]): as_int(row.get("support")) for row in rows})
        process_counts: Counter[str] = Counter()
        effect_counts: Counter[str] = Counter()
        path_counts: Counter[str] = Counter()
        context_counts: Counter[str] = Counter()
        for row in rows:
            source = governance_by_key.get((row["dimension"], row["raw_tag"]), {})
            process_counts.update(parse_profile_counter(source.get("top_processes", "")))
            effect_counts.update(parse_profile_counter(source.get("top_effects", "")))
            path_counts.update(parse_profile_counter(source.get("top_paths", "")))
            context_counts.update(parse_profile_counter(source.get("top_context_tags", "")))
        out.append(
            {
                "dimension": dimension,
                "active_display_tag": display_tag,
                "raw_tag_count": len(rows),
                "support": support,
                "raw_support_pct": pct(support, total_support),
                "review_required_rows": sum(1 for row in rows if as_bool(row.get("requires_review"))),
                "review_required_support": review_support,
                "review_required_support_pct": pct(review_support, support),
                "long_tail_rows": sum(1 for row in rows if as_bool(row.get("is_long_tail"))),
                "long_tail_support": long_tail_support,
                "candidate_rows": sum(1 for row in rows if row.get("candidate_display_tag")),
                "active_merge_rows": sum(1 for row in rows if row.get("raw_tag") != row.get("active_display_tag")),
                "raw_tags": compact_counter(raw_support, limit=None),
                "governance_actions": compact_counter(action_counts),
                "top_processes": compact_counter(process_counts),
                "top_effects": compact_counter(effect_counts),
                "top_paths": compact_counter(path_counts),
                "top_context_tags": compact_counter(context_counts),
            }
        )
    out.sort(key=lambda row: (-as_int(row["support"]), row["dimension"], row["active_display_tag"]))
    return out


def summarize(
    governance_rows: list[dict[str, str]],
    display_rows: list[dict[str, Any]],
    drilldown_rows: list[dict[str, Any]],
    diff_rows: list[dict[str, Any]],
    r203_payload: dict[str, Any],
    r205_payload: dict[str, Any],
) -> dict[str, Any]:
    total_support = sum(as_int(row.get("support")) for row in display_rows)
    raw_keys = {(row.get("dimension", ""), row.get("raw_tag", "")) for row in governance_rows}
    display_keys = {(row.get("dimension", ""), row.get("raw_tag", "")) for row in display_rows}
    no_other_rows = [
        row for row in display_rows if str(row.get("active_display_tag") or "").lower() in {"other", "others"}
    ]
    candidate_rows = [row for row in display_rows if row.get("candidate_display_tag")]
    pending_merge_rows = [
        row for row in display_rows if row.get("candidate_source") == "r189_profile_guarded_merge_candidate"
    ]
    regenerated_rows = [row for row in display_rows if row.get("candidate_source") == "r202_llama_candidate"]
    review_rows = [row for row in display_rows if as_bool(row.get("requires_review"))]
    active_merge_rows = [row for row in display_rows if row.get("raw_tag") != row.get("active_display_tag")]
    return {
        "raw_tag_rows": len(governance_rows),
        "display_map_rows": len(display_rows),
        "drilldown_rows": len(drilldown_rows),
        "reviewed_diff_rows": len(diff_rows),
        "total_support": total_support,
        "raw_unique_labels": len({row.get("raw_tag", "") for row in display_rows if row.get("raw_tag")}),
        "active_display_unique_labels": len(
            {row.get("active_display_tag", "") for row in display_rows if row.get("active_display_tag")}
        ),
        "active_merge_rows": len(active_merge_rows),
        "candidate_rows": len(candidate_rows),
        "pending_merge_candidate_rows": len(pending_merge_rows),
        "regenerated_candidate_rows": len(regenerated_rows),
        "alias_active_rows": sum(1 for row in display_rows if row.get("active_source") == "r189_alias_overlay"),
        "candidate_reviewed_promote_rows": len(diff_rows),
        "review_required_rows": len(review_rows),
        "review_required_support": sum(as_int(row.get("support")) for row in review_rows),
        "review_required_support_pct": pct(sum(as_int(row.get("support")) for row in review_rows), total_support),
        "long_tail_rows": sum(1 for row in display_rows if as_bool(row.get("is_long_tail"))),
        "long_tail_support": sum(as_int(row.get("support")) for row in display_rows if as_bool(row.get("is_long_tail"))),
        "long_tail_support_pct": pct(
            sum(as_int(row.get("support")) for row in display_rows if as_bool(row.get("is_long_tail"))),
            total_support,
        ),
        "raw_coverage_complete": raw_keys == display_keys,
        "missing_raw_keys": sorted(raw_keys - display_keys)[:10],
        "extra_display_keys": sorted(display_keys - raw_keys)[:10],
        "no_hidden_other_bucket": not no_other_rows,
        "hidden_other_rows": len(no_other_rows),
        "drilldown_support_preserved": sum(as_int(row.get("support")) for row in drilldown_rows) == total_support,
        "drilldown_raw_tags_complete": all(
            sum(parse_profile_counter(row.get("raw_tags", "")).values()) == as_int(row.get("support"))
            and len(parse_profile_counter(row.get("raw_tags", ""))) == as_int(row.get("raw_tag_count"))
            for row in drilldown_rows
        ),
        "r203_status": r203_payload.get("status"),
        "r203_final_labels": (r203_payload.get("summary") or {}).get("final_label_count"),
        "r205_status": r205_payload.get("status"),
    }


def write_markdown(path: Path, payload: dict[str, Any], drilldown_rows: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R209 Reversible Display Map",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R196/R203/R205 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not update the canonical map.",
        "- Active display tags apply only deterministic R189 alias overlays.",
        "- R189 lexical/profile merges and regenerated tags remain candidate labels unless a future reviewed diff promotes them.",
        "- The drilldown CSV stores the complete raw-tag membership for each display bucket.",
        "",
        "## Reversibility Checks",
        "",
        "| check | value |",
        "|---|---:|",
        f"| raw tag rows | {summary['raw_tag_rows']} |",
        f"| display map rows | {summary['display_map_rows']} |",
        f"| active display labels | {summary['active_display_unique_labels']} |",
        f"| active merge rows | {summary['active_merge_rows']} |",
        f"| candidate rows | {summary['candidate_rows']} |",
        f"| pending merge candidate rows | {summary['pending_merge_candidate_rows']} |",
        f"| regenerated candidate rows | {summary['regenerated_candidate_rows']} |",
        f"| alias active rows | {summary['alias_active_rows']} |",
        f"| reviewed diff rows | {summary['reviewed_diff_rows']} |",
        f"| raw coverage complete | {summary['raw_coverage_complete']} |",
        f"| drilldown support preserved | {summary['drilldown_support_preserved']} |",
        f"| drilldown raw tags complete | {summary['drilldown_raw_tags_complete']} |",
        f"| hidden `other` rows | {summary['hidden_other_rows']} |",
        f"| review-required support pct | {summary['review_required_support_pct']} |",
        "",
        "## Top Display Buckets",
        "",
        "| dimension | display tag | support | raw tags | review support pct | top processes/effects |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in drilldown_rows[:25]:
        profile = row.get("top_processes") or row.get("top_effects") or row.get("top_context_tags")
        lines.append(
            f"| {row['dimension']} | `{row['active_display_tag']}` | {row['support']} | "
            f"{row['raw_tag_count']} | {row['review_required_support_pct']} | {profile} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R209 supports a concrete UI/data contract for reversible compaction: every "
            "raw tag has one active display row and every display bucket has a raw-tag "
            "drilldown. It does not prove tag adequacy, merge quality, regenerated-tag "
            "quality, or developer utility. Those claims still require R124/R190/R203 "
            "human labels and R142/R151 developer-task results.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    r196_csv = args.r196_dir / "long-tail-governance-r196.csv"
    r196_json = args.r196_dir / "long-tail-governance-r196.json"
    r203_results = args.r203_dir / "long-tail-promotion-results-r203.csv"
    r203_json = args.r203_dir / "long-tail-promotion-r203.json"
    r205_json = args.r205_dir / "long-tail-compaction-r205.json"
    for path in [r196_csv, r196_json, r203_results, r203_json, r205_json]:
        if not path.exists():
            raise FileNotFoundError(f"missing R209 input artifact: {rel(path)}")

    governance_rows = read_csv(r196_csv)
    promotion_rows = read_csv(r203_results)
    r203_payload = read_json(r203_json)
    r205_payload = read_json(r205_json)
    display_rows = build_display_map(governance_rows, promotion_rows)
    diff_rows = build_reviewed_diff(display_rows)
    drilldown_rows = build_drilldown_rows(governance_rows, display_rows)
    summary = summarize(governance_rows, display_rows, drilldown_rows, diff_rows, r203_payload, r205_payload)

    status = "reversible_display_map_ready_no_map_update"
    if diff_rows:
        status = "reviewed_display_map_diff_ready_no_map_update"

    payload = {
        "run_id": "R209",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3 mechanism; C6 protocol/gate only",
        "claim_boundary": (
            "R209 materializes a reversible display-map contract over existing generated artifacts. "
            "It preserves raw tags, avoids hidden other buckets, and keeps regenerated tags as candidates. "
            "It does not update the canonical map or support tag adequacy, merge quality, promotion "
            "quality, developer utility, or community adoption without human evidence."
        ),
        "input": {
            "r196_csv": rel(r196_csv),
            "r196_csv_sha256": sha256_file(r196_csv),
            "r196_json": rel(r196_json),
            "r196_json_sha256": sha256_file(r196_json),
            "r203_results": rel(r203_results),
            "r203_results_sha256": sha256_file(r203_results),
            "r203_json": rel(r203_json),
            "r203_json_sha256": sha256_file(r203_json),
            "r205_json": rel(r205_json),
            "r205_json_sha256": sha256_file(r205_json),
        },
        "method": {
            "active_map_rule": "only deterministic R189 alias rows use canonical_tag; R189 lexical/profile rows stay raw-active",
            "candidate_rule": "R189 lexical/profile canonical tags and R203/R202 regenerated tags are exposed as candidate_display_tag but are not active",
            "diff_rule": "future promote labels produce reviewed diff rows only with final consensus/adjudicated R203 evidence; this script still does not update the canonical map",
            "drilldown_rule": "display-drilldown rows include complete raw_tags membership; profile columns are top-k summaries",
            "raw_trace_policy": "read generated artifacts only; do not mutate raw traces",
            "no_other_policy": "other/others is not an active display tag; tail rows remain raw-drilldown-visible",
        },
        "summary": summary,
        "claim_gate": {
            "reversible_display_map_supported": bool(
                summary["raw_coverage_complete"]
                and summary["drilldown_support_preserved"]
                and summary["drilldown_raw_tags_complete"]
                and summary["no_hidden_other_bucket"]
            ),
            "raw_tags_preserved": True,
            "canonical_overlay_only": True,
            "active_alias_overlay_only": True,
            "no_hidden_other_bucket": bool(summary["no_hidden_other_bucket"]),
            "drilldown_available": bool(drilldown_rows),
            "drilldown_raw_tags_complete": bool(summary["drilldown_raw_tags_complete"]),
            "canonical_map_updated": False,
            "regenerated_tags_active_without_review": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "semantic_adequacy_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
            "requires_r124_labels_for_adequacy": True,
            "requires_r190_labels_for_merge_quality": True,
            "requires_r203_labels_for_promotion_quality": True,
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, display_rows, drilldown_rows, diff_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r196-dir", type=Path, default=DEFAULT_R196_DIR)
    parser.add_argument("--r203-dir", type=Path, default=DEFAULT_R203_DIR)
    parser.add_argument("--r205-dir", type=Path, default=DEFAULT_R205_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, display_rows, drilldown_rows, diff_rows = build_payload(args)
    out_dir = args.out_dir
    summary_json = out_dir / "reversible-display-map-r209.json"
    summary_md = out_dir / "reversible-display-map-r209.md"
    display_map_csv = out_dir / "active-display-map-r209.csv"
    drilldown_csv = out_dir / "display-drilldown-r209.csv"
    diff_csv = out_dir / "reviewed-display-map-diff-r209.csv"
    payload["outputs"] = {
        "summary_json": rel(summary_json),
        "summary_md": rel(summary_md),
        "active_display_map_csv": rel(display_map_csv),
        "display_drilldown_csv": rel(drilldown_csv),
        "reviewed_display_map_diff_csv": rel(diff_csv),
    }
    write_json(summary_json, payload)
    write_markdown(summary_md, payload, drilldown_rows)
    write_csv(display_map_csv, display_rows, DISPLAY_MAP_FIELDS)
    write_csv(drilldown_csv, drilldown_rows, DRILLDOWN_FIELDS)
    write_csv(diff_csv, diff_rows, DIFF_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": rel(summary_json)}, sort_keys=True))


if __name__ == "__main__":
    main()
