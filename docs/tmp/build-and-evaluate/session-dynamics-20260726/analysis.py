#!/usr/bin/env python3
"""Recompute session dynamics, startup, bookkeeping, and retry-loop evidence.

The script is intentionally self-contained and writes only below its own
experiment directory.  It treats exported ``events`` as tool calls and
``actions``/``source_paths`` as file-access evidence; those denominators are
never silently mixed.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import spearmanr


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = HERE.parent / "rq1-rq4-recompute-final" / "rq1-raw" / "events"
RAW = HERE / "raw"
FIGURES = HERE / "figures"
PHASES = ("early", "middle", "late")
PHASE_LABELS = {"early": "Early", "middle": "Middle", "late": "Late"}
CATEGORIES = ("read", "edit", "shell", "network", "plan", "subagent", "tool")
VENDOR_COLORS = {"claude": "#D55E00", "codex": "#0072B2", "gemini": "#009E73"}
ACCESS_READ = {"read"}
ACCESS_WRITE = {"write", "create", "delete", "rename", "rename_from"}
GAP_ORDER = ("<1h", "1–6h", "6–24h", "1–3d", "3–7d", "≥7d")
PROJECT_ORDER = (
    "agentsight",
    "ActPlane",
    "bpf-developer-tutorial",
    "eunomia-dev",
    "agentskill-observability-paper",
    "academic-writing-skills",
)


def ensure_dirs() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_path(path: str | None) -> str:
    if not path:
        return ""
    return re.sub(r"/+", "/", path.strip().replace("\\", "/"))


def event_accesses(event: dict[str, Any]) -> list[tuple[str, str]]:
    """Return one non-duplicated access list.

    Worktree-relative ``actions`` are preferred.  ``source_paths`` is the
    fallback that retains external memory/skill files excluded from a worktree.
    """

    source = event.get("actions") or event.get("source_paths") or []
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for item in source:
        path = clean_path(item.get("path"))
        access = str(item.get("access") or "")
        if not path or not access:
            continue
        key = (path, access)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


def action_accesses(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolved worktree actions, retaining artifact identity."""

    result = []
    seen = set()
    for item in event.get("actions") or []:
        path = clean_path(item.get("path"))
        access = str(item.get("access") or "")
        artifact_id = str(item.get("artifact_id") or path)
        key = (artifact_id, path, access)
        if path and access and key not in seen:
            seen.add(key)
            result.append(
                {"artifact_id": artifact_id, "path": path, "access": access}
            )
    return result


def source_accesses(event: dict[str, Any]) -> list[dict[str, str]]:
    result = []
    seen = set()
    for item in event.get("source_paths") or []:
        path = clean_path(item.get("path"))
        access = str(item.get("access") or "")
        key = (path, access)
        if path and access and key not in seen:
            seen.add(key)
            result.append({"path": path, "access": access})
    return result


def read_paths(event: dict[str, Any]) -> list[str]:
    return [path for path, access in event_accesses(event) if access in ACCESS_READ]


def write_paths(event: dict[str, Any]) -> list[str]:
    return [path for path, access in event_accesses(event) if access in ACCESS_WRITE]


def patch_changed_lines(event: dict[str, Any]) -> float:
    if event.get("tool_name") != "apply_patch":
        return math.nan
    command = str(event.get("command") or "")
    changed = 0
    for line in command.splitlines():
        if line.startswith(("+++", "---", "***")):
            continue
        if line.startswith(("+", "-")):
            changed += 1
    return float(changed) if changed else math.nan


@dataclass
class Corpus:
    events: list[dict[str, Any]]
    sessions: dict[tuple[str, str], list[dict[str, Any]]]
    headers: list[dict[str, Any]]
    files: list[Path]


