#!/usr/bin/env python3
"""R222: retrospective prompt-bias audit over existing tag artifacts.

This script does not call an LLM. It compares the current Rust AgentFlame
prefer-list prompt against older no-prefer Python artifacts where possible, then
reports why the old data is not a same-fragment ablation. It also summarizes
R180/R122 tag concentration signals that motivate a real no-prefer ablation.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "prompt-bias-retrospective-r222"
DEFAULT_VIS_OUT = SCRIPT_DIR / "out"
DEFAULT_R170_REPORT = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "agentflame.json"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


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


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(str(value))


def dist_stats_from_counter(counts: Counter[str], unit: str) -> dict[str, Any]:
    total = sum(counts.values())
    entropy = -sum((count / total) * math.log(count / total) for count in counts.values()) if total else 0.0
    top = counts.most_common(12)
    head_words = ["refactor", "review", "debug", "test", "design", "analyze", "docs", "localization", "localized"]
    return {
        "unit": unit,
        "total": total,
        "unique_tags": len(counts),
        "effective_tags": round(math.exp(entropy), 3) if total else 0.0,
        "top1_tag": top[0][0] if top else "",
        "top1_count": top[0][1] if top else 0,
        "top1_share_pct": round(100.0 * top[0][1] / total, 3) if total and top else 0.0,
        "top2_share_pct": round(100.0 * sum(count for _, count in top[:2]) / total, 3) if total else 0.0,
        "top5_share_pct": round(100.0 * sum(count for _, count in top[:5]) / total, 3) if total else 0.0,
        "refactor_share_pct": round(100.0 * counts["refactor"] / total, 3) if total else 0.0,
        "review_refactor_share_pct": round(
            100.0 * (counts["review"] + counts["refactor"]) / total, 3
        )
        if total
        else 0.0,
        "watched_word_counts": "; ".join(f"{word}={counts[word]}" for word in head_words if counts[word]),
        "top_tags": "; ".join(f"{tag}={count}" for tag, count in top),
    }


def dist_stats(values: list[str], unit: str) -> dict[str, Any]:
    return dist_stats_from_counter(Counter(values), unit)


def prompt_has_prefer_list(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return bool(re.search(r"Prefer common words such as", text))


def legacy_prompt_has_prefer_list(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return bool(re.search(r"Prefer common words such as|Prefer words like", text))


def r170_dimension_stats(tag_counts: list[dict[str, str]], dimension: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    unit = ""
    for row in tag_counts:
        if row.get("dimension") != dimension:
            continue
        unit = row.get("unit", unit)
        counts[row.get("tag", "")] += int(float(row.get("count", "0")))
    stats = dist_stats_from_counter(counts, unit or dimension)
    stats["source"] = "r170_tag_counts"
    stats["dimension"] = dimension
    return stats


def r180_model_stats(r180: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in r180.get("bench", {}).get("models", []):
        tags: list[str] = []
        for fragment in model.get("fragments", []):
            tags.extend(str(tag) for tag in fragment.get("tags", []) if tag)
        stats = dist_stats(tags, "tag_runs")
        stats["source"] = "r180_model_runs"
        stats["dimension"] = "all_fragments"
        stats["model"] = model.get("label", "")
        stability = model.get("stability", {})
        stats["exact_stability_pct"] = stability.get("exact_stability_pct", "")
        stats["valid_run_pct"] = stability.get("valid_run_pct", "")
        rows.append(stats)
    return rows


def r122_stats(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for kind in ["all", "session", "prompt", "llm"]:
        selected = rows if kind == "all" else [row for row in rows if row.get("kind") == kind]
        stats = dist_stats([row.get("candidate_tag", "") for row in selected], "fragments")
        stats["source"] = "r122_candidate_modal_tags"
        stats["dimension"] = kind
        stats["model"] = "3b_modal_candidate"
        out.append(stats)
    return out


def old_new_hash_join(old_prompt_rows: list[dict[str, str]], r170_report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    old_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    new_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in old_prompt_rows:
        old_by_hash[row.get("prompt_hash", "")].append(row)
    for row in r170_report.get("prompt_tags", []):
        new_by_hash[row.get("prompt_hash", "")].append(row)
    shared = sorted(set(old_by_hash) & set(new_by_hash))
    rows: list[dict[str, Any]] = []
    for prompt_hash in shared:
        old_tags = Counter(row.get("prompt_tag", "") for row in old_by_hash[prompt_hash])
        new_tags = Counter(row.get("prompt_tag", "") for row in new_by_hash[prompt_hash])
        rows.append(
            {
                "prompt_hash": prompt_hash,
                "old_tag": old_tags.most_common(1)[0][0] if old_tags else "",
                "new_tag": new_tags.most_common(1)[0][0] if new_tags else "",
                "old_count": sum(old_tags.values()),
                "new_count": sum(new_tags.values()),
                "same_tag": old_tags.most_common(1)[0][0] == new_tags.most_common(1)[0][0]
                if old_tags and new_tags
                else False,
            }
        )
    summary = {
        "old_prompt_rows": len(old_prompt_rows),
        "old_unique_prompt_hashes": len(old_by_hash),
        "r170_prompt_rows": len(r170_report.get("prompt_tags", [])),
        "r170_unique_prompt_hashes": len(new_by_hash),
        "shared_prompt_hashes": len(shared),
        "same_prompt_old_new_comparison_available": len(shared) > 0,
    }
    return rows, summary


def write_markdown(path: Path, payload: dict[str, Any], distribution_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# R222 Prompt Bias Retrospective",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "R222 does not call an LLM. It checks whether existing old artifacts can support a prefer-list vs no-prefer comparison.",
        "",
        "## Verdict",
        "",
        f"- Same-fragment old/new comparison available: `{payload['old_new_join']['same_prompt_old_new_comparison_available']}`",
        f"- Shared prompt hashes: `{payload['old_new_join']['shared_prompt_hashes']}`",
        f"- Current Rust prompt has prefer-list wording: `{payload['prompts']['rust_agentflame_has_prefer_list']}`",
        f"- Legacy Python prompt has prefer-list wording: `{payload['prompts']['legacy_python_has_prefer_list']}`",
        f"- Bias risk observed in existing distributions: `{payload['claim_gates']['bias_risk_observed']}`",
        f"- True ablation still required: `{payload['claim_gates']['same_fragment_prefer_ablation_required']}`",
        "",
        "## Distribution Signals",
        "",
        "| source | model | dimension | total | unique | effective | top1 | top1 % | review+refactor % | top tags |",
        "|---|---:|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in distribution_rows:
        lines.append(
            "| {source} | {model} | {dimension} | {total} | {unique_tags} | {effective_tags} | {top1_tag} | {top1_share_pct} | {review_refactor_share_pct} | {top_tags} |".format(
                **{key: str(row.get(key, "")) for key in [
                    "source",
                    "model",
                    "dimension",
                    "total",
                    "unique_tags",
                    "effective_tags",
                    "top1_tag",
                    "top1_share_pct",
                    "review_refactor_share_pct",
                    "top_tags",
                ]}
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The old Python no-prefer artifact is not comparable to R170 by prompt hash; it is a different small sample.",
            "- R180 already shows model/prompt concentration risks: 0.6B collapses heavily to `debug`, 1.1B collapses to `localization/localized`, and 3B concentrates on `review/refactor`.",
            "- Existing data is enough to mark the prefer-list prompt as risky, but not enough to quantify the causal effect of the prefer-list itself.",
            "- The next required experiment is a same-fragment R223 ablation: current prefer-list vs no-prefer vs anti-common no-prefer over the R122 300 redacted fragments.",
            "",
            "Claim boundary: R222 is retrospective evidence only. It does not prove that removing the prefer-list improves adequacy.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(vis_out: Path, r170_report_path: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    old_prompt_rows = read_csv(vis_out / "prompt-tags.csv")
    tag_counts = read_csv(vis_out / "tag-stats-r189" / "tag-counts-r170.csv")
    r122_rows = read_csv(vis_out / "tag-adequacy-label-packet-r122.csv")
    r180 = read_json(vis_out / "model-benchmarks-r180.json")
    r170_report = read_json(r170_report_path)

    join_rows, join_summary = old_new_hash_join(old_prompt_rows, r170_report)
    write_csv(
        out_dir / "old-new-prompt-hash-join-r222.csv",
        join_rows,
        ["prompt_hash", "old_tag", "new_tag", "old_count", "new_count", "same_tag"],
    )

    distribution_rows: list[dict[str, Any]] = []
    old_stats = dist_stats([row.get("prompt_tag", "") for row in old_prompt_rows], "prompt_rows")
    old_stats["source"] = "legacy_python_no_prefer_artifact"
    old_stats["dimension"] = "prompt"
    old_stats["model"] = "sample36"
    distribution_rows.append(old_stats)
    for dimension in [
        "session_tag_by_sessions",
        "prompt_tag_by_prompt_rows",
        "llm_tag_by_llm_events",
        "prompt_tag_by_system_effect_weight",
        "llm_tag_by_estimated_tokens",
    ]:
        row = r170_dimension_stats(tag_counts, dimension)
        row["model"] = "r170_prefer_list"
        distribution_rows.append(row)
    distribution_rows.extend(r180_model_stats(r180))
    distribution_rows.extend(r122_stats(r122_rows))
    write_csv(
        out_dir / "prompt-bias-distributions-r222.csv",
        distribution_rows,
        [
            "source",
            "model",
            "dimension",
            "unit",
            "total",
            "unique_tags",
            "effective_tags",
            "top1_tag",
            "top1_count",
            "top1_share_pct",
            "top2_share_pct",
            "top5_share_pct",
            "refactor_share_pct",
            "review_refactor_share_pct",
            "exact_stability_pct",
            "valid_run_pct",
            "watched_word_counts",
            "top_tags",
        ],
    )

    bias_risk = any(
        as_float(row.get("top1_share_pct")) >= 50.0
        or as_float(row.get("review_refactor_share_pct")) >= 40.0
        for row in distribution_rows
        if row.get("source") in {"r180_model_runs", "r122_candidate_modal_tags", "r170_tag_counts"}
    )
    payload = {
        "schema_version": 1,
        "run_id": "R222",
        "generated_at": now_iso(),
        "inputs": {
            "legacy_prompt_rows": rel(vis_out / "prompt-tags.csv"),
            "r170_report": rel(r170_report_path),
            "r170_tag_counts": rel(vis_out / "tag-stats-r189" / "tag-counts-r170.csv"),
            "r180": rel(vis_out / "model-benchmarks-r180.json"),
            "r122": rel(vis_out / "tag-adequacy-label-packet-r122.csv"),
        },
        "outputs": {
            "summary_json": rel(out_dir / "prompt-bias-retrospective-r222.json"),
            "summary_md": rel(out_dir / "prompt-bias-retrospective-r222.md"),
            "distribution_csv": rel(out_dir / "prompt-bias-distributions-r222.csv"),
            "join_csv": rel(out_dir / "old-new-prompt-hash-join-r222.csv"),
        },
        "prompts": {
            "rust_agentflame_has_prefer_list": prompt_has_prefer_list(REPO_ROOT / "agentflame" / "src" / "main.rs"),
            "legacy_python_has_prefer_list": legacy_prompt_has_prefer_list(SCRIPT_DIR / "semantic_tag_flamegraph.py"),
        },
        "old_new_join": join_summary,
        "distribution_highlights": {
            "r180_0_6b_top1": next(
                (row for row in distribution_rows if row.get("source") == "r180_model_runs" and row.get("model") == "0.6b"),
                {},
            ),
            "r180_1_1b_top1": next(
                (row for row in distribution_rows if row.get("source") == "r180_model_runs" and row.get("model") == "1.1b"),
                {},
            ),
            "r180_3b_top1": next(
                (row for row in distribution_rows if row.get("source") == "r180_model_runs" and row.get("model") == "3b"),
                {},
            ),
            "r122_all": next(
                (row for row in distribution_rows if row.get("source") == "r122_candidate_modal_tags" and row.get("dimension") == "all"),
                {},
            ),
        },
        "claim_gates": {
            "same_fragment_old_new_comparison_available": join_summary["same_prompt_old_new_comparison_available"],
            "prefer_list_ablation_available": False,
            "bias_risk_observed": bias_risk,
            "same_fragment_prefer_ablation_required": True,
            "remove_prefer_list_supported_by_existing_evidence": False,
        },
        "claim_boundary": (
            "R222 is a retrospective audit over existing artifacts. It finds prompt-bias risk and "
            "documents that old artifacts are not a same-fragment prefer-list ablation. It does not "
            "prove that any prompt variant has better semantic adequacy."
        ),
        "git": {
            "commit": git(["rev-parse", "HEAD"]),
            "status_short": git(["status", "--short"]),
        },
    }
    write_json(out_dir / "prompt-bias-retrospective-r222.json", payload)
    write_markdown(out_dir / "prompt-bias-retrospective-r222.md", payload, distribution_rows)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vis-out", type=Path, default=DEFAULT_VIS_OUT)
    parser.add_argument("--r170-report", type=Path, default=DEFAULT_R170_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    payload = run(args.vis_out, args.r170_report, args.out)
    print(
        json.dumps(
            {
                "status": "ok",
                "out_dir": rel(args.out),
                "same_fragment_old_new": payload["old_new_join"]["same_prompt_old_new_comparison_available"],
                "shared_prompt_hashes": payload["old_new_join"]["shared_prompt_hashes"],
                "bias_risk_observed": payload["claim_gates"]["bias_risk_observed"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
