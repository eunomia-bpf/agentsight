#!/usr/bin/env python3
"""Run R131 semantic-axis ablations over AgentFlame folded artifacts.

This checker does not rescan raw agent histories. It reads the already-generated
folded stacks and measures what each semantic axis contributes when projected
away from the same observation multiset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = REPO_ROOT / ".agentsight" / "agentflame" / "latest"
DEFAULT_LOCAL_OUT = REPO_ROOT / ".agentsight" / "agentflame" / "ablations-r131" / "summary.json"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out"

SYSTEM_BASE = (
    "project:",
    "agent:",
    "call:",
    "process:",
    "effect:",
    "path:",
    "domain:",
    "status:",
)
TOKEN_BASE = ("project:", "agent:", "model:", "kind:")


def read_folded(path: Path) -> Counter[str]:
    stacks: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, weight = line.rpartition(" ")
            if not stack or not weight.isdigit():
                raise ValueError(f"invalid folded line {path}:{line_no}: {line[:160]}")
            stacks[stack] += int(weight)
    return stacks


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def run_git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def pct(part: float | int, whole: float | int) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def frame_value(frames: list[str], prefix: str, default: str = "unknown") -> str:
    for frame in frames:
        if frame.startswith(prefix):
            return frame.split(":", 1)[1]
    return default


def project_stack(stack: str, keep_prefixes: tuple[str, ...]) -> str:
    return ";".join(
        frame for frame in stack.split(";") if frame.startswith(keep_prefixes)
    )


def project_counter(source: Counter[str], keep_prefixes: tuple[str, ...]) -> Counter[str]:
    out: Counter[str] = Counter()
    for stack, weight in source.items():
        projected = project_stack(stack, keep_prefixes)
        if projected:
            out[projected] += weight
    return out


def counter_summary(stacks: Counter[str]) -> dict[str, Any]:
    return {
        "total_weight": sum(stacks.values()),
        "unique_stacks": len(stacks),
        "sha256": short_hash(
            "\n".join(f"{stack} {weight}" for stack, weight in sorted(stacks.items()))
        ),
    }


def counter_delta(left: Counter[str], right: Counter[str], limit: int = 5) -> dict[str, Any]:
    missing = left - right
    extra = right - left
    return {
        "missing_from_right": [
            {"stack": stack, "weight": weight} for stack, weight in missing.most_common(limit)
        ],
        "extra_in_right": [
            {"stack": stack, "weight": weight} for stack, weight in extra.most_common(limit)
        ],
    }


def entropy_bits(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def system_semantic_key(stack: str) -> str:
    frames = stack.split(";")
    return (
        f"session:{frame_value(frames, 'session:')}/"
        f"prompt:{frame_value(frames, 'prompt:')}"
    )


def token_semantic_key(stack: str) -> str:
    frames = stack.split(";")
    return (
        f"session:{frame_value(frames, 'session:')}/"
        f"prompt:{frame_value(frames, 'prompt:')}/"
        f"call:{frame_value(frames, 'call:')}"
    )


def compression_summary(stacks: Counter[str]) -> dict[str, Any]:
    total = sum(stacks.values())
    unique = len(stacks)
    collapsed = sum(weight - 1 for weight in stacks.values() if weight > 1)
    return {
        "total_weight": total,
        "unique_stacks": unique,
        "compression_ratio": round(total / unique, 3) if unique else 0,
        "max_stack_reuse": max(stacks.values()) if stacks else 0,
        "collapsed_observations": collapsed,
        "collapsed_observation_share_pct": pct(collapsed, total),
    }


def mixing_against_full(
    full: Counter[str],
    keep_prefixes: tuple[str, ...],
    semantic_key: Callable[[str], str],
    example_limit: int,
) -> dict[str, Any]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for stack, weight in full.items():
        projected = project_stack(stack, keep_prefixes)
        buckets[projected][semantic_key(stack)] += weight

    mixed = {
        projected: variants
        for projected, variants in buckets.items()
        if len(variants) > 1
    }
    total = sum(full.values())
    mixed_weight = sum(sum(variants.values()) for variants in mixed.values())
    mixed_residual_weight = sum(
        sum(variants.values()) - variants.most_common(1)[0][1]
        for variants in mixed.values()
    )
    weighted_entropy_numer = sum(
        sum(variants.values()) * entropy_bits(variants)
        for variants in mixed.values()
    )
    examples = []
    for projected, variants in sorted(
        mixed.items(),
        key=lambda item: (-sum(item[1].values()), -len(item[1]), item[0]),
    )[:example_limit]:
        examples.append(
            {
                "projected_stack_hash": short_hash(projected),
                "projected_stack": projected,
                "weight": sum(variants.values()),
                "full_semantic_variant_count": len(variants),
                "top_full_semantic_variants": [
                    {"semantic": key, "weight": value}
                    for key, value in variants.most_common(8)
                ],
            }
        )

    return {
        "projected_bucket_count": len(buckets),
        "mixed_bucket_count": len(mixed),
        "mixed_bucket_share_pct": pct(len(mixed), len(buckets)),
        "mixed_weight": mixed_weight,
        "mixed_weight_share_pct": pct(mixed_weight, total),
        "mixed_residual_weight": mixed_residual_weight,
        "mixed_residual_weight_share_pct": pct(mixed_residual_weight, total),
        "weighted_mixed_bucket_entropy_bits": round(
            weighted_entropy_numer / mixed_weight,
            3,
        )
        if mixed_weight
        else 0.0,
        "max_full_semantic_variants_per_bucket": max(
            (len(variants) for variants in buckets.values()),
            default=0,
        ),
        "examples": examples,
    }


def variant_row(
    *,
    family: str,
    name: str,
    axes: list[str],
    full: Counter[str],
    keep_prefixes: tuple[str, ...],
    no_semantic_unique: int,
    semantic_key: Callable[[str], str],
    example_limit: int,
) -> dict[str, Any]:
    stacks = project_counter(full, keep_prefixes)
    compression = compression_summary(stacks)
    mixing = mixing_against_full(full, keep_prefixes, semantic_key, example_limit)
    return {
        "family": family,
        "variant": name,
        "semantic_axes": axes,
        "keep_prefixes": list(keep_prefixes),
        "projection": compression,
        "integrity": {
            "same_total_weight_as_full": compression["total_weight"] == sum(full.values()),
            "full_total_weight": sum(full.values()),
            "variant_total_weight": compression["total_weight"],
        },
        "stack_growth_vs_no_semantic_pct": pct(
            compression["unique_stacks"] - no_semantic_unique,
            no_semantic_unique,
        ),
        "mixing_against_full_semantics": mixing,
    }


def load_report_cross_check(report_path: Path, system: Counter[str], token: Counter[str]) -> dict[str, Any]:
    if not report_path.exists():
        return {
            "agentflame_report": str(report_path.relative_to(REPO_ROOT)),
            "exists": False,
            "matches_folded_totals": False,
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = report.get("summary") or {}
    report_system_total = ((summary.get("system") or {}).get("total_weight"))
    report_token_total = ((summary.get("token") or {}).get("total_weight"))
    folded_system_total = sum(system.values())
    folded_token_total = sum(token.values())
    return {
        "agentflame_report": str(report_path.relative_to(REPO_ROOT)),
        "exists": True,
        "report_sha256": sha256_file(report_path),
        "report_system_total_weight": report_system_total,
        "folded_system_total_weight": folded_system_total,
        "report_token_total_weight": report_token_total,
        "folded_token_total_weight": folded_token_total,
        "system_total_matches": report_system_total == folded_system_total,
        "token_total_matches": report_token_total == folded_token_total,
        "matches_folded_totals": (
            report_system_total == folded_system_total
            and report_token_total == folded_token_total
        ),
    }


def external_folded_cross_checks(
    input_dir: Path,
    system: Counter[str],
    token: Counter[str],
) -> list[dict[str, Any]]:
    checks: list[tuple[str, str, Counter[str], tuple[str, ...]]] = [
        ("system", "no-semantic", system, SYSTEM_BASE),
        ("system", "session-only", system, (*SYSTEM_BASE, "session:")),
        ("system", "prompt-only", system, (*SYSTEM_BASE, "prompt:")),
        ("token", "session-only", token, (*TOKEN_BASE, "session:")),
        ("token", "prompt-only", token, (*TOKEN_BASE, "prompt:")),
        ("token", "llm-call-only", token, (*TOKEN_BASE, "call:")),
    ]
    path_by_variant = {
        ("system", "no-semantic"): input_dir / "nonsemantic-system.folded.txt",
        ("system", "session-only"): input_dir / "session-system.folded.txt",
        ("system", "prompt-only"): input_dir / "prompt-system.folded.txt",
        ("token", "session-only"): input_dir / "session-token.folded.txt",
        ("token", "prompt-only"): input_dir / "prompt-token.folded.txt",
        ("token", "llm-call-only"): input_dir / "llm-token.folded.txt",
    }
    out = []
    for family, variant, full, keep in checks:
        path = path_by_variant[(family, variant)]
        projected = project_counter(full, keep)
        row: dict[str, Any] = {
            "family": family,
            "variant": variant,
            "path": str(path.relative_to(REPO_ROOT)),
            "exists": path.exists(),
            "projected": counter_summary(projected),
        }
        if path.exists():
            external = read_folded(path)
            row["external"] = {
                **counter_summary(external),
                "file_sha256": sha256_file(path),
            }
            row["exact_counter_match"] = projected == external
            row["delta_examples"] = counter_delta(projected, external)
        else:
            row["external"] = None
            row["exact_counter_match"] = False
        out.append(row)
    return out


def add_reductions(rows: list[dict[str, Any]]) -> None:
    by_family: dict[str, float] = {}
    for row in rows:
        if row["variant"] == "no-semantic":
            by_family[row["family"]] = row["mixing_against_full_semantics"][
                "mixed_weight_share_pct"
            ]
    for row in rows:
        baseline = by_family.get(row["family"], 0.0)
        current = row["mixing_against_full_semantics"]["mixed_weight_share_pct"]
        row["mixed_weight_reduction_vs_no_semantic_points"] = round(baseline - current, 3)
        row["mixed_weight_reduction_vs_no_semantic_pct"] = (
            pct(baseline - current, baseline) if baseline else 0.0
        )


def top_takeaways(system_rows: list[dict[str, Any]], token_rows: list[dict[str, Any]]) -> list[str]:
    def find(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
        return next(row for row in rows if row["variant"] == name)

    def mixed(row: dict[str, Any]) -> str:
        value = row["mixing_against_full_semantics"]["mixed_weight_share_pct"]
        return f"{value:.3f}%"

    sys_no = find(system_rows, "no-semantic")
    sys_session = find(system_rows, "session-only")
    sys_prompt = find(system_rows, "prompt-only")
    sys_full = find(system_rows, "full")
    tok_no = find(token_rows, "no-semantic")
    tok_prompt_llm = find(token_rows, "prompt+llm-call")
    tok_full = find(token_rows, "full")
    return [
        (
            "System-effect stacks have no LLM-call semantic axis by construction; "
            "LLM-call labels apply to token/LLM-call accounting, while tool effects "
            "inherit session and prompt tags."
        ),
        (
            "For system effects, no-semantic projection mixes "
            f"{mixed(sys_no)} "
            "of full semantic weight; session-only leaves "
            f"{mixed(sys_session)}, "
            "prompt-only leaves "
            f"{mixed(sys_prompt)}, "
            "and full session+prompt semantics leaves "
            f"{mixed(sys_full)} by construction."
        ),
        (
            "For token accounting, prompt+LLM-call projection reduces mixed full "
            "semantic weight from "
            f"{mixed(tok_no)} "
            "to "
            f"{mixed(tok_prompt_llm)}; "
            "full session+prompt+LLM-call semantics leaves "
            f"{mixed(tok_full)} by construction."
        ),
    ]


def table_rows(rows: list[dict[str, Any]]) -> str:
    out = [
        "| Family | Variant | Axes | Total | Unique | Growth vs no-sem | Mixed bucket weight % | Residual mixed weight % | Reduction vs no-sem | Max reuse |",
        "|--------|---------|------|-------|--------|------------------|-----------------------|-------------------------|---------------------|-----------|",
    ]
    for row in rows:
        axes = ",".join(row["semantic_axes"]) or "none"
        proj = row["projection"]
        mix = row["mixing_against_full_semantics"]
        out.append(
            f"| {row['family']} | {row['variant']} | {axes} | "
            f"{proj['total_weight']} | {proj['unique_stacks']} | "
            f"{row['stack_growth_vs_no_semantic_pct']:.3f}% | "
            f"{mix['mixed_weight_share_pct']:.3f}% | "
            f"{mix['mixed_residual_weight_share_pct']:.3f}% | "
            f"{row['mixed_weight_reduction_vs_no_semantic_points']:.3f} pp | "
            f"{proj['max_stack_reuse']} |"
        )
    return "\n".join(out)


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    takeaways = "\n".join(f"- {item}" for item in summary["takeaways"])
    rows = table_rows(summary["variants"])
    integrity = summary["integrity"]
    md = f"""# R131 Semantic-Axis Ablation