def load_corpus(project_limit: set[str] | None = None) -> Corpus:
    events: list[dict[str, Any]] = []
    sessions: dict[tuple[str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    headers: list[dict[str, Any]] = []
    files: list[Path] = []
    input_index = 0
    for path in sorted(DATA.glob("*.json")):
        if project_limit and path.stem not in project_limit:
            continue
        doc = json.loads(path.read_text())
        files.append(path)
        headers.append({k: v for k, v in doc.items() if k != "events"})
        for event in doc["events"]:
            row = dict(event)
            row["_project"] = path.stem
            row["_input_index"] = input_index
            row["_accesses"] = event_accesses(row)
            row["_action_accesses"] = action_accesses(row)
            row["_source_accesses"] = source_accesses(row)
            row["_read_paths"] = read_paths(row)
            row["_write_paths"] = write_paths(row)
            row["_patch_lines"] = patch_changed_lines(row)
            events.append(row)
            sessions[(path.stem, str(row["session_id"]))].append(row)
            input_index += 1
    for seq in sessions.values():
        seq.sort(
            key=lambda e: (
                int(e["ts_ms"]),
                str(e.get("source_stream_id") or ""),
                int(e.get("source_tool_ordinal") or 0),
                str(e.get("id") or ""),
            )
        )
        for ordinal, event in enumerate(seq, 1):
            event["_ordinal"] = ordinal
    return Corpus(events, dict(sessions), headers, files)


def dominant(values: Iterable[str]) -> str:
    counts = collections.Counter(v for v in values if v)
    return counts.most_common(1)[0][0] if counts else ""


def qtile(series: pd.Series, q: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return float(clean.quantile(q)) if len(clean) else math.nan


def quantile_table(
    frame: pd.DataFrame,
    groups: list[str],
    metrics: list[str],
    *,
    id_col: str | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, sub in frame.groupby(groups, dropna=False, observed=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(groups, keys))
        for metric in metrics:
            clean = pd.to_numeric(sub[metric], errors="coerce").dropna()
            row = {
                **base,
                "metric": metric,
                "n": int(len(clean)),
                "q25": float(clean.quantile(0.25)) if len(clean) else math.nan,
                "median": float(clean.quantile(0.5)) if len(clean) else math.nan,
                "q75": float(clean.quantile(0.75)) if len(clean) else math.nan,
                "p90": float(clean.quantile(0.9)) if len(clean) else math.nan,
                "mean": float(clean.mean()) if len(clean) else math.nan,
            }
            if id_col:
                row["n_units"] = int(sub.loc[clean.index, id_col].nunique())
            rows.append(row)
    return pd.DataFrame(rows)


def session_metadata(corpus: Corpus) -> pd.DataFrame:
    rows = []
    for (project, session_id), seq in corpus.sessions.items():
        worktrees = sorted(
            {str(e.get("worktree_id")) for e in seq if e.get("worktree_id")}
        )
        gaps = [
            max(0, int(b["ts_ms"]) - int(a["ts_ms"]))
            for a, b in zip(seq, seq[1:])
        ]
        tied = sum(int(a["ts_ms"]) == int(b["ts_ms"]) for a, b in zip(seq, seq[1:]))
        rows.append(
            {
                "project": project,
                "session_id": session_id,
                "vendor": str(seq[0].get("vendor") or ""),
                "calls": len(seq),
                "start_ms": min(int(e["ts_ms"]) for e in seq),
                "end_ms": max(int(e["ts_ms"]) for e in seq),
                "duration_hours": (
                    max(int(e["ts_ms"]) for e in seq)
                    - min(int(e["ts_ms"]) for e in seq)
                )
                / 3_600_000,
                "worktree_id": worktrees[0] if len(worktrees) == 1 else "",
                "worktree_count": len(worktrees),
                "worktree_ids": "|".join(worktrees),
                "source_streams": len({str(e.get("source_stream_id") or "") for e in seq}),
                "prompt_indices": len({e.get("prompt_index") for e in seq}),
                "root_calls": sum(e.get("source_role") == "root" for e in seq),
                "subagent_calls": sum(e.get("source_role") == "subagent" for e in seq),
                "user_role_calls": sum(e.get("source_role") == "user" for e in seq),
                "max_internal_gap_hours": (max(gaps) / 3_600_000 if gaps else 0.0),
                "tied_adjacent_timestamp_share": (
                    tied / (len(seq) - 1) if len(seq) > 1 else 0.0
                ),
            }
        )
    return pd.DataFrame(rows)


def assign_event_history(seq: list[dict[str, Any]]) -> None:
    seen_reads: set[str] = set()
    recent_writes: collections.deque[set[str]] = collections.deque(maxlen=10)
    for event in seq:
        resolved = event["_action_accesses"] if event.get("status") != "fail" else []
        reads = [
            item["artifact_id"] for item in resolved if item["access"] in ACCESS_READ
        ]
        event["_read_actions"] = len(reads)
        event["_repeat_read_actions"] = sum(artifact in seen_reads for artifact in reads)
        event["_any_repeat_read_call"] = bool(
            any(artifact in seen_reads for artifact in reads)
        )
        seen_reads.update(reads)
        writes = {
            item["artifact_id"] for item in resolved if item["access"] in ACCESS_WRITE
        }
        event["_edit_artifacts"] = writes
        event["_edit_paths"] = {
            item["path"] for item in resolved if item["access"] in ACCESS_WRITE
        }
        recent_union = set().union(*recent_writes) if recent_writes else set()
        is_edit = event.get("category") == "edit"
        event["_recent_reedit"] = bool(is_edit and writes and writes.intersection(recent_union))
        recent_writes.append(writes)


def summarize_slice(
    project: str,
    session_id: str,
    vendor: str,
    label: str | int,
    seq: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    calls = len(seq)
    resolved = sum(e.get("status") in {"ok", "fail"} for e in seq)
    fail = sum(e.get("status") == "fail" for e in seq)
    read_n = sum(int(e["_read_actions"]) for e in seq)
    reread_n = sum(int(e["_repeat_read_actions"]) for e in seq)
    edit_events = [
        e for e in seq if e.get("category") == "edit" and e.get("status") != "fail"
    ]
    edit_paths = [p for e in edit_events for p in e["_edit_paths"]]
    patch_lines = [float(e["_patch_lines"]) for e in edit_events if not math.isnan(e["_patch_lines"])]
    row: dict[str, Any] = {
        "project": project,
        "session_id": session_id,
        "vendor": vendor,
        "slice": label,
        "calls": calls,
        "repeat_read_share": reread_n / read_n if read_n else math.nan,
        "read_actions": read_n,
        "repeat_read_actions": reread_n,
        "reread_call_share": (
            sum(bool(e["_any_repeat_read_call"]) for e in seq)
            / sum(bool(e["_read_actions"]) for e in seq)
            if any(e["_read_actions"] for e in seq)
            else math.nan
        ),
        "failure_share": fail / calls if calls else math.nan,
        "resolved_failure_share": fail / resolved if resolved else math.nan,
        "observed_share": sum(e.get("status") == "observed" for e in seq) / calls,
        "recent_reedit_share": (
            sum(bool(e["_recent_reedit"]) for e in edit_events) / len(edit_events)
            if edit_events
            else math.nan
        ),
        "edit_calls_per_path": (
            len(edit_events) / len(set(edit_paths)) if edit_paths else math.nan
        ),
        "paths_per_edit_call": (
            len(edit_paths) / sum(bool(e["_write_paths"]) for e in edit_events)
            if any(e["_write_paths"] for e in edit_events)
            else math.nan
        ),
        "patch_lines_median": float(np.median(patch_lines)) if patch_lines else math.nan,
        "patch_lines_n": len(patch_lines),
        "edit_share": len(edit_events) / calls if calls else math.nan,
    }
    for category in CATEGORIES:
        row[f"tool_{category}_share"] = (
            sum(e.get("category") == category for e in seq) / calls if calls else math.nan
        )
    return row


def analyze_drift(corpus: Corpus) -> dict[str, pd.DataFrame]:
    all_phase_rows: list[dict[str, Any]] = []
    phase_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    for (project, session_id), seq in corpus.sessions.items():
        assign_event_history(seq)
        vendor = str(seq[0].get("vendor") or "")
        n = len(seq)
        if n >= 3:
            phase_indices = [
                [i for i in range(n) if min(2, math.floor(3 * i / n)) == phase_idx]
                for phase_idx in range(3)
            ]
            for phase, idx in zip(PHASES, phase_indices):
                all_phase_rows.append(
                    summarize_slice(project, session_id, vendor, phase, [seq[int(i)] for i in idx])
                )
            for gate in (30, 60, 100):
                if n >= gate:
                    for phase, idx in zip(PHASES, phase_indices):
                        row = summarize_slice(
                            project, session_id, vendor, phase, [seq[int(i)] for i in idx]
                        )
                        row["length_gate"] = gate
                        sensitivity_rows.append(row)
                        if gate == 30:
                            phase_rows.append(dict(row))
        if n >= 30:
            decile_indices = [
                [
                    i
                    for i in range(n)
                    if min(9, math.floor(10 * ((i + 0.5) / n))) == decile
                ]
                for decile in range(10)
            ]
            for decile, idx in enumerate(decile_indices, 1):
                curve_rows.append(
                    summarize_slice(
                        project, session_id, vendor, decile, [seq[int(i)] for i in idx]
                    )
                )
    all_phase = pd.DataFrame(all_phase_rows)
    phase = pd.DataFrame(phase_rows)
    sensitivity = pd.DataFrame(sensitivity_rows)
    curve = pd.DataFrame(curve_rows)
    gap_map = {}
    for key, seq in corpus.sessions.items():
        gaps = [
            max(0, int(b["ts_ms"]) - int(a["ts_ms"]))
            for a, b in zip(seq, seq[1:])
        ]
        gap_map[key] = max(gaps) / 3_600_000 if gaps else 0.0
    for frame in (all_phase, phase, sensitivity, curve):
        frame["max_internal_gap_hours"] = [
            gap_map[(row.project, row.session_id)] for row in frame.itertuples()
        ]
        frame["noncomposite_8h"] = frame.max_internal_gap_hours <= 8
    metric_cols = [
        "repeat_read_share",
        "reread_call_share",
        "failure_share",
        "resolved_failure_share",
        "observed_share",
        "recent_reedit_share",
        "edit_calls_per_path",
        "paths_per_edit_call",
        "patch_lines_median",
        "edit_share",
    ] + [f"tool_{category}_share" for category in CATEGORIES]
    quantiles = quantile_table(
        phase, ["project", "vendor", "slice"], metric_cols, id_col="session_id"
    )
    all_session_quantiles = quantile_table(
        all_phase,
        ["project", "vendor", "slice"],
        metric_cols,
        id_col="session_id",
    )
    sensitivity_quantiles = quantile_table(
        sensitivity,
        ["project", "vendor", "length_gate", "slice"],
        metric_cols,
        id_col="session_id",
    )
    curve_q = quantile_table(
        curve, ["project", "vendor", "slice"], metric_cols, id_col="session_id"
    )
    paired_rows: list[dict[str, Any]] = []
    wide_source = phase.pivot_table(
        index=["project", "vendor", "session_id"],
        columns="slice",
        values=metric_cols,
        aggfunc="first",
    )
    for key, row in wide_source.iterrows():
        project, vendor, session_id = key
        out = {"project": project, "vendor": vendor, "session_id": session_id}
        for metric in metric_cols:
            try:
                out[f"{metric}_late_minus_early"] = float(
                    row[(metric, "late")] - row[(metric, "early")]
                )
            except (KeyError, TypeError):
                out[f"{metric}_late_minus_early"] = math.nan
        paired_rows.append(out)
    paired = pd.DataFrame(paired_rows)
    delta_cols = [c for c in paired.columns if c.endswith("_late_minus_early")]
    paired_q = quantile_table(
        paired, ["project", "vendor"], delta_cols, id_col="session_id"
    )
    noncomposite_ids = {
        (row.project, row.session_id)
        for row in phase[phase.noncomposite_8h].itertuples()
    }
    paired_noncomposite = paired[
        [
            (row.project, row.session_id) in noncomposite_ids
            for row in paired.itertuples()
        ]
    ].copy()
    paired_noncomposite_q = quantile_table(
        paired_noncomposite, ["project", "vendor"], delta_cols, id_col="session_id"
    )
    direction_rows = []
    for (project, vendor), sub in paired.groupby(["project", "vendor"]):
        for metric in delta_cols:
            clean = pd.to_numeric(sub[metric], errors="coerce").dropna()
            direction_rows.append(
                {
                    "project": project,
                    "vendor": vendor,
                    "metric": metric,
                    "n": len(clean),
                    "positive_share": float((clean > 0).mean()) if len(clean) else math.nan,
                    "negative_share": float((clean < 0).mean()) if len(clean) else math.nan,
                    "zero_share": float((clean == 0).mean()) if len(clean) else math.nan,
                }
            )
    direction = pd.DataFrame(direction_rows)
    coverage_rows = []
    for (project, vendor), events in pd.DataFrame(
        [
            {
                "project": e["_project"],
                "vendor": e["vendor"],
                "status": e["status"],
                "read_actions": sum(
                    item["access"] in ACCESS_READ for item in e["_action_accesses"]
                ),
                "source_read_paths": sum(
                    item["access"] in ACCESS_READ for item in e["_source_accesses"]
                ),
            }
            for e in corpus.events
        ]
    ).groupby(["project", "vendor"]):
        coverage_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "calls": len(events),
                "nonfailed_resolved_read_actions": int(
                    events.loc[events.status != "fail", "read_actions"].sum()
                ),
                "all_resolved_read_actions": int(events.read_actions.sum()),
                "source_read_paths": int(events.source_read_paths.sum()),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    return {
        "all_session_phase": all_phase,
        "all_session_quantiles": all_session_quantiles,
        "phase": phase,
        "length_sensitivity": sensitivity,
        "length_sensitivity_quantiles": sensitivity_quantiles,
        "quantiles": quantiles,
        "curve": curve,
        "curve_quantiles": curve_q,
        "paired": paired,
        "paired_quantiles": paired_q,
        "paired_noncomposite_8h": paired_noncomposite,
        "paired_noncomposite_8h_quantiles": paired_noncomposite_q,
        "direction": direction,
        "coverage": coverage,
    }


def save_drift_plots(drift: dict[str, pd.DataFrame]) -> None:
    curve_q = drift["curve_quantiles"]
    curve_raw = drift["curve"]
    metrics = [
        ("repeat_read_share", "Repeated-read share"),
        ("failure_share", "Recorded-fail share"),
        ("recent_reedit_share", "Re-edit within 10 calls"),
        ("edit_calls_per_path", "Edit calls / distinct path"),
    ]
    fig, axes = plt.subplots(
        len(PROJECT_ORDER), len(metrics), figsize=(17, 20), sharex=True, constrained_layout=True
    )
    for r, project in enumerate(PROJECT_ORDER):
        for c, (metric, label) in enumerate(metrics):
            ax = axes[r, c]
            sub = curve_q[(curve_q.project == project) & (curve_q.metric == metric)]
            for vendor in sorted(sub.vendor.unique()):
                v = sub[sub.vendor == vendor].sort_values("slice")
                color = VENDOR_COLORS.get(vendor, "#666666")
                n_sessions = curve_raw[
                    (curve_raw.project == project) & (curve_raw.vendor == vendor)
                ].session_id.nunique()
                if n_sessions >= 10:
                    x = pd.to_numeric(v["slice"]).to_numpy(dtype=float)
                    y = pd.to_numeric(v["median"]).to_numpy(dtype=float)
                    q1 = pd.to_numeric(v["q25"]).to_numpy(dtype=float)
                    q3 = pd.to_numeric(v["q75"]).to_numpy(dtype=float)
                    ax.plot(
                        x,
                        y,
                        marker="o",
                        ms=3,
                        lw=1.6,
                        label=f"{vendor} (n={n_sessions})",
                        color=color,
                    )
                    ax.fill_between(x, q1, q3, color=color, alpha=0.12)
                else:
                    raw = curve_raw[
                        (curve_raw.project == project)
                        & (curve_raw.vendor == vendor)
                    ][["slice", metric]].dropna()
                    if len(raw):
                        offsets = (
                            raw.groupby("slice").cumcount()
                            - raw.groupby("slice")[metric].transform("count") / 2
                        ) * 0.025
                        ax.scatter(
                            raw["slice"] + offsets,
                            raw[metric],
                            s=12,
                            alpha=0.45,
                            label=f"{vendor} points (n={n_sessions})",
                            color=color,
                        )
            ax.grid(axis="y", alpha=0.25)
            ax.set_xlim(1, 10)
            if r == 0:
                ax.set_title(label)
            if c == 0:
                ax.set_ylabel(project)
            if r == len(PROJECT_ORDER) - 1:
                ax.set_xlabel("Session progress decile")
            if r == 0 and c == len(metrics) - 1:
                ax.legend(frameon=False, fontsize=8)
    fig.suptitle(
        "Within-session dynamics (median and IQR across sessions with ≥30 calls)", fontsize=15
    )
    fig.savefig(FIGURES / "01_session_progress_curves.png", dpi=180)
    plt.close(fig)

    phase = drift["phase"]
    fig, axes = plt.subplots(3, 2, figsize=(15, 15), constrained_layout=True)
    colors = {
        "read": "#56B4E9",
        "edit": "#E69F00",
        "shell": "#0072B2",
        "network": "#009E73",
        "plan": "#CC79A7",
        "subagent": "#D55E00",
        "tool": "#999999",
    }
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = phase[phase.project == project]
        labels: list[str] = []
        stacks: dict[str, list[float]] = {c: [] for c in CATEGORIES}
        for vendor in sorted(sub.vendor.unique()):
            for phase_name in PHASES:
                v = sub[(sub.vendor == vendor) & (sub["slice"] == phase_name)]
                labels.append(f"{vendor[:2]}-{phase_name[0].upper()}")
                med = np.array(
                    [v[f"tool_{category}_share"].median() for category in CATEGORIES],
                    dtype=float,
                )
                med = np.nan_to_num(med, nan=0.0)
                med = med / med.sum() if med.sum() else med
                for category, value in zip(CATEGORIES, med):
                    stacks[category].append(float(value))
        bottom = np.zeros(len(labels))
        for category in CATEGORIES:
            values = np.array(stacks[category])
            ax.bar(
                np.arange(len(labels)),
                values,
                bottom=bottom,
                label=category,
                color=colors[category],
                width=0.82,
            )
            bottom += values
        ax.set_title(project)
        ax.set_xticks(np.arange(len(labels)), labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylim(0, 1)
        ax.grid(axis="y", alpha=0.2)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=len(CATEGORIES),
        frameon=False,
    )
    fig.suptitle(
        "Tool-category composition by tertile (normalized session medians; E/M/L)", fontsize=15
    )
    fig.savefig(FIGURES / "01_tool_mix_tertiles.png", dpi=180)
    plt.close(fig)


INSTRUCTION_NAMES = {"claude.md", "agents.md", "gemini.md"}
ROOT_README_NAMES = {"readme.md", "readme", "readme.zh-cn.md", "readme.zh.md"}
GIT_STRICT_RE = re.compile(
    r"(?:^|[;&|]\s*|\b)git\s+"
    r"(?:(?:-C|--git-dir|--work-tree)\s+(?:\"[^\"]*\"|'[^']*'|\S+)\s+"
    r"|(?:--git-dir|--work-tree)=\S+\s+|-[^\s]+\s+)*"
    r"(status|log)\b",
    re.I,
)
GIT_BROAD_RE = re.compile(
    r"(?:^|[;&|]\s*|\b)git\s+(?:-[^\s]+\s+)*(status|log|show|diff|branch|rev-parse)\b",
    re.I,
)
ORIENTATION_RE = re.compile(
    r"^\s*(?:pwd|ls(?:\s|$)|tree(?:\s|$)|find(?:\s|$)|rg\s+--files\b)", re.I
)


def basename_lower(path: str) -> str:
    return Path(path).name.lower()


def startup_call_tags(
    event: dict[str, Any], prior_paths: set[str], prior_mutations: set[str]
) -> dict[str, bool]:
    reads = {
        item["artifact_id"]
        for item in event["_action_accesses"]
        if item["access"] in ACCESS_READ and event.get("status") != "fail"
    }
    read_paths_local = {
        item["path"]
        for item in event["_action_accesses"]
        if item["access"] in ACCESS_READ and event.get("status") != "fail"
    }
    command = str(event.get("command") or "")
    instruction = any(
        basename_lower(path) in INSTRUCTION_NAMES for path in read_paths_local
    )
    root_readme = any(
        "/" not in path and basename_lower(path) in ROOT_README_NAMES
        for path in read_paths_local
    )
    git_strict = bool(GIT_STRICT_RE.search(command))
    git_broad = bool(GIT_BROAD_RE.search(command))
    prior_reread = bool(reads.intersection(prior_paths))
    prior_mutation_reread = bool(reads.intersection(prior_mutations))
    orientation = bool(ORIENTATION_RE.search(command))
    return {
        "instruction": instruction,
        "root_readme": root_readme,
        "git_strict": git_strict,
        "git_broad": git_broad,
        "prior_reread": prior_reread,
        "prior_mutation_reread": prior_mutation_reread,
        "orientation": orientation,
        "narrow": instruction or git_strict,
        "extended": instruction or git_strict or root_readme or prior_reread,
        "broad": instruction or git_broad or root_readme or prior_reread or orientation,
    }


def gap_bin(hours: float) -> str:
    if hours < 1:
        return "<1h"
    if hours < 6:
        return "1–6h"
    if hours < 24:
        return "6–24h"
    if hours < 72:
        return "1–3d"
    if hours < 168:
        return "3–7d"
    return "≥7d"


def predecessor_map(
    corpus: Corpus, meta: pd.DataFrame
) -> dict[tuple[str, str], tuple[str, float, str]]:
    """Latest *completed* session in the same project/worktree."""

    pred: dict[tuple[str, str], tuple[str, float, str]] = {}
    eligible_meta = meta[meta.worktree_count == 1]
    for (project, worktree), group in eligible_meta.groupby(
        ["project", "worktree_id"], dropna=False
    ):
        records = group.sort_values(["start_ms", "end_ms"]).to_dict("records")
        completed: list[dict[str, Any]] = []
        for current in records:
            eligible = [r for r in completed if int(r["end_ms"]) < int(current["start_ms"])]
            if eligible:
                previous = max(eligible, key=lambda r: int(r["end_ms"]))
                gap_hours = (
                    int(current["start_ms"]) - int(previous["end_ms"])
                ) / 3_600_000
                pred[(str(project), str(current["session_id"]))] = (
                    str(previous["session_id"]),
                    gap_hours,
                    str(previous["vendor"]),
                )
            completed.append(current)
    return pred


def analyze_startup(corpus: Corpus, meta: pd.DataFrame) -> dict[str, pd.DataFrame]:
    predecessors = predecessor_map(corpus, meta)
    touched: dict[tuple[str, str], set[str]] = {}
    mutated: dict[tuple[str, str], set[str]] = {}
    for key, seq in corpus.sessions.items():
        touched[key] = {
            item["artifact_id"]
            for event in seq
            if event.get("status") != "fail"
            for item in event["_action_accesses"]
        }
        mutated[key] = {
            item["artifact_id"]
            for event in seq
            if event.get("status") != "fail"
            for item in event["_action_accesses"]
            if item["access"] in ACCESS_WRITE
        }
    meta_lookup = {
        (row.project, row.session_id): row for row in meta.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    for (project, session_id), seq in corpus.sessions.items():
        vendor = str(seq[0].get("vendor") or "")
        previous = predecessors.get((project, session_id))
        previous_id = previous[0] if previous else ""
        gap_hours = previous[1] if previous else math.nan
        previous_vendor = previous[2] if previous else ""
        prior_paths = touched.get((project, previous_id), set()) if previous else set()
        prior_mutations = (
            mutated.get((project, previous_id), set()) if previous else set()
        )
        meta_row = meta_lookup[(project, session_id)]
        for n_prefix in (5, 10, 20):
            prefix = seq[: min(n_prefix, len(seq))]
            tags = [
                startup_call_tags(event, prior_paths, prior_mutations) for event in prefix
            ]
            row = {
                "project": project,
                "session_id": session_id,
                "vendor": vendor,
                "n_prefix": n_prefix,
                "observed_prefix_calls": len(prefix),
                "complete_prefix": len(seq) >= n_prefix,
                "previous_session_id": previous_id,
                "previous_vendor": previous_vendor,
                "predecessor_available": bool(previous),
                "unique_worktree": meta_row.worktree_count == 1,
                "gap_hours": gap_hours,
                "gap_bin": gap_bin(gap_hours) if previous else "",
            }
            for tag in (
                "instruction",
                "root_readme",
                "git_strict",
                "git_broad",
                "prior_reread",
                "prior_mutation_reread",
                "orientation",
                "narrow",
                "extended",
                "broad",
            ):
                row[f"{tag}_calls"] = sum(x[tag] for x in tags)
                row[f"{tag}_share"] = row[f"{tag}_calls"] / len(prefix)
            rows.append(row)
            if n_prefix == 10:
                for event, event_tags in zip(prefix, tags):
                    detail_rows.append(
                        {
                            "project": project,
                            "session_id": session_id,
                            "vendor": vendor,
                            "ordinal": event["_ordinal"],
                            "tool_name": event.get("tool_name"),
                            "category": event.get("category"),
                            "command": event.get("command"),
                            "source_event_id": event.get("source_event_id"),
                            **event_tags,
                        }
                    )
    startup = pd.DataFrame(rows)
    details = pd.DataFrame(detail_rows)
    primary = startup[startup.n_prefix == 10].copy()
    complete_primary = primary[primary.complete_prefix].copy()
    metrics = [
        "narrow_share",
        "extended_share",
        "broad_share",
        "instruction_share",
        "root_readme_share",
        "git_strict_share",
        "prior_reread_share",
        "prior_mutation_reread_share",
        "orientation_share",
    ]
    quantiles = quantile_table(
        complete_primary, ["project", "vendor"], metrics, id_col="session_id"
    )
    sensitivity = quantile_table(
        startup, ["project", "vendor", "n_prefix"], metrics, id_col="session_id"
    )
    gap_rows: list[dict[str, Any]] = []
    gap_source = complete_primary[complete_primary.predecessor_available].copy()
    gap_source["gap_bin"] = pd.Categorical(
        gap_source["gap_bin"], categories=GAP_ORDER, ordered=True
    )
    for keys, sub in gap_source.groupby(
        ["project", "vendor", "gap_bin"], observed=True
    ):
        project, vendor, label = keys
        clean = sub.extended_share.dropna()
        gap_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "gap_bin": label,
                "n": len(clean),
                "q25": qtile(clean, 0.25),
                "median": qtile(clean, 0.5),
                "q75": qtile(clean, 0.75),
                "p90": qtile(clean, 0.9),
            }
        )
    gap_table = pd.DataFrame(gap_rows)
    rho_rows = []
    for (project, vendor), sub in gap_source.groupby(["project", "vendor"]):
        clean = sub[["gap_hours", "extended_share"]].dropna()
        if len(clean) >= 10 and clean.gap_hours.nunique() >= 2:
            rho, pvalue = spearmanr(clean.gap_hours, clean.extended_share)
        else:
            rho, pvalue = math.nan, math.nan
        rho_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "n": len(clean),
                "spearman_rho": rho,
                "pvalue_descriptive": pvalue,
            }
        )
    rho = pd.DataFrame(rho_rows)
    return {
        "sessions": startup,
        "details_n10": details,
        "quantiles_n10": quantiles,
        "sensitivity": sensitivity,
        "gap_bins": gap_table,
        "gap_spearman": rho,
    }


def save_startup_plots(startup: dict[str, pd.DataFrame]) -> None:
    primary = startup["sessions"]
    primary = primary[
        (primary.n_prefix == 10) & primary.complete_prefix.astype(bool)
    ]
    fig, axes = plt.subplots(3, 2, figsize=(14, 14), constrained_layout=True)
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = primary[primary.project == project]
        vendors = sorted(sub.vendor.unique())
        values = [
            sub[sub.vendor == vendor].extended_share.dropna().to_numpy()
            for vendor in vendors
        ]
        if values:
            box = ax.boxplot(values, labels=vendors, patch_artist=True, showfliers=False)
            for patch, vendor in zip(box["boxes"], vendors):
                patch.set_facecolor(VENDOR_COLORS.get(vendor, "#999999"))
                patch.set_alpha(0.45)
            for x, (vendor, vals) in enumerate(zip(vendors, values), 1):
                jitter = np.linspace(-0.12, 0.12, len(vals)) if len(vals) else []
                ax.scatter(
                    np.full(len(vals), x) + jitter,
                    vals,
                    s=10,
                    alpha=0.35,
                    color=VENDOR_COLORS.get(vendor, "#666666"),
                )
        ax.set_title(project)
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("Extended startup-context proxy (first 10 calls)")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Startup reconstruction tax: session-level distributions", fontsize=15)
    fig.savefig(FIGURES / "02_startup_tax_distributions.png", dpi=180)
    plt.close(fig)

    gap = startup["gap_bins"]
    fig, axes = plt.subplots(3, 2, figsize=(15, 14), sharex=True, constrained_layout=True)
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = gap[gap.project == project]
        for vendor in sorted(sub.vendor.unique()):
            v = sub[sub.vendor == vendor].copy()
            order = {label: i for i, label in enumerate(GAP_ORDER)}
            v["_x"] = v.gap_bin.map(order)
            v = v.sort_values("_x")
            x = v["_x"].to_numpy(dtype=float)
            med = v["median"].to_numpy(dtype=float)
            q1 = v["q25"].to_numpy(dtype=float)
            q3 = v["q75"].to_numpy(dtype=float)
            color = VENDOR_COLORS.get(vendor, "#666666")
            ax.plot(x, med, marker="o", label=vendor, color=color)
            ax.fill_between(x, q1, q3, color=color, alpha=0.13)
            for xi, yi, n in zip(x, med, v["n"]):
                ax.annotate(f"n={int(n)}", (xi, yi), xytext=(0, 6), textcoords="offset points",
                            ha="center", fontsize=6, color=color)
        ax.set_title(project)
        ax.set_ylim(-0.02, 1.02)
        ax.grid(axis="y", alpha=0.25)
        ax.set_xticks(np.arange(len(GAP_ORDER)), GAP_ORDER, rotation=35, ha="right")
        ax.set_ylabel("Median startup-tax share")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.01),
            ncol=3,
            frameon=False,
        )
    fig.suptitle(
        "Startup tax vs. gap to latest completed same-worktree session (median and IQR)",
        fontsize=15,
    )
    fig.savefig(FIGURES / "02_startup_tax_vs_gap.png", dpi=180)
    plt.close(fig)


