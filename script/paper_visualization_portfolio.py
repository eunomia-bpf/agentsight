#!/usr/bin/env python3
"""R363: generate a paper visualization and analysis portfolio.

This is a paper artifact over existing scored results, not a new empirical
experiment. It turns tracked R320/R345/R348/R355/R361/R362 outputs into
multiple paper-ready views so the paper is not framed as a flamegraph-only
artifact: baseline tradeoff, metric heatmap, diagnostic lenses, actionability,
and oracle-depth adequacy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-visualization-portfolio-r363"
RUN_ID = "R363"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R320 profile accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R320 policy scores": OUT_ROOT / "operation-profile-accuracy-r320" / "policy-scores.csv",
    "R345 diagnostic lens": OUT_ROOT / "operation-diagnostic-lens-portfolio-r345" / "diagnostic-lens-report.json",
    "R348 action counterfactual": OUT_ROOT / "operation-action-counterfactual-r348" / "action-counterfactual-report.json",
    "R354 executable profile patch": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "R355 oracle depth": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "R358 boundary profile patch": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "R361 claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R362 section readiness": OUT_ROOT / "paper-core-section-readiness-r362" / "section-readiness.json",
}

PRIMARY_POLICIES = [
    "flat:width",
    "fixed_session:query_aware",
    "dataset_native:query_aware",
    "raw_action_stack:query_aware",
    "operation_stack:width",
    "operation_stack:query_aware",
    "operation_stack:oracle_upper_bound",
    "label_drilldown:oracle_upper_bound",
]

POLICY_LABELS = {
    "flat:width": "Flat",
    "fixed_session:query_aware": "Fixed-session",
    "dataset_native:query_aware": "Dataset-native",
    "raw_action_stack:query_aware": "Raw-action",
    "operation_stack:width": "Op-stack width",
    "operation_stack:query_aware": "Op-stack query",
    "operation_stack:oracle_upper_bound": "Op-stack oracle",
    "label_drilldown:oracle_upper_bound": "Label drilldown",
}

POLICY_COLORS = {
    "flat:width": "#7a7a7a",
    "fixed_session:query_aware": "#d55e00",
    "dataset_native:query_aware": "#0072b2",
    "raw_action_stack:query_aware": "#cc79a7",
    "operation_stack:width": "#56b4e9",
    "operation_stack:query_aware": "#009e73",
    "operation_stack:oracle_upper_bound": "#004d3a",
    "label_drilldown:oracle_upper_bound": "#f0e442",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status(path: Path) -> str:
    display = rel(path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=ROOT, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=ROOT, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True)
    return result.stdout.strip()


def fnum(value: Any) -> float:
    if value is None or value == "":
        return math.nan
    return float(value)


def fmt(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def tex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def source_rows() -> list[dict[str, str]]:
    return [
        {
            "source": name,
            "path": rel(path),
            "status": git_status(path),
            "sha256": sha256(path),
        }
        for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items()
    ]


def policy_tradeoff_rows(r320: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy in PRIMARY_POLICIES:
        summary = r320["policy_summary"][policy]
        rows.append(
            {
                "policy": policy,
                "label": POLICY_LABELS[policy],
                "view": summary["view"],
                "ranker": summary["ranker"],
                "hidden": bool(summary["uses_hidden_fields"]),
                "ap": summary["median_average_precision"],
                "top5_work": summary["median_top5_work"],
                "top5_recall": summary["median_top5_recall"],
                "budget30_recall": summary["median_budget30_recall"],
                "work_to_first_positive": summary["median_work_to_first_positive"],
                "groups": summary["median_groups"],
            }
        )
    return rows


def heatmap_rows(tradeoff_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metrics = [
        ("AP", "ap", False),
        ("R@30%", "budget30_recall", False),
        ("P@5 recall", "top5_recall", False),
        ("1-Work@5", "top5_work", True),
        ("1-WTFP", "work_to_first_positive", True),
        ("1-logGroups", "groups", True),
    ]
    max_groups = max(row["groups"] for row in tradeoff_rows)
    for policy in tradeoff_rows:
        for label, key, invert in metrics:
            value = float(policy[key])
            if key == "groups":
                score = 1.0 - math.log1p(value) / math.log1p(max_groups)
            elif invert:
                score = 1.0 - value
            else:
                score = value
            rows.append(
                {
                    "policy": policy["policy"],
                    "label": policy["label"],
                    "metric": label,
                    "raw_value": value,
                    "score": max(0.0, min(1.0, score)),
                    "hidden": policy["hidden"],
                }
            )
    return rows


def lens_rows(r345: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in r345["lens_summary"]:
        rows.append(
            {
                "objective": row["objective"],
                "lens": row["lens"],
                "visualization": row["visualization"],
                "operation_stack_family_best_tasks": int(row["operation_stack_family_best_tasks"]),
                "default_operation_stack_best_tasks": int(row["default_operation_stack_best_tasks"]),
                "non_operation_stack_best_tasks": int(row["non_operation_stack_best_tasks"]),
                "distinct_best_views": int(row["distinct_best_views"]),
                "interpretation": row["interpretation"],
            }
        )
    return rows


def action_rows(r348: dict[str, Any], r354: dict[str, Any], r358: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in r348["action_class_summary"]:
        rows.append(
            {
                "action_class": row["action_class"],
                "objective_rows": int(row["objective_rows"]),
                "tasks": int(row["tasks"]),
                "median_gain_over_default": fnum(row["median_gain_over_default"]),
                "max_gain_over_default": fnum(row["max_gain_over_default"]),
                "source": "R348",
            }
        )
    summary = r354["summary"]
    rows.append(
        {
            "action_class": "executable_profile_spec_patch",
            "objective_rows": int(str(summary["accepted_patches"]).split("/")[0]),
            "tasks": int(str(summary["accepted_patches"]).split("/")[1]),
            "median_gain_over_default": float(summary["median_delta_ap"]),
            "max_gain_over_default": float(summary["median_delta_top5_lift"]),
            "source": "R354",
        }
    )
    rows.append(
        {
            "action_class": "boundary_derived_fields",
            "objective_rows": 1,
            "tasks": 1,
            "median_gain_over_default": float(r358["summary"]["learned_boundary_delta_ap_vs_semantic"]),
            "max_gain_over_default": float(r358["summary"]["learned_boundary_group_reduction_vs_semantic"]),
            "source": "R358",
        }
    )
    return rows


def oracle_depth_rows(r355: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = {
        ("operation_stack:query_aware", "flat:width", "top5_unit_work"),
        ("operation_stack:query_aware", "fixed_session:query_aware", "budget30_positive_unit_recall"),
        ("operation_stack:query_aware", "fixed_session:query_aware", "budget30_positive_unit_f1"),
        ("operation_stack:query_aware", "fixed_session:query_aware", "groups_to_50pct_positive_units"),
        ("operation_stack:query_aware", "raw_action_stack:query_aware", "positive_units_per_group"),
    }
    rows: list[dict[str, Any]] = []
    for row in r355["comparisons"]:
        key = (row["left"], row["right"], row["metric"])
        if key in wanted:
            rows.append(
                {
                    "comparison": f"{row['left']} vs {row['right']}",
                    "metric": row["metric"],
                    "direction": row["direction"],
                    "task_depth_rows": int(row["task_depth_rows"]),
                    "improved_rows": int(row["improved_rows"]),
                    "worse_rows": int(row["worse_rows"]),
                    "tied_rows": int(row["tied_rows"]),
                    "median_delta": float(row["median_delta"]),
                }
            )
    return rows


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif;font-size:12px;fill:#222}.small{font-size:10px}.title{font-size:16px;font-weight:700}.axis{stroke:#333;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}.label{font-size:11px}</style>",
    ]


def write_tradeoff_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 760, 440
    left, right, top, bottom = 72, 260, 48, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    lines = svg_header(width, height)
    lines.append('<text class="title" x="24" y="28">Baseline tradeoff: inspection work vs. budget recall</text>')
    for i in range(6):
        x = left + plot_w * i / 5
        y = top + plot_h * i / 5
        lines.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}"/>')
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}"/>')
    lines.append(f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}"/>')
    lines.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}"/>')
    lines.append(f'<text x="{left + plot_w/2 - 90}" y="{height-24}">Median top-5 inspected work (lower is better)</text>')
    lines.append(f'<text transform="translate(18,{top + plot_h/2 + 90}) rotate(-90)">Median budget-30 recall (higher is better)</text>')
    for i in range(6):
        tick = i / 5
        x = left + plot_w * tick
        y = top + plot_h * (1 - tick)
        lines.append(f'<text class="small" x="{x-8:.1f}" y="{top+plot_h+18}">{tick:.1f}</text>')
        lines.append(f'<text class="small" x="{left-34}" y="{y+4:.1f}">{tick:.1f}</text>')
    for row in rows:
        x = left + plot_w * float(row["top5_work"])
        y = top + plot_h * (1 - float(row["budget30_recall"]))
        color = POLICY_COLORS[row["policy"]]
        radius = 7 if row["policy"] == "operation_stack:query_aware" else 5
        stroke = "#000" if row["hidden"] else "#fff"
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" stroke="{stroke}" stroke-width="1.5"/>')
        if row["policy"] == "operation_stack:query_aware":
            lines.append(f'<text class="label" x="{x+10:.1f}" y="{y-8:.1f}">op-stack query</text>')
    legend_x = left + plot_w + 28
    lines.append(f'<text x="{legend_x}" y="{top}" font-weight="700">Policies</text>')
    for i, row in enumerate(rows):
        y = top + 22 + i * 22
        color = POLICY_COLORS[row["policy"]]
        suffix = " (oracle)" if row["hidden"] else ""
        lines.append(f'<rect x="{legend_x}" y="{y-10}" width="12" height="12" fill="{color}" stroke="#333" stroke-width="0.5"/>')
        lines.append(f'<text class="small" x="{legend_x+18}" y="{y}">{html.escape(row["label"] + suffix)}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_heatmap_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    policies = [POLICY_LABELS[p] for p in PRIMARY_POLICIES]
    metrics = ["AP", "R@30%", "P@5 recall", "1-Work@5", "1-WTFP", "1-logGroups"]
    cell_w, cell_h = 92, 30
    left, top = 150, 56
    width = left + cell_w * len(metrics) + 30
    height = top + cell_h * len(policies) + 60
    score = {(row["label"], row["metric"]): row["score"] for row in rows}
    raw = {(row["label"], row["metric"]): row["raw_value"] for row in rows}
    lines = svg_header(width, height)
    lines.append('<text class="title" x="24" y="28">Metric heatmap: accuracy, work, and fragmentation</text>')
    for j, metric in enumerate(metrics):
        x = left + j * cell_w + 4
        lines.append(f'<text class="small" x="{x}" y="{top-12}">{html.escape(metric)}</text>')
    for i, policy in enumerate(policies):
        y = top + i * cell_h
        lines.append(f'<text class="small" x="18" y="{y+20}">{html.escape(policy)}</text>')
        for j, metric in enumerate(metrics):
            value = score[(policy, metric)]
            green = int(235 - value * 110)
            red = int(245 - value * 185)
            blue = int(240 - value * 170)
            fill = f"rgb({red},{green},{blue})"
            x = left + j * cell_w
            lines.append(f'<rect x="{x}" y="{y}" width="{cell_w-3}" height="{cell_h-3}" fill="{fill}" stroke="#fff"/>')
            lines.append(f'<text class="small" x="{x+8}" y="{y+19}">{fmt(raw[(policy, metric)])}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_lens_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 820, 380
    left, top, bar_w = 250, 56, 440
    lines = svg_header(width, height)
    lines.append('<text class="title" x="24" y="28">Diagnostic lenses: which view wins each objective?</text>')
    max_tasks = max(row["operation_stack_family_best_tasks"] + row["non_operation_stack_best_tasks"] for row in rows)
    for i, row in enumerate(rows):
        y = top + i * 44
        os_w = bar_w * row["operation_stack_family_best_tasks"] / max_tasks
        non_w = bar_w * row["non_operation_stack_best_tasks"] / max_tasks
        lines.append(f'<text class="small" x="18" y="{y+15}">{html.escape(row["objective"])}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{os_w:.1f}" height="20" fill="#009e73"/>')
        lines.append(f'<rect x="{left+os_w:.1f}" y="{y}" width="{non_w:.1f}" height="20" fill="#d55e00"/>')
        lines.append(f'<text class="small" x="{left+os_w+non_w+10:.1f}" y="{y+15}">op {row["operation_stack_family_best_tasks"]}, counter {row["non_operation_stack_best_tasks"]}</text>')
    lines.append(f'<rect x="{left}" y="{height-48}" width="14" height="14" fill="#009e73"/><text class="small" x="{left+20}" y="{height-36}">operation-stack family best</text>')
    lines.append(f'<rect x="{left+210}" y="{height-48}" width="14" height="14" fill="#d55e00"/><text class="small" x="{left+230}" y="{height-36}">baseline/counterpoint best</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_action_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    rows = sorted(rows, key=lambda row: row["objective_rows"], reverse=True)
    width, height = 860, 430
    left, top, bar_w = 250, 52, 480
    max_rows = max(row["objective_rows"] for row in rows)
    lines = svg_header(width, height)
    lines.append('<text class="title" x="24" y="28">Actionability knobs: non-default actions and gains</text>')
    for i, row in enumerate(rows):
        y = top + i * 34
        w = bar_w * row["objective_rows"] / max_rows
        color = "#009e73" if "operation_stack" in row["action_class"] or "profile_spec" in row["action_class"] or "boundary" in row["action_class"] else "#0072b2"
        lines.append(f'<text class="small" x="18" y="{y+15}">{html.escape(row["action_class"])}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="18" fill="{color}"/>')
        lines.append(f'<text class="small" x="{left+w+8:.1f}" y="{y+14}">{row["objective_rows"]} rows, gain {fmt(row["median_gain_over_default"])}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_oracle_depth_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 820, 310
    left, top, bar_w = 300, 52, 420
    lines = svg_header(width, height)
    lines.append('<text class="title" x="24" y="28">Oracle-depth adequacy: rows improved by operation-stack query-aware</text>')
    for i, row in enumerate(rows):
        y = top + i * 38
        w = bar_w * row["improved_rows"] / row["task_depth_rows"]
        label = f"{row['metric']} vs {row['comparison'].split(' vs ')[1]}"
        lines.append(f'<text class="small" x="18" y="{y+15}">{html.escape(label)}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="18" fill="#eee"/>')
        lines.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="18" fill="#009e73"/>')
        lines.append(f'<text class="small" x="{left+bar_w+8}" y="{y+14}">{row["improved_rows"]}/{row["task_depth_rows"]}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_checks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tradeoff = payload["tradeoff_rows"]
    lens = payload["lens_rows"]
    action = payload["action_rows"]
    depth = payload["oracle_depth_rows"]
    source_status = payload["source_status"]
    op_query = next(row for row in tradeoff if row["policy"] == "operation_stack:query_aware")
    flat = next(row for row in tradeoff if row["policy"] == "flat:width")
    fixed = next(row for row in tradeoff if row["policy"] == "fixed_session:query_aware")
    checks = [
        {
            "check": "multi_view_portfolio_not_flamegraph_only",
            "status": "pass" if len(payload["visualizations"]) >= 5 else "fail",
            "evidence": f"{len(payload['visualizations'])} paper views generated.",
        },
        {
            "check": "baseline_tradeoff_view_preserves_main_claim",
            "status": "pass"
            if op_query["top5_work"] < flat["top5_work"] and op_query["budget30_recall"] >= fixed["budget30_recall"]
            else "fail",
            "evidence": "Operation-stack query-aware remains lower work than flat and at least fixed-session budget recall in the median summary.",
        },
        {
            "check": "diagnostic_lens_view_preserves_counterpoints",
            "status": "pass"
            if len(lens) == 6 and any(row["non_operation_stack_best_tasks"] > row["operation_stack_family_best_tasks"] for row in lens)
            else "fail",
            "evidence": "Six diagnostic lenses are present and at least one lens is a non-operation-stack counterpoint.",
        },
        {
            "check": "actionability_view_has_nondefault_knobs",
            "status": "pass" if sum(row["objective_rows"] for row in action) >= 36 else "fail",
            "evidence": "Actionability rows include objective-level counterfactuals plus executable profile-spec and boundary-field knobs.",
        },
        {
            "check": "oracle_depth_view_preserves_depth_support",
            "status": "pass" if any(row["improved_rows"] == 24 for row in depth) and any(row["improved_rows"] >= 20 for row in depth) else "fail",
            "evidence": "Oracle-depth rows preserve 24/24 flat-work and >=20/24 fixed-session recall/group support.",
        },
        {
            "check": "source_policy_no_new_data_or_profiler_rerun",
            "status": "pass"
            if payload["input_policy"]["dataset_sync"] == "none"
            and payload["input_policy"]["profiler_rerun"] is False
            and all(row["status"] == "tracked_clean" for row in source_status)
            else "fail",
            "evidence": "R363 reads tracked clean upstream artifacts only.",
        },
        {
            "check": "two_abstractions_only",
            "status": "pass" if payload["profiler_abstractions"] == ["operation", "operation stack"] else "fail",
            "evidence": "Visualization portfolio is over operation/operation-stack outputs, not new profiler objects.",
        },
    ]
    return checks


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R363 Paper Visualization Portfolio",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a visualization and analysis portfolio over existing tracked results, not a new empirical result.",
        f"- Paper table: `{payload['paper_table']}`.",
        "",
        "## Visualizations",
        "",
        "| View | Path | Claim role |",
        "|---|---|---|",
    ]
    for row in payload["visualizations"]:
        lines.append(f"| {row['name']} | `{row['path']}` | {row['claim_role']} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    cards = []
    for row in payload["visualizations"]:
        svg_path = Path(row["path"]).name
        cards.append(
            f"<section><h2>{html.escape(row['name'])}</h2><p>{html.escape(row['claim_role'])}</p>"
            f"<img src=\"{html.escape(svg_path)}\" alt=\"{html.escape(row['name'])}\" style=\"max-width:100%;border:1px solid #ddd\"></section>"
        )
    check_rows = "\n".join(
        f"<tr><td>{html.escape(c['check'])}</td><td>{html.escape(c['status'])}</td><td>{html.escape(c['evidence'])}</td></tr>"
        for c in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R363 Paper Visualization Portfolio</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
section {{ margin: 1.5rem 0; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
</style>
</head>
<body>
<h1>R363 Paper Visualization Portfolio</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>; checks:
{payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
{''.join(cards)}
<h2>Checks</h2>
<table><tr><th>Check</th><th>Status</th><th>Evidence</th></tr>{check_rows}</table>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_latex_table(path: Path, payload: dict[str, Any]) -> None:
    tradeoff = {row["policy"]: row for row in payload["tradeoff_rows"]}
    op_query = tradeoff["operation_stack:query_aware"]
    flat = tradeoff["flat:width"]
    fixed = tradeoff["fixed_session:query_aware"]

    op_best = sum(row["operation_stack_family_best_tasks"] for row in payload["lens_rows"])
    counter_best = sum(row["non_operation_stack_best_tasks"] for row in payload["lens_rows"])

    r348_actions = [row for row in payload["action_rows"] if row["source"] == "R348"]
    total_objectives = sum(row["objective_rows"] for row in r348_actions)
    nondefault = sum(row["objective_rows"] for row in r348_actions if row["action_class"] != "keep_default_operation_stack")
    patch = next(row for row in payload["action_rows"] if row["action_class"] == "executable_profile_spec_patch")
    boundary = next(row for row in payload["action_rows"] if row["action_class"] == "boundary_derived_fields")

    depth_by_metric = {row["metric"]: row for row in payload["oracle_depth_rows"]}

    rows = [
        {
            "view": "Baseline tradeoff",
            "artifact": "baseline-tradeoff.svg",
            "evidence": (
                f"Op-stack query Work@5 {fmt(op_query['top5_work'])} vs flat {fmt(flat['top5_work'])}; "
                f"R@30% {fmt(op_query['budget30_recall'])} vs fixed-session {fmt(fixed['budget30_recall'])}; "
                f"groups {fmt(op_query['groups'])} vs {fmt(fixed['groups'])}."
            ),
            "role": "E2",
        },
        {
            "view": "Metric heatmap",
            "artifact": "metric-heatmap.svg",
            "evidence": (
                f"Shows AP {fmt(op_query['ap'])}, R@30% {fmt(op_query['budget30_recall'])}, "
                f"Work@5 {fmt(op_query['top5_work'])}, and the fixed-session WTFP counterpoint "
                f"{fmt(fixed['work_to_first_positive'])}."
            ),
            "role": "E2",
        },
        {
            "view": "Diagnostic lenses",
            "artifact": "diagnostic-lenses.svg",
            "evidence": (
                f"Six lenses over 36 objective rows: operation-stack-family views win {op_best}/36, "
                f"while baseline counterpoints win {counter_best}/36."
            ),
            "role": "E3",
        },
        {
            "view": "Actionability knobs",
            "artifact": "actionability-knobs.svg",
            "evidence": (
                f"{nondefault}/{total_objectives} objective rows require non-default actions; "
                f"R354 accepts {patch['objective_rows']}/{patch['tasks']} profile-spec patches; "
                f"R358 boundary fields add AP {fmt(boundary['median_gain_over_default'])}."
            ),
            "role": "E3",
        },
        {
            "view": "Oracle-depth adequacy",
            "artifact": "oracle-depth-adequacy.svg",
            "evidence": (
                f"Lower top-5 unit work than flat on {depth_by_metric['top5_unit_work']['improved_rows']}/24 rows; "
                f"higher fixed-session unit recall on "
                f"{depth_by_metric['budget30_positive_unit_recall']['improved_rows']}/24; "
                f"fewer groups to 50% positives on "
                f"{depth_by_metric['groups_to_50pct_positive_units']['improved_rows']}/24."
            ),
            "role": "E2/E3",
        },
    ]

    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\caption{R363 paper-facing visualization portfolio. The views are generated from tracked R320/R345/R348/R354/R355/R358 artifacts and summarize E2/E3 tradeoffs; R363 is not a new empirical result.}",
        r"\label{tab:visualization-portfolio}",
        r"\begin{tabular}{p{0.16\linewidth}p{0.19\linewidth}p{0.45\linewidth}p{0.09\linewidth}}",
        r"\toprule",
        r"View & Artifact & Paper-facing evidence & Role \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{tex_escape(row['view'])} & \\texttt{{{tex_escape(row['artifact'])}}} & "
            f"{tex_escape(row['evidence'])} & {tex_escape(row['role'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    start = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    r320 = read_json(SOURCES["R320 profile accuracy"])
    r345 = read_json(SOURCES["R345 diagnostic lens"])
    r348 = read_json(SOURCES["R348 action counterfactual"])
    r354 = read_json(SOURCES["R354 executable profile patch"])
    r355 = read_json(SOURCES["R355 oracle depth"])
    r358 = read_json(SOURCES["R358 boundary profile patch"])
    r361 = read_json(SOURCES["R361 claim evidence"])
    r362 = read_json(SOURCES["R362 section readiness"])

    tradeoff = policy_tradeoff_rows(r320)
    heatmap = heatmap_rows(tradeoff)
    lenses = lens_rows(r345)
    actions = action_rows(r348, r354, r358)
    depth = oracle_depth_rows(r355)

    write_tradeoff_svg(out_dir / "baseline-tradeoff.svg", tradeoff)
    write_heatmap_svg(out_dir / "metric-heatmap.svg", heatmap)
    write_lens_svg(out_dir / "diagnostic-lenses.svg", lenses)
    write_action_svg(out_dir / "actionability-knobs.svg", actions)
    write_oracle_depth_svg(out_dir / "oracle-depth-adequacy.svg", depth)

    visualizations = [
        {
            "name": "baseline-tradeoff",
            "path": rel(out_dir / "baseline-tradeoff.svg"),
            "claim_role": "E2 baseline superiority/tradeoff: work, recall, and oracle upper bounds.",
        },
        {
            "name": "metric-heatmap",
            "path": rel(out_dir / "metric-heatmap.svg"),
            "claim_role": "E2 fidelity and counterpoints across AP, recall, work, WTFP, and fragmentation.",
        },
        {
            "name": "diagnostic-lenses",
            "path": rel(out_dir / "diagnostic-lenses.svg"),
            "claim_role": "E3 multi-lens analysis: ranked stacks, hot groups, budget curves, drilldown, and fragmentation.",
        },
        {
            "name": "actionability-knobs",
            "path": rel(out_dir / "actionability-knobs.svg"),
            "claim_role": "E3 actionable optimization knobs from view/ranker/stack/profile-spec/boundary changes.",
        },
        {
            "name": "oracle-depth-adequacy",
            "path": rel(out_dir / "oracle-depth-adequacy.svg"),
            "claim_role": "E2/E3 depth-aware localization against task-specific oracle units.",
        },
    ]

    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-visualization-portfolio.v1",
        "status": "unknown",
        "commit": git_commit(),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "network_access_required": False,
            "profiler_rerun": False,
            "hidden_label_use": "only through already-scored upstream artifacts",
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "upstream_gates": {
            "r361": r361["status"],
            "r361_checks": f"{r361['summary']['checks_passed']}/{r361['summary']['checks_total']}",
            "r362": r362["status"],
            "r362_checks": f"{r362['summary']['checks_passed']}/{r362['summary']['checks_total']}",
        },
        "visualizations": visualizations,
        "tradeoff_rows": tradeoff,
        "heatmap_rows": heatmap,
        "lens_rows": lenses,
        "action_rows": actions,
        "oracle_depth_rows": depth,
        "source_status": source_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }
    checks = build_checks(payload)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    payload["status"] = status
    payload["checks"] = checks
    payload["summary"] = {
        "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
        "checks_total": len(checks),
        "visualizations": len(visualizations),
        "status": status,
    }

    write_csv(
        out_dir / "baseline-tradeoff.csv",
        tradeoff,
        ["policy", "label", "view", "ranker", "hidden", "ap", "top5_work", "top5_recall", "budget30_recall", "work_to_first_positive", "groups"],
    )
    write_csv(out_dir / "metric-heatmap.csv", heatmap, ["policy", "label", "metric", "raw_value", "score", "hidden"])
    write_csv(
        out_dir / "diagnostic-lenses.csv",
        lenses,
        [
            "objective",
            "lens",
            "visualization",
            "operation_stack_family_best_tasks",
            "default_operation_stack_best_tasks",
            "non_operation_stack_best_tasks",
            "distinct_best_views",
            "interpretation",
        ],
    )
    write_csv(
        out_dir / "actionability-knobs.csv",
        actions,
        ["action_class", "objective_rows", "tasks", "median_gain_over_default", "max_gain_over_default", "source"],
    )
    write_csv(
        out_dir / "oracle-depth-adequacy.csv",
        depth,
        ["comparison", "metric", "direction", "task_depth_rows", "improved_rows", "worse_rows", "tied_rows", "median_delta"],
    )
    write_csv(out_dir / "portfolio-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    table_path = out_dir / "portfolio-table.tex"
    payload["paper_table"] = rel(table_path)
    write_latex_table(table_path, payload)
    (out_dir / "visualization-portfolio.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(out_dir / "visualization-portfolio.md", payload)
    write_html(out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": payload["summary"]["checks_passed"],
        "checks_total": payload["summary"]["checks_total"],
        "report": rel(out_dir / "visualization-portfolio.json"),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