Date: {summary['generated_at'][:10]}

Input: `{summary['input']['agentflame_dir']}`

Integrity:

- System total preserved: {integrity['system_total_preserved']}
- Token total preserved: {integrity['token_total_preserved']}
- All variant totals match their full folded input: {integrity['all_totals_preserved']}
- AgentFlame report totals match folded inputs: {integrity['agentflame_report_totals_match']}
- Generated folded projections exactly match existing folded files: {integrity['external_folded_exact_matches']}

Definition: mixed bucket weight counts the whole projected bucket when it
contains more than one full semantic key; residual mixed weight counts only the
non-dominant semantic variants inside those mixed buckets.

## Results

{rows}

## Takeaways

{takeaways}

## Top System Example

`{summary['top_examples']['system']['projected_stack']}`

This projected bucket has weight {summary['top_examples']['system']['weight']} and
{summary['top_examples']['system']['full_semantic_variant_count']} full semantic variants.

## Top Token Example

`{summary['top_examples']['token']['projected_stack']}`

This projected bucket has weight {summary['top_examples']['token']['weight']} and
{summary['top_examples']['token']['full_semantic_variant_count']} full semantic variants.
"""
    path.write_text(md, encoding="utf-8")


def svg_bar_panel(
    *,
    title: str,
    rows: list[dict[str, Any]],
    x: int,
    y: int,
    width: int,
    bar_color: str,
) -> str:
    max_pct = max(
        row["mixing_against_full_semantics"]["mixed_weight_share_pct"] for row in rows
    ) or 1
    parts = [
        f"<text x='{x}' y='{y}' class='title'>{title}</text>",
    ]
    bar_y = y + 28
    for idx, row in enumerate(rows):
        pct_value = row["mixing_against_full_semantics"]["mixed_weight_share_pct"]
        bar_width = int((width - 180) * pct_value / max_pct)
        yy = bar_y + idx * 34
        label = row["variant"]
        parts.append(f"<text x='{x}' y='{yy + 14}' class='label'>{label}</text>")
        parts.append(
            f"<rect x='{x + 130}' y='{yy}' width='{bar_width}' height='18' "
            f"rx='2' fill='{bar_color}'/>"
        )
        parts.append(
            f"<text x='{x + 140 + bar_width}' y='{yy + 14}' class='value'>"
            f"{pct_value:.1f}%</text>"
        )
    return "\n".join(parts)


def write_svg(path: Path, system_rows: list[dict[str, Any]], token_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height = 360
    width = 980
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
  <style>
    text {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; fill: #1f2937; }}
    .heading {{ font-size: 20px; font-weight: 700; }}
    .title {{ font-size: 15px; font-weight: 700; }}
    .label {{ font-size: 12px; }}
    .value {{ font-size: 12px; fill: #374151; }}
    .note {{ font-size: 12px; fill: #4b5563; }}
  </style>
  <rect x='0' y='0' width='{width}' height='{height}' fill='#ffffff'/>
  <text x='24' y='34' class='heading'>R131 mixed full-semantic weight after axis ablation</text>
  <text x='24' y='56' class='note'>Lower is better; totals are preserved for every projection.</text>
  {svg_bar_panel(title='System effects: session/prompt axes', rows=system_rows, x=24, y=92, width=430, bar_color='#2563eb')}
  {svg_bar_panel(title='Token accounting: session/prompt/LLM axes', rows=token_rows, x=510, y=92, width=430, bar_color='#059669')}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    input_dir = args.input.resolve()
    system_path = input_dir / "semantic-system.folded.txt"
    token_path = input_dir / "semantic-token.folded.txt"
    report_path = input_dir / "agentflame.json"
    for path in (system_path, token_path):
        if not path.exists():
            raise FileNotFoundError(path)

    system = read_folded(system_path)
    token = read_folded(token_path)

    system_variants = [
        ("no-semantic", [], SYSTEM_BASE),
        ("session-only", ["session"], (*SYSTEM_BASE, "session:")),
        ("prompt-only", ["prompt"], (*SYSTEM_BASE, "prompt:")),
        ("full", ["session", "prompt"], (*SYSTEM_BASE, "session:", "prompt:")),
    ]
    token_variants = [
        ("no-semantic", [], TOKEN_BASE),
        ("session-only", ["session"], (*TOKEN_BASE, "session:")),
        ("prompt-only", ["prompt"], (*TOKEN_BASE, "prompt:")),
        ("llm-call-only", ["llm-call"], (*TOKEN_BASE, "call:")),
        ("prompt+llm-call", ["prompt", "llm-call"], (*TOKEN_BASE, "prompt:", "call:")),
        (
            "full",
            ["session", "prompt", "llm-call"],
            (*TOKEN_BASE, "session:", "prompt:", "call:"),
        ),
    ]

    no_system_unique = len(project_counter(system, SYSTEM_BASE))
    no_token_unique = len(project_counter(token, TOKEN_BASE))
    system_rows = [
        variant_row(
            family="system",
            name=name,
            axes=axes,
            full=system,
            keep_prefixes=keep,
            no_semantic_unique=no_system_unique,
            semantic_key=system_semantic_key,
            example_limit=args.example_limit,
        )
        for name, axes, keep in system_variants
    ]
    token_rows = [
        variant_row(
            family="token",
            name=name,
            axes=axes,
            full=token,
            keep_prefixes=keep,
            no_semantic_unique=no_token_unique,
            semantic_key=token_semantic_key,
            example_limit=args.example_limit,
        )
        for name, axes, keep in token_variants
    ]
    add_reductions(system_rows)
    add_reductions(token_rows)

    all_rows = system_rows + token_rows
    report_check = load_report_cross_check(report_path, system, token)
    folded_checks = external_folded_cross_checks(input_dir, system, token)
    folded_checks_pass = all(row["exact_counter_match"] for row in folded_checks)
    top_system_example = system_rows[0]["mixing_against_full_semantics"]["examples"][0]
    top_token_example = token_rows[0]["mixing_against_full_semantics"]["examples"][0]
    repo_status = run_git(["status", "--short"])
    summary = {
        "run_id": "R131",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input": {
            "agentflame_dir": str(input_dir.relative_to(REPO_ROOT)),
            "system_folded": str(system_path.relative_to(REPO_ROOT)),
            "token_folded": str(token_path.relative_to(REPO_ROOT)),
            "agentflame_report": str(report_path.relative_to(REPO_ROOT)) if report_path.exists() else None,
            "system_folded_sha256": sha256_file(system_path),
            "token_folded_sha256": sha256_file(token_path),
            "agentflame_report_sha256": sha256_file(report_path) if report_path.exists() else None,
        },
        "provenance": {
            "repo_commit": run_git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(repo_status),
            "source_sha256": sha256_file(Path(__file__)),
            "command": " ".join(args.command_argv),
        },
        "variants": all_rows,
        "cross_checks": {
            "agentflame_report_totals": report_check,
            "generated_folded_files": folded_checks,
            "all_external_checks_passed": (
                report_check.get("matches_folded_totals") is True and folded_checks_pass
            ),
        },
        "takeaways": top_takeaways(system_rows, token_rows),
        "top_examples": {
            "system": top_system_example,
            "token": top_token_example,
        },
        "integrity": {
            "system_total_weight": sum(system.values()),
            "token_total_weight": sum(token.values()),
            "system_total_preserved": all(
                row["integrity"]["same_total_weight_as_full"] for row in system_rows
            ),
            "token_total_preserved": all(
                row["integrity"]["same_total_weight_as_full"] for row in token_rows
            ),
            "all_totals_preserved": all(
                row["integrity"]["same_total_weight_as_full"] for row in all_rows
            ),
            "agentflame_report_totals_match": report_check.get("matches_folded_totals") is True,
            "external_folded_exact_matches": folded_checks_pass,
        },
        "interpretation": [
            "This is a mechanism ablation, not a user-utility result.",
            "The full variant has zero mixing against full semantics by construction; the reviewer-facing value is the marginal drop from no-semantic to session/prompt/LLM-call projections.",
            "System-effect stacks intentionally evaluate session and prompt axes only because process/file/network effects are tool-call effects, not LLM-call effects.",
        ],
    }
    if not summary["integrity"]["all_totals_preserved"]:
        raise AssertionError("one or more projections changed total weight")
    if not summary["integrity"]["agentflame_report_totals_match"]:
        raise AssertionError("agentflame.json totals do not match folded inputs")
    if not summary["integrity"]["external_folded_exact_matches"]:
        raise AssertionError("projected counters do not match generated folded files")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--local-out", type=Path, default=DEFAULT_LOCAL_OUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--example-limit", type=int, default=12)
    args = parser.parse_args()
    import sys

    args.command_argv = sys.argv
    return args


def main() -> None:
    args = parse_args()
    summary = build_summary(args)
    write_json(args.local_out, summary)
    write_json(args.out_dir / "semantic-ablation-r131.json", summary)
    write_markdown(args.out_dir / "semantic-ablation-r131.md", summary)
    system_rows = [row for row in summary["variants"] if row["family"] == "system"]
    token_rows = [row for row in summary["variants"] if row["family"] == "token"]
    write_svg(args.out_dir / "semantic-ablation-r131.svg", system_rows, token_rows)
    print(
        "R131 ok: "
        f"system_total={summary['integrity']['system_total_weight']} "
        f"token_total={summary['integrity']['token_total_weight']} "
        f"variants={len(summary['variants'])}"
    )


if __name__ == "__main__":
    main()