STRICT_STATE_WORDS = {
    "todo",
    "todos",
    "task",
    "tasks",
    "state",
    "status",
    "progress",
    "tracker",
    "worklog",
    "plan",
}
BROAD_STATE_WORDS = {
    "plan",
    "plans",
    "checklist",
    "roadmap",
    "verdict",
    "audit",
    "followup",
}
KNOWN_RESEARCH_HARNESS = {
    "docs/idea-story.md",
    "docs/evaluation.md",
    "docs/user-instruction.md",
}


def bookkeeping_kind(path: str, *, broad: bool = False) -> str:
    lower = clean_path(path).lower()
    name = Path(lower).name
    parts = [p for p in lower.split("/") if p]
    words = set(re.findall(r"[a-z0-9]+", Path(name).stem))
    if name in {"claude.md", "agents.md", "gemini.md"}:
        return "instruction"
    if name == "skill.md" or "skills" in parts:
        return "skill"
    if name == "memory.md" or "memory" in parts or ".memory" in parts:
        return "memory"
    relative_candidates = {lower}
    for marker in ("/docs/",):
        if marker in lower:
            relative_candidates.add("docs/" + lower.split(marker, 1)[1])
    if relative_candidates.intersection(KNOWN_RESEARCH_HARNESS):
        return "experiment_status"
    doc_like = Path(name).suffix in {".md", ".txt", ".json", ".yaml", ".yml", ""}
    if doc_like and words.intersection(STRICT_STATE_WORDS):
        if "experiment" in words or "claim" in words or "results" in words:
            return "experiment_status"
        return "task_plan_status"
    if broad and doc_like and words.intersection(BROAD_STATE_WORDS):
        return "broad_process_doc"
    return ""


def is_project_path(path: str, project: str) -> bool:
    if not path.startswith("/"):
        return True
    lower = path.lower()
    if "/workspace/" not in lower:
        return False
    token = project.lower().replace(".dev", "")
    if project == "agentsight":
        return "agentsight" in lower
    return token in lower


def analyze_bookkeeping(corpus: Corpus) -> dict[str, pd.DataFrame]:
    call_rows: list[dict[str, Any]] = []
    access_rows: list[dict[str, Any]] = []
    for event in corpus.events:
        project = str(event["_project"])
        all_path_accesses = {
            (item["path"], item["access"]) for item in event["_action_accesses"]
        }
        all_path_accesses.update(
            (item["path"], item["access"]) for item in event["_source_accesses"]
        )
        strict_kinds = {
            bookkeeping_kind(path)
            for path, _ in all_path_accesses
            if bookkeeping_kind(path)
        }
        broad_kinds = {
            bookkeeping_kind(path, broad=True)
            for path, _ in all_path_accesses
            if bookkeeping_kind(path, broad=True)
        }
        ordinary_in_worktree = any(
            not bookkeeping_kind(item["path"])
            for item in event["_action_accesses"]
        )
        adjusted_strict_kinds = {
            kind
            for path, _ in all_path_accesses
            for kind in [bookkeeping_kind(path)]
            if kind
            and not (
                project == "academic-writing-skills"
                and kind == "skill"
                and is_project_path(path, project)
            )
        }
        plan_tool = event.get("category") == "plan" or event.get("tool_name") == "update_plan"
        skill_invocation = bool(
            event.get("tool_name") == "Skill" or event.get("skill_name")
        )
        attributed_skill = bool(event.get("attribution_skill"))
        gross_strict = bool(strict_kinds) or plan_tool or skill_invocation
        gross_broad = bool(broad_kinds) or plan_tool or skill_invocation
        call_rows.append(
            {
                "project": project,
                "session_id": event["session_id"],
                "vendor": event["vendor"],
                "ordinal": event["_ordinal"],
                "ts_ms": event["ts_ms"],
                "source_event_id": event.get("source_event_id"),
                "event_id": event.get("id"),
                "file_bookkeeping_strict": bool(strict_kinds),
                "file_bookkeeping_broad": bool(broad_kinds),
                "plan_tool": plan_tool,
                "skill_invocation": skill_invocation,
                "attributed_skill": attributed_skill,
                "control_plane_strict": gross_strict,
                "control_plane_broad": gross_broad,
                "exclusive_bookkeeping_strict": gross_strict and not ordinary_in_worktree,
                "mixed_bookkeeping_ordinary": gross_strict and ordinary_in_worktree,
                "adjusted_control_plane_strict": (
                    bool(adjusted_strict_kinds) or plan_tool or skill_invocation
                ),
                "strict_kinds": "|".join(sorted(strict_kinds)),
                "broad_kinds": "|".join(sorted(broad_kinds)),
                "ordinary_in_worktree_target": ordinary_in_worktree,
            }
        )
        candidates: list[tuple[str, str, str, str]] = []
        for item in event["_action_accesses"]:
            candidates.append(
                (item["path"], item["access"], "action", item["artifact_id"])
            )
        action_paths = {(x[0], x[1]) for x in candidates}
        for item in event["_source_accesses"]:
            # Retain external harness paths, plus source-only project paths.
            if (
                not is_project_path(item["path"], project)
                or not event["_action_accesses"]
            ) and (item["path"], item["access"]) not in action_paths:
                candidates.append(
                    (item["path"], item["access"], "source_path", item["path"])
                )
        for path, access, layer, identity in candidates:
            strict_kind = bookkeeping_kind(path)
            broad_kind = bookkeeping_kind(path, broad=True)
            access_rows.append(
                {
                    "project": project,
                    "session_id": event["session_id"],
                    "vendor": event["vendor"],
                    "ordinal": event["_ordinal"],
                    "ts_ms": int(event["ts_ms"]),
                    "input_index": int(event["_input_index"]),
                    "source_event_id": event.get("source_event_id"),
                    "status": event.get("status"),
                    "path": path,
                    "identity": identity,
                    "layer": layer,
                    "access": access,
                    "is_read": access in ACCESS_READ,
                    "is_write": access in ACCESS_WRITE,
                    "strict_kind": strict_kind,
                    "broad_kind": broad_kind,
                    "strict_class": "bookkeeping" if strict_kind else "ordinary",
                    "broad_class": "bookkeeping" if broad_kind else "ordinary",
                    "project_path": is_project_path(path, project),
                    "primary_access": event.get("status") != "fail",
                }
            )
    calls = pd.DataFrame(call_rows)
    accesses = pd.DataFrame(access_rows)

    for col in (
        "write_followed_by_later_read",
        "same_root_opportunity",
        "h10_opportunity",
        "h50_opportunity",
        "h100_opportunity",
        "read_within_10",
        "read_within_50",
        "read_within_100",
        "next_root_opportunity",
        "read_in_next_root",
    ):
        accesses[col] = False
    accesses["first_later_read_call_distance"] = math.nan
    session_lengths = {key: len(seq) for key, seq in corpus.sessions.items()}
    meta = session_metadata(corpus)
    meta_lookup = {
        (row.project, row.session_id): row for row in meta.itertuples(index=False)
    }
    predecessors = predecessor_map(corpus, meta)
    next_candidates: dict[tuple[str, str], list[tuple[int, str]]] = collections.defaultdict(list)
    for (project, focal_session), (previous_session, _, _) in predecessors.items():
        next_candidates[(project, previous_session)].append(
            (
                int(meta_lookup[(project, focal_session)].start_ms),
                focal_session,
            )
        )
    next_root = {
        key: min(values)[1] for key, values in next_candidates.items()
    }
    primary_accesses = accesses[accesses.primary_access]
    root_read_identities = {
        (project, session_id): set(
            sub.loc[sub.is_read, "identity"].astype(str)
        )
        for (project, session_id), sub in primary_accesses.groupby(
            ["project", "session_id"]
        )
    }
    for (project, session_id, identity), idx in primary_accesses.groupby(
        ["project", "session_id", "identity"]
    ).groups.items():
        ordered = accesses.loc[list(idx)].sort_values(["ordinal", "input_index"])
        read_ordinals = sorted(
            {int(row.ordinal) for row in ordered.itertuples() if row.is_read}
        )
        total_calls = session_lengths[(project, session_id)]
        for row_idx, row in ordered[ordered.is_write].iterrows():
            later = [ordinal for ordinal in read_ordinals if ordinal > int(row.ordinal)]
            remaining = total_calls - int(row.ordinal)
            accesses.loc[row_idx, "same_root_opportunity"] = remaining > 0
            for horizon in (10, 50, 100):
                observed_read = any(
                    x <= int(row.ordinal) + horizon for x in later
                )
                eligible = remaining >= horizon or observed_read
                accesses.loc[row_idx, f"h{horizon}_opportunity"] = eligible
                accesses.loc[row_idx, f"read_within_{horizon}"] = bool(
                    observed_read
                )
            if later:
                accesses.loc[row_idx, "write_followed_by_later_read"] = True
                accesses.loc[row_idx, "first_later_read_call_distance"] = (
                    later[0] - int(row.ordinal)
                )
            successor = next_root.get((project, session_id))
            if successor:
                accesses.loc[row_idx, "next_root_opportunity"] = True
                accesses.loc[row_idx, "read_in_next_root"] = (
                    str(identity)
                    in root_read_identities.get((project, successor), set())
                )

    stratum_rows: list[dict[str, Any]] = []
    for (project, vendor), call_sub in calls.groupby(["project", "vendor"]):
        access_sub = accesses[
            (accesses.project == project)
            & (accesses.vendor == vendor)
            & (accesses.project_path | (accesses.strict_kind != ""))
            & accesses.primary_access
        ]
        row: dict[str, Any] = {
            "project": project,
            "vendor": vendor,
            "calls": len(call_sub),
            "file_bookkeeping_calls_strict": int(call_sub.file_bookkeeping_strict.sum()),
            "file_bookkeeping_share_strict": float(call_sub.file_bookkeeping_strict.mean()),
            "control_plane_calls_strict": int(call_sub.control_plane_strict.sum()),
            "control_plane_share_strict": float(call_sub.control_plane_strict.mean()),
            "control_plane_calls_broad": int(call_sub.control_plane_broad.sum()),
            "control_plane_share_broad": float(call_sub.control_plane_broad.mean()),
            "exclusive_bookkeeping_calls_strict": int(
                call_sub.exclusive_bookkeeping_strict.sum()
            ),
            "exclusive_bookkeeping_share_strict": float(
                call_sub.exclusive_bookkeeping_strict.mean()
            ),
            "mixed_bookkeeping_ordinary_calls": int(
                call_sub.mixed_bookkeeping_ordinary.sum()
            ),
            "adjusted_control_plane_share_strict": float(
                call_sub.adjusted_control_plane_strict.mean()
            ),
            "plan_tool_calls": int(call_sub.plan_tool.sum()),
            "skill_invocations": int(call_sub.skill_invocation.sum()),
            "skill_attributed_calls": int(call_sub.attributed_skill.sum()),
        }
        for cls in ("bookkeeping", "ordinary"):
            sub = access_sub[access_sub.strict_class == cls]
            reads = int(sub.is_read.sum())
            writes = int(sub.is_write.sum())
            write_sub = sub[sub.is_write]
            row[f"{cls}_reads"] = reads
            row[f"{cls}_writes"] = writes
            row[f"{cls}_write_read_ratio"] = writes / reads if reads else math.nan
            row[f"{cls}_written_revisit_share"] = (
                float(
                    write_sub[write_sub.h50_opportunity].read_within_50.mean()
                )
                if int(write_sub.h50_opportunity.sum())
                else math.nan
            )
            row[f"{cls}_h50_eligible_writes"] = int(write_sub.h50_opportunity.sum())
            row[f"{cls}_unique_paths"] = int(sub.path.nunique())
        stratum_rows.append(row)
    strata = pd.DataFrame(stratum_rows)

    file_rows: list[dict[str, Any]] = []
    file_source = accesses[
        (accesses.project_path | (accesses.strict_kind != ""))
        & accesses.primary_access
    ]
    for (project, vendor, path), sub in file_source.groupby(["project", "vendor", "path"]):
        reads = int(sub.is_read.sum())
        writes = int(sub.is_write.sum())
        write_sub = sub[sub.is_write]
        strict_kind = dominant(sub.strict_kind.astype(str))
        broad_kind = dominant(sub.broad_kind.astype(str))
        file_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "path": path,
                "strict_kind": strict_kind,
                "broad_kind": broad_kind,
                "strict_class": "bookkeeping" if strict_kind else "ordinary",
                "broad_class": "bookkeeping" if broad_kind else "ordinary",
                "reads": reads,
                "writes": writes,
                "accesses": reads + writes,
                "write_read_ratio": writes / reads if reads else math.nan,
                "written_with_zero_reads": bool(writes and not reads),
                "write_revisit_share": (
                    float(
                        write_sub[write_sub.h50_opportunity].read_within_50.mean()
                    )
                    if int(write_sub.h50_opportunity.sum())
                    else math.nan
                ),
                "h50_eligible_writes": int(write_sub.h50_opportunity.sum()),
            }
        )
    files = pd.DataFrame(file_rows)
    file_quantiles = quantile_table(
        files[files.writes > 0],
        ["project", "vendor", "strict_class"],
        ["reads", "writes", "write_read_ratio", "write_revisit_share"],
        id_col="path",
    )
    zero_read_rows = []
    for keys, sub in files[files.writes > 0].groupby(
        ["project", "vendor", "strict_class"]
    ):
        zero_read_rows.append(
            {
                "project": keys[0],
                "vendor": keys[1],
                "strict_class": keys[2],
                "written_files": len(sub),
                "zero_read_written_files": int(sub.written_with_zero_reads.sum()),
                "zero_read_written_share": float(sub.written_with_zero_reads.mean()),
            }
        )
    zero_read = pd.DataFrame(zero_read_rows)
    top_files = (
        files[files.strict_class == "bookkeeping"]
        .sort_values(["accesses", "writes"], ascending=False)
        .head(100)
        .copy()
    )
    kind_summary = (
        file_source.assign(
            display_kind=lambda x: x.strict_kind.where(
                x.strict_kind != "", "ordinary"
            )
        )
        .groupby(["project", "vendor", "display_kind"])
        .agg(
            accesses=("path", "size"),
            reads=("is_read", "sum"),
            writes=("is_write", "sum"),
            unique_paths=("path", "nunique"),
        )
        .reset_index()
    )
    coverage = pd.DataFrame(
        [
            {
                "event_rows": len(corpus.events),
                "events_with_actions": sum(bool(e["_action_accesses"]) for e in corpus.events),
                "events_with_source_paths": sum(
                    bool(e["_source_accesses"]) for e in corpus.events
                ),
                "events_source_only": sum(
                    bool(e["_source_accesses"]) and not bool(e["_action_accesses"])
                    for e in corpus.events
                ),
                "action_access_rows": int((accesses.layer == "action").sum()),
                "external_or_source_only_rows": int(
                    (accesses.layer == "source_path").sum()
                ),
            }
        ]
    )
    revisit_rows = []
    write_source = file_source[file_source.is_write]
    for (project, vendor, cls), sub in write_source.groupby(
        ["project", "vendor", "strict_class"]
    ):
        row = {
            "project": project,
            "vendor": vendor,
            "strict_class": cls,
            "writes": len(sub),
            "same_root_opportunities": int(sub.same_root_opportunity.sum()),
            "same_root_revisit_share": (
                float(
                    sub[sub.same_root_opportunity]
                    .write_followed_by_later_read.mean()
                )
                if int(sub.same_root_opportunity.sum())
                else math.nan
            ),
            "next_root_opportunities": int(sub.next_root_opportunity.sum()),
            "next_root_revisit_share": (
                float(sub[sub.next_root_opportunity].read_in_next_root.mean())
                if int(sub.next_root_opportunity.sum())
                else math.nan
            ),
            "first_read_distance_median": qtile(
                sub.first_later_read_call_distance, 0.5
            ),
            "first_read_distance_q25": qtile(
                sub.first_later_read_call_distance, 0.25
            ),
            "first_read_distance_q75": qtile(
                sub.first_later_read_call_distance, 0.75
            ),
        }
        for horizon in (10, 50, 100):
            eligible = sub[sub[f"h{horizon}_opportunity"]]
            row[f"h{horizon}_opportunities"] = len(eligible)
            row[f"h{horizon}_revisit_share"] = (
                float(eligible[f"read_within_{horizon}"].mean())
                if len(eligible)
                else math.nan
            )
        revisit_rows.append(row)
    revisit_summary = pd.DataFrame(revisit_rows)
    return {
        "calls": calls,
        "accesses": accesses,
        "strata": strata,
        "files": files,
        "file_quantiles": file_quantiles,
        "zero_read": zero_read,
        "top_files": top_files,
        "kind_summary": kind_summary,
        "coverage": coverage,
        "revisit_summary": revisit_summary,
    }


def save_bookkeeping_plots(book: dict[str, pd.DataFrame]) -> None:
    strata = book["strata"]
    metrics = [
        ("control_plane_share_strict", "Strict control-plane call share"),
        ("control_plane_share_broad", "Broad sensitivity call share"),
    ]
    fig, axes = plt.subplots(3, 2, figsize=(15, 14), constrained_layout=True)
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = strata[strata.project == project].sort_values("vendor")
        x = np.arange(len(sub))
        width = 0.35
        for offset, (metric, label) in zip((-width / 2, width / 2), metrics):
            ax.bar(x + offset, sub[metric], width, label=label)
        ax.set_xticks(x, sub.vendor)
        ax.set_ylim(0, max(0.05, min(1.0, float(sub[[m[0] for m in metrics]].max().max()) * 1.25)))
        ax.set_title(project)
        ax.set_ylabel("Share of all tool calls")
        ax.grid(axis="y", alpha=0.25)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.01), ncol=2,
               frameon=False)
    fig.suptitle("Harness/bookkeeping overhead proxies by project × vendor", fontsize=15)
    fig.savefig(FIGURES / "03_bookkeeping_call_share.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(3, 2, figsize=(15, 14), constrained_layout=True)
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = strata[strata.project == project].sort_values("vendor")
        labels = []
        values = []
        colors = []
        for _, row in sub.iterrows():
            for cls, color in (("bookkeeping", "#D55E00"), ("ordinary", "#0072B2")):
                labels.append(f"{row.vendor[:2]}-{cls[:1].upper()}")
                values.append(row[f"{cls}_write_read_ratio"])
                colors.append(color)
        ax.bar(np.arange(len(values)), values, color=colors, alpha=0.75)
        ax.set_xticks(np.arange(len(values)), labels, rotation=40, ha="right")
        ax.set_yscale("log")
        ax.set_title(project)
        ax.set_ylabel("Write/read ratio (log scale)")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Bookkeeping vs ordinary project files: aggregate write/read ratio", fontsize=15
    )
    fig.savefig(FIGURES / "03_bookkeeping_write_read_ratio.png", dpi=180)
    plt.close(fig)

    files = book["files"]
    fig, axes = plt.subplots(3, 2, figsize=(15, 14), constrained_layout=True)
    for ax, project in zip(axes.flat, PROJECT_ORDER):
        sub = files[(files.project == project) & (files.writes > 0)]
        data = []
        labels = []
        colors = []
        for vendor in sorted(sub.vendor.unique()):
            for cls, color in (("bookkeeping", "#D55E00"), ("ordinary", "#0072B2")):
                vals = sub[(sub.vendor == vendor) & (sub.strict_class == cls)][
                    "write_revisit_share"
                ].dropna()
                if len(vals):
                    data.append(vals.to_numpy())
                    labels.append(f"{vendor[:2]}-{cls[:1].upper()}")
                    colors.append(color)
        if data:
            box = ax.boxplot(data, labels=labels, patch_artist=True, showfliers=False)
            for patch, color in zip(box["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.45)
        ax.set_title(project)
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("Per-file share of writes later read")
        ax.tick_params(axis="x", rotation=40)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "Post-write revisit distributions (B=bookkeeping, O=ordinary)", fontsize=15
    )
    fig.savefig(FIGURES / "03_bookkeeping_revisit_distributions.png", dpi=180)
    plt.close(fig)


def normalized_command(command: str | None) -> str:
    text = " ".join(str(command or "").strip().lower().split())
    text = re.sub(r"/tmp/[a-z0-9_.\-/]+", "/tmp/<tmp>", text)
    text = re.sub(r"\b[0-9a-f]{16,}\b", "<id>", text)
    return text[:1000]


def patch_target_paths(command: str | None) -> list[str]:
    return sorted(
        {
            clean_path(path)
            for path in re.findall(
                r"^\*\*\* (?:Update|Add|Delete) File: (.+)$",
                str(command or ""),
                flags=re.MULTILINE,
            )
        }
    )


def poll_session_id(event: dict[str, Any]) -> str:
    if event.get("tool_name") not in {"write_stdin", "wait"}:
        return ""
    try:
        payload = json.loads(str(event.get("command") or ""))
    except json.JSONDecodeError:
        return ""
    return str(payload.get("session_id") or payload.get("cell_id") or "")


def strict_target(event: dict[str, Any]) -> tuple[str, str]:
    actions = sorted(
        {
            f"{item['artifact_id']}:{item['access']}"
            for item in event["_action_accesses"]
        }
    )
    if actions:
        return (
            f"{event.get('category')}|actions|" + "|".join(actions),
            "actions",
        )
    sources = sorted(
        {f"{item['path']}:{item['access']}" for item in event["_source_accesses"]}
    )
    if sources:
        return (
            f"{event.get('category')}|source_paths|" + "|".join(sources),
            "source_paths",
        )
    exact_command = " ".join(str(event.get("command") or "").split())
    return (
        f"{event.get('tool_name')}|{event.get('command_name')}|{exact_command}",
        "command_fallback",
    )


def command_family(event: dict[str, Any]) -> str:
    command = normalized_command(event.get("command"))
    if event.get("effect") == "test":
        return "validation"
    if re.search(r"(?:^|\s)(rg|grep|find)\b", command):
        return "search"
    if re.search(r"(?:^|\s)(gh|gitlab|curl|wget)\b", command) or event.get(
        "category"
    ) == "network":
        return "remote"
    match = re.search(
        r"(cargo|npm|pnpm|yarn|pytest|python3?|make|cmake|go|git|gh|rg|grep|find|sed|cat)\b",
        command,
    )
    return match.group(1) if match else str(event.get("tool_name") or event.get("category"))


def target_object(event: dict[str, Any]) -> str:
    poll_id = poll_session_id(event)
    if poll_id:
        return f"poll|{event.get('tool_name')}|{poll_id}"
    paths = sorted({item["path"] for item in event["_action_accesses"]})
    if not paths:
        paths = sorted({item["path"] for item in event["_source_accesses"]})
    if not paths:
        paths = patch_target_paths(event.get("command"))
    if event.get("category") == "edit" and paths:
        return "edit|" + "|".join(paths)
    if event.get("effect") == "test":
        return "validation"
    if paths:
        return f"{event.get('category')}|" + "|".join(paths)
    return f"{event.get('category')}|{command_family(event)}"


def failure_pattern(event: dict[str, Any]) -> str:
    if event.get("category") == "edit":
        return "repeated_edit"
    if poll_session_id(event):
        return "process_polling"
    if event.get("effect") == "test":
        return "validation_retry"
    family = command_family(event)
    if family == "search":
        return "search_miss"
    if family == "remote":
        return "remote_lookup"
    if event.get("category") == "read":
        return "file_read"
    return "other"


def classify_chain_outcome(
    seq: list[dict[str, Any]],
    end_idx: int,
    signature: str,
    obj: str,
    horizon: int | None,
) -> tuple[str, int | None, dict[str, Any] | None]:
    stop = len(seq) if horizon is None else min(len(seq), end_idx + horizon)
    future = list(enumerate(seq[end_idx:stop], start=end_idx))
    exact_ok = [
        (idx, event)
        for idx, event in future
        if strict_target(event)[0] == signature and event.get("status") == "ok"
    ]
    if exact_ok:
        idx, event = exact_ok[0]
        return "exact_target_recovered", idx, event
    exact_observed = [
        (idx, event)
        for idx, event in future
        if strict_target(event)[0] == signature and event.get("status") == "observed"
    ]
    if exact_observed:
        idx, event = exact_observed[0]
        return "exact_target_observed_unresolved", idx, event
    exact_failed = [
        (idx, event)
        for idx, event in future
        if strict_target(event)[0] == signature and event.get("status") == "fail"
    ]
    if exact_failed:
        idx, event = exact_failed[0]
        return "exact_target_failed_again", idx, event
    modified = [
        (idx, event)
        for idx, event in future
        if target_object(event) == obj and strict_target(event)[0] != signature
    ]
    if modified:
        idx, event = modified[0]
        return "modified_route_observed", idx, event
    return "no_observed_return", None, None


def analyze_failures(corpus: Corpus) -> dict[str, pd.DataFrame]:
    chain_rows: list[dict[str, Any]] = []
    call_rows: list[dict[str, Any]] = []
    cluster_rows: list[dict[str, Any]] = []
    streams: dict[tuple[str, str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for event in corpus.events:
        streams[
            (
                str(event["_project"]),
                str(event["session_id"]),
                str(event.get("source_stream_id") or ""),
            )
        ].append(event)
    for (project, session_id, stream_id), seq in streams.items():
        seq.sort(
            key=lambda e: (
                int(e.get("source_tool_ordinal") or 0),
                int(e["ts_ms"]),
                str(e.get("id") or ""),
            )
        )
        for stream_ordinal, event in enumerate(seq, 1):
            event["_stream_ordinal"] = stream_ordinal
        vendor = str(seq[0].get("vendor") or "")
        i = 0
        while i < len(seq):
            event = seq[i]
            if event.get("status") != "fail":
                i += 1
                continue
            signature, key_source = strict_target(event)
            j = i + 1
            while (
                j < len(seq)
                and seq[j].get("status") == "fail"
                and strict_target(seq[j])[0] == signature
            ):
                j += 1
            length = j - i
            if length >= 3:
                obj = target_object(event)
                outcomes = {}
                for label, horizon in (("full", None), ("next10", 10), ("next50", 50)):
                    outcomes[label] = classify_chain_outcome(
                        seq, j, signature, obj, horizon
                    )
                outcome, recovery_idx, recovery_event = outcomes["full"]
                chain_id = f"{project}:{session_id}:{stream_id}:{i + 1}-{j}"
                recovery_after = recovery_idx - j + 1 if recovery_idx is not None else math.nan
                episode_span = (
                    recovery_idx - i + 1 if recovery_idx is not None else length
                )
                chain_rows.append(
                    {
                        "chain_id": chain_id,
                        "project": project,
                        "vendor": vendor,
                        "session_id": session_id,
                        "source_stream_id": stream_id,
                        "start_stream_ordinal": i + 1,
                        "end_stream_ordinal": j,
                        "start_root_ordinal": event["_ordinal"],
                        "end_root_ordinal": seq[j - 1]["_ordinal"],
                        "length": length,
                        "pattern": failure_pattern(event),
                        "target_signature": signature,
                        "target_key_source": key_source,
                        "target_object": obj,
                        "outcome": outcome,
                        "outcome_next10": outcomes["next10"][0],
                        "outcome_next50": outcomes["next50"][0],
                        "exact_failed_return_full": (
                            outcomes["full"][0] == "exact_target_failed_again"
                        ),
                        "exact_failed_return_next10": (
                            outcomes["next10"][0] == "exact_target_failed_again"
                        ),
                        "exact_failed_return_next50": (
                            outcomes["next50"][0] == "exact_target_failed_again"
                        ),
                        "recovery_stream_ordinal": (
                            recovery_event["_stream_ordinal"] if recovery_event else math.nan
                        ),
                        "recovery_root_ordinal": (
                            recovery_event["_ordinal"] if recovery_event else math.nan
                        ),
                        "calls_after_chain_to_outcome": recovery_after,
                        "episode_span_calls": episode_span,
                        "representative_command": str(event.get("command") or "")[:500],
                        "representative_tool": event.get("tool_name"),
                        "source_event_id": event.get("source_event_id"),
                        "recovery_command": (
                            str(recovery_event.get("command") or "")[:500]
                            if recovery_event
                            else ""
                        ),
                        "recovery_tool": recovery_event.get("tool_name") if recovery_event else "",
                    }
                )
                for local_idx in range(i, j):
                    call = seq[local_idx]
                    call_rows.append(
                        {
                            "chain_id": chain_id,
                            "project": project,
                            "vendor": vendor,
                            "session_id": session_id,
                            "source_stream_id": stream_id,
                            "stream_ordinal": call["_stream_ordinal"],
                            "root_ordinal": call["_ordinal"],
                            "event_id": call.get("id"),
                            "tool_name": call.get("tool_name"),
                            "category": call.get("category"),
                            "effect": call.get("effect"),
                            "status": call.get("status"),
                            "command": call.get("command"),
                            "source_event_id": call.get("source_event_id"),
                        }
                    )
            i = j

        # Sensitivity: same-target failures separated by at most two calls.
        failures_by_target: dict[str, list[int]] = collections.defaultdict(list)
        for idx, event in enumerate(seq):
            if event.get("status") == "fail":
                failures_by_target[strict_target(event)[0]].append(idx)
        for signature, indices in failures_by_target.items():
            run = [indices[0]]
            for idx in indices[1:]:
                if idx - run[-1] <= 3:
                    run.append(idx)
                else:
                    if len(run) >= 3:
                        cluster_rows.append(
                            {
                                "project": project,
                                "vendor": vendor,
                                "session_id": session_id,
                                "source_stream_id": stream_id,
                                "first_stream_ordinal": run[0] + 1,
                                "last_stream_ordinal": run[-1] + 1,
                                "failures": len(run),
                                "span_calls": run[-1] - run[0] + 1,
                                "target_signature": signature,
                                "pattern": failure_pattern(seq[run[0]]),
                            }
                        )
                    run = [idx]
            if len(run) >= 3:
                cluster_rows.append(
                    {
                        "project": project,
                        "vendor": vendor,
                        "session_id": session_id,
                        "source_stream_id": stream_id,
                        "first_stream_ordinal": run[0] + 1,
                        "last_stream_ordinal": run[-1] + 1,
                        "failures": len(run),
                        "span_calls": run[-1] - run[0] + 1,
                        "target_signature": signature,
                        "pattern": failure_pattern(seq[run[0]]),
                    }
                )
    chains = pd.DataFrame(chain_rows)
    chain_calls = pd.DataFrame(call_rows)
    clusters = pd.DataFrame(cluster_rows)
    if len(chains):
        pattern_summary = (
            chains.groupby(["pattern", "outcome"])
            .agg(chains=("chain_id", "count"), failed_calls=("length", "sum"))
            .reset_index()
        )
        stratum = (
            chains.groupby(["project", "vendor"])
            .agg(
                chains=("chain_id", "count"),
                failed_calls_in_chains=("length", "sum"),
                median_length=("length", "median"),
                p90_length=("length", lambda x: x.quantile(0.9)),
                max_length=("length", "max"),
            )
            .reset_index()
        )
    else:
        pattern_summary = pd.DataFrame()
        stratum = pd.DataFrame()
    corpus_counts = collections.Counter(
        (event["_project"], event["vendor"]) for event in corpus.events
    )
    if len(stratum):
        stratum["all_calls"] = [
            corpus_counts[(row.project, row.vendor)] for row in stratum.itertuples()
        ]
        stratum["chain_call_share"] = (
            stratum.failed_calls_in_chains / stratum.all_calls
        )
    cases = (
        chains.sort_values(
            ["pattern", "length", "start_stream_ordinal"],
            ascending=[True, False, True],
        )
        .drop_duplicates(["pattern", "session_id"])
        .groupby("pattern", group_keys=False)
        .head(3)
        if len(chains)
        else pd.DataFrame()
    )
    return {
        "chains": chains,
        "chain_calls": chain_calls,
        "interleaved_clusters": clusters,
        "pattern_summary": pattern_summary,
        "stratum": stratum,
        "cases": cases,
    }


def save_failure_plot(failures: dict[str, pd.DataFrame]) -> None:
    chains = failures["chains"]
    stratum = failures["stratum"]
    if chains.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    lengths = sorted(chains["length"].unique())
    for pattern in sorted(chains.pattern.unique()):
        vals = chains[chains.pattern == pattern]["length"].to_numpy()
        ccdf = [float((vals >= x).mean()) for x in lengths]
        axes[0].step(lengths, ccdf, where="post", label=f"{pattern} (n={len(vals)})")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Consecutive failed calls")
    axes[0].set_ylabel("CCDF")
    axes[0].set_title("Chain-length distribution")
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=7, frameon=False)

    outcome = chains.groupby(["pattern", "outcome"]).size().unstack(fill_value=0)
    outcome = outcome.div(outcome.sum(axis=1), axis=0)
    bottom = np.zeros(len(outcome))
    outcome_colors = {
        "exact_target_recovered": "#009E73",
        "modified_route_observed": "#56B4E9",
        "no_observed_return": "#D55E00",
        "exact_target_observed_unresolved": "#CC79A7",
        "exact_target_failed_again": "#F0E442",
    }
    for name in (
        "exact_target_recovered",
        "modified_route_observed",
        "no_observed_return",
        "exact_target_observed_unresolved",
        "exact_target_failed_again",
    ):
        if name not in outcome:
            continue
        axes[1].bar(
            np.arange(len(outcome)),
            outcome[name],
            bottom=bottom,
            label=name,
            color=outcome_colors[name],
        )
        bottom += outcome[name].to_numpy()
    axes[1].set_xticks(np.arange(len(outcome)), outcome.index, rotation=35, ha="right")
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("Share of chains")
    axes[1].set_title("Recorded outcome")
    axes[1].legend(fontsize=7, frameon=False)
    axes[1].grid(axis="y", alpha=0.25)

    labels = [f"{r.project}\n{r.vendor}" for r in stratum.itertuples()]
    axes[2].barh(np.arange(len(stratum)), stratum.chain_call_share * 100, color="#0072B2")
    axes[2].set_yticks(np.arange(len(stratum)), labels, fontsize=7)
    axes[2].invert_yaxis()
    axes[2].set_xlabel("% of all calls in strict chains")
    axes[2].set_title("Local call burden")
    axes[2].grid(axis="x", alpha=0.25)
    fig.suptitle("Strict same-target consecutive failure chains (length ≥3)", fontsize=15)
    fig.savefig(FIGURES / "04_failure_cascades.png", dpi=180)
    plt.close(fig)


def corpus_tables(corpus: Corpus, meta: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rows = []
    for (project, vendor), events in pd.DataFrame(
        [
            {
                "project": e["_project"],
                "vendor": e["vendor"],
                "status": e["status"],
                "category": e["category"],
                "session_id": e["session_id"],
                "file_actions": len(e.get("actions") or []),
            }
            for e in corpus.events
        ]
    ).groupby(["project", "vendor"]):
        rows.append(
            {
                "project": project,
                "vendor": vendor,
                "sessions": events.session_id.nunique(),
                "tool_calls": len(events),
                "file_actions": int(events.file_actions.sum()),
                "recorded_fail_calls": int((events.status == "fail").sum()),
                "observed_status_calls": int((events.status == "observed").sum()),
                "read_calls": int((events.category == "read").sum()),
                "edit_calls": int((events.category == "edit").sum()),
                "shell_calls": int((events.category == "shell").sum()),
            }
        )
    summary = pd.DataFrame(rows)
    length_rows = []
    for (project, vendor), sub in meta.groupby(["project", "vendor"]):
        calls = sub.calls
        length_rows.append(
            {
                "project": project,
                "vendor": vendor,
                "sessions": len(sub),
                "min": int(calls.min()),
                "q25": qtile(calls, 0.25),
                "median": qtile(calls, 0.5),
                "q75": qtile(calls, 0.75),
                "p90": qtile(calls, 0.9),
                "p95": qtile(calls, 0.95),
                "p99": qtile(calls, 0.99),
                "max": int(calls.max()),
                "sessions_ge_9": int((calls >= 9).sum()),
                "sessions_ge_30": int((calls >= 30).sum()),
            }
        )
    full_grid = pd.MultiIndex.from_product(
        [PROJECT_ORDER, ("claude", "codex", "gemini")],
        names=["project", "vendor"],
    ).to_frame(index=False)
    coverage_grid = full_grid.merge(summary, on=["project", "vendor"], how="left")
    for column in (
        "sessions",
        "tool_calls",
        "file_actions",
        "recorded_fail_calls",
        "observed_status_calls",
        "read_calls",
        "edit_calls",
        "shell_calls",
    ):
        coverage_grid[column] = coverage_grid[column].fillna(0).astype(int)
    return {
        "summary": summary,
        "coverage_grid": coverage_grid,
        "session_lengths": pd.DataFrame(length_rows),
    }


def save_df(frame: pd.DataFrame, name: str, *, gzip: bool = False) -> None:
    path = RAW / name
    frame.to_csv(path, index=False, compression="gzip" if gzip else None)


def serializable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if math.isnan(float(value)) else float(value)
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value)}")


def build_summary(
    corpus: Corpus,
    meta: pd.DataFrame,
    drift: dict[str, pd.DataFrame],
    startup: dict[str, pd.DataFrame],
    book: dict[str, pd.DataFrame],
    failures: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    primary_startup = startup["sessions"]
    primary_startup = primary_startup[
        (primary_startup.n_prefix == 10) & primary_startup.complete_prefix
    ]
    chains = failures["chains"]
    call_frame = book["calls"]
    access_frame = book["accesses"]
    book_writes = access_frame[
        (access_frame.strict_class == "bookkeeping")
        & access_frame.is_write
        & access_frame.primary_access
    ]
    ordinary_writes = access_frame[
        (access_frame.strict_class == "ordinary")
        & access_frame.is_write
        & access_frame.project_path
        & access_frame.primary_access
    ]
    strict_reads = int(
        (
            (access_frame.strict_class == "bookkeeping")
            & access_frame.is_read
            & access_frame.primary_access
        ).sum()
    )
    strict_writes = int(
        (
            (access_frame.strict_class == "bookkeeping")
            & access_frame.is_write
            & access_frame.primary_access
        ).sum()
    )
    ordinary_reads = int(
        (
            (access_frame.strict_class == "ordinary")
            & access_frame.is_read
            & access_frame.project_path
            & access_frame.primary_access
        ).sum()
    )
    ordinary_write_count = int(len(ordinary_writes))
    unique_calls = len({str(e.get("id")) for e in corpus.events})
    unique_call_frame = (
        call_frame.groupby("event_id", dropna=False)
        .agg(
            control_plane_strict=("control_plane_strict", "max"),
            control_plane_broad=("control_plane_broad", "max"),
            exclusive_bookkeeping_strict=("exclusive_bookkeeping_strict", "max"),
        )
        .reset_index()
    )
    unique_chain_calls = (
        failures["chain_calls"].event_id.nunique()
        if len(failures["chain_calls"])
        else 0
    )
    return {
        "corpus": {
            "projects": len({e["_project"] for e in corpus.events}),
            "project_root_memberships": len(corpus.sessions),
            "unique_session_ids": len({key[1] for key in corpus.sessions}),
            "project_event_rows": len(corpus.events),
            "unique_events": unique_calls,
            "duplicate_project_event_rows": len(corpus.events) - unique_calls,
            "file_actions": sum(len(e.get("actions") or []) for e in corpus.events),
            "vendors": dict(collections.Counter(e["vendor"] for e in corpus.events)),
        },
        "drift": {
            "session_project_pairs_ge_3": int(
                drift["all_session_phase"][["project", "session_id"]]
                .drop_duplicates()
                .shape[0]
            ),
            "session_project_pairs_ge_30": int(
                drift["curve"][["project", "session_id"]].drop_duplicates().shape[0]
            ),
        },
        "startup": {
            "sessions_with_10_calls": int(len(primary_startup)),
            "sessions_with_predecessor": int(primary_startup.predecessor_available.sum()),
            "median_narrow_proxy": float(primary_startup.narrow_share.median()),
            "median_extended_proxy": float(primary_startup.extended_share.median()),
            "q25_extended_proxy": float(primary_startup.extended_share.quantile(0.25)),
            "q75_extended_proxy": float(primary_startup.extended_share.quantile(0.75)),
            "p90_extended_proxy": float(primary_startup.extended_share.quantile(0.9)),
        },
        "bookkeeping": {
            "file_bookkeeping_calls_strict": int(call_frame.file_bookkeeping_strict.sum()),
            "file_bookkeeping_share_strict": float(call_frame.file_bookkeeping_strict.mean()),
            "control_plane_calls_strict": int(call_frame.control_plane_strict.sum()),
            "control_plane_share_strict": float(call_frame.control_plane_strict.mean()),
            "control_plane_calls_broad": int(call_frame.control_plane_broad.sum()),
            "control_plane_share_broad": float(call_frame.control_plane_broad.mean()),
            "exclusive_bookkeeping_share_strict": float(
                call_frame.exclusive_bookkeeping_strict.mean()
            ),
            "adjusted_control_plane_share_strict": float(
                call_frame.adjusted_control_plane_strict.mean()
            ),
            "unique_event_control_plane_share_strict": float(
                unique_call_frame.control_plane_strict.mean()
            ),
            "bookkeeping_reads": strict_reads,
            "bookkeeping_writes": strict_writes,
            "bookkeeping_write_read_ratio": (
                strict_writes / strict_reads if strict_reads else math.nan
            ),
            "ordinary_project_reads": ordinary_reads,
            "ordinary_project_writes": ordinary_write_count,
            "ordinary_write_read_ratio": (
                ordinary_write_count / ordinary_reads if ordinary_reads else math.nan
            ),
            "bookkeeping_write_revisit_share": (
                float(book_writes[book_writes.h50_opportunity].read_within_50.mean())
                if int(book_writes.h50_opportunity.sum())
                else math.nan
            ),
            "ordinary_write_revisit_share": (
                float(
                    ordinary_writes[
                        ordinary_writes.h50_opportunity
                    ].read_within_50.mean()
                )
                if int(ordinary_writes.h50_opportunity.sum())
                else math.nan
            ),
            "bookkeeping_h50_eligible_writes": int(book_writes.h50_opportunity.sum()),
            "ordinary_h50_eligible_writes": int(
                ordinary_writes.h50_opportunity.sum()
            ),
        },
        "failures": {
            "chains": int(len(chains)),
            "failed_calls_in_chains": int(chains.length.sum()) if len(chains) else 0,
            "strict_chain_call_share": (
                float(chains.length.sum() / len(corpus.events)) if len(chains) else 0.0
            ),
            "unique_event_chain_call_share": unique_chain_calls / unique_calls,
            "interleaved_clusters": int(len(failures["interleaved_clusters"])),
            "outcomes": (
                chains.outcome.value_counts().sort_index().to_dict() if len(chains) else {}
            ),
            "patterns": (
                chains.pattern.value_counts().sort_index().to_dict() if len(chains) else {}
            ),
        },
    }


def save_outputs(
    corpus: Corpus,
    meta: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    drift: dict[str, pd.DataFrame],
    startup: dict[str, pd.DataFrame],
    book: dict[str, pd.DataFrame],
    failures: dict[str, pd.DataFrame],
) -> None:
    save_df(tables["summary"], "corpus_by_project_vendor.csv")
    save_df(tables["coverage_grid"], "corpus_full_6x3_grid.csv")
    save_df(tables["session_lengths"], "session_length_distributions.csv")
    save_df(meta, "sessions.csv")
    eligibility = tables["coverage_grid"][["project", "vendor", "sessions", "tool_calls"]].copy()
    ge3 = (
        drift["all_session_phase"][["project", "vendor", "session_id"]]
        .drop_duplicates()
        .groupby(["project", "vendor"])
        .size()
    )
    ge30 = (
        drift["phase"][["project", "vendor", "session_id"]]
        .drop_duplicates()
        .groupby(["project", "vendor"])
        .size()
    )
    startup10 = startup["sessions"][
        (startup["sessions"].n_prefix == 10) & startup["sessions"].complete_prefix
    ]
    startup_counts = startup10.groupby(["project", "vendor"]).size()
    pred_counts = startup10[startup10.predecessor_available].groupby(
        ["project", "vendor"]
    ).size()
    book_calls = book["strata"].set_index(["project", "vendor"])[
        "control_plane_calls_strict"
    ]
    chain_counts = (
        failures["chains"].groupby(["project", "vendor"]).size()
        if len(failures["chains"])
        else pd.Series(dtype=float)
    )
    for name, series in (
        ("drift_sessions_ge3", ge3),
        ("drift_long_sessions_ge30", ge30),
        ("startup_complete_n10", startup_counts),
        ("startup_predecessor_n10", pred_counts),
        ("bookkeeping_matched_calls", book_calls),
        ("strict_failure_chains", chain_counts),
    ):
        eligibility[name] = [
            int(series.get((row.project, row.vendor), 0))
            for row in eligibility.itertuples()
        ]
    save_df(eligibility, "section_eligibility_full_6x3_grid.csv")
    for key, frame in drift.items():
        save_df(frame, f"drift_{key}.csv")
    for key, frame in startup.items():
        save_df(
            frame,
            f"startup_{key}.csv" + (".gz" if key == "details_n10" else ""),
            gzip=key == "details_n10",
        )
    for key, frame in book.items():
        save_df(
            frame,
            f"bookkeeping_{key}.csv" + (".gz" if key in {"calls", "accesses"} else ""),
            gzip=key in {"calls", "accesses"},
        )
    for key, frame in failures.items():
        save_df(frame, f"failures_{key}.csv")


def write_manifest(corpus: Corpus, summary: dict[str, Any]) -> None:
    revisions = {
        header["repository"]: header.get("revision") for header in corpus.headers
    }
    manifest = {
        "command": "python analysis.py",
        "data_directory": str(DATA.relative_to(REPO)),
        "input_files": [
            {
                "path": str(path.relative_to(REPO)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in corpus.files
        ],
        "revisions": revisions,
        "python": sys.version,
        "platform": platform.platform(),
        "libraries": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "definitions": {
            "all_session_tertile_min_calls": 3,
            "drift_primary_min_calls": 30,
            "drift_length_sensitivities": [60, 100],
            "curve_min_calls": 30,
            "startup_prefixes": [5, 10, 20],
            "startup_primary_prefix": 10,
            "recent_reedit_window_calls": 10,
            "failure_chain_min_consecutive_same_target_failures": 3,
            "interleaved_cluster_max_intervening_calls": 2,
            "root_flatten_order": [
                "ts_ms",
                "source_stream_id",
                "source_tool_ordinal",
                "id",
            ],
            "strict_failure_order": [
                "repository",
                "session_id",
                "source_stream_id",
                "source_tool_ordinal",
            ],
        },
        "summary": summary,
    }
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=serializable) + "\n"
    )


def run_analysis(corpus: Corpus, *, write: bool) -> dict[str, Any]:
    meta = session_metadata(corpus)
    tables = corpus_tables(corpus, meta)
    drift = analyze_drift(corpus)
    startup = analyze_startup(corpus, meta)
    book = analyze_bookkeeping(corpus)
    failures = analyze_failures(corpus)
    summary = build_summary(corpus, meta, drift, startup, book, failures)
    if write:
        save_outputs(corpus, meta, tables, drift, startup, book, failures)
        save_drift_plots(drift)
        save_startup_plots(startup)
        save_bookkeeping_plots(book)
        save_failure_plot(failures)
        write_manifest(corpus, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="run the full metric path on academic-writing-skills without main outputs",
    )
    args = parser.parse_args()
    ensure_dirs()
    if args.preflight:
        corpus = load_corpus({"academic-writing-skills"})
        summary = run_analysis(corpus, write=False)
        if (
            summary["corpus"]["project_event_rows"] != 948
            or summary["corpus"]["project_root_memberships"] != 17
        ):
            raise SystemExit("preflight invariant failed")
        (HERE / "preflight.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, default=serializable) + "\n"
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=serializable))
        return
    corpus = load_corpus()
    if len(corpus.events) != 181_303:
        raise SystemExit(f"expected 181303 calls, got {len(corpus.events)}")
    if len(corpus.sessions) != 551:
        raise SystemExit(f"expected 551 sessions, got {len(corpus.sessions)}")
    summary = run_analysis(corpus, write=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=serializable))


if __name__ == "__main__":
    main()
