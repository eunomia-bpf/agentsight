#!/usr/bin/env python3
"""Run a local-only tag stability smoke test over real session fragments.

Raw prompt/session/LLM text is used only in-process. Outputs contain hashes,
one-word tags, counts, and provenance, so the committed artifact can be audited
without exposing session text.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_tag_flamegraph import (  # noqa: E402
    DEFAULT_CLAUDE_ROOT,
    DEFAULT_CODEX_ROOT,
    DEFAULT_LLAMA_CLI,
    REPO_ROOT,
    OneWordTagger,
    clean_space,
    command_text,
    file_sha256,
    parse_sessions,
    path_group,
    short_hash,
)


TAG_RE = re.compile(r"^[a-z][a-z0-9]{1,15}$")
GENERIC_TAGS = {
    "agent",
    "analysis",
    "answer",
    "assistant",
    "chat",
    "code",
    "coding",
    "data",
    "doing",
    "general",
    "prompt",
    "request",
    "response",
    "session",
    "task",
    "unknown",
    "work",
    "working",
}


@dataclasses.dataclass(frozen=True)
class Fragment:
    fragment_id: str
    kind: str
    source: str
    model: str
    text: str
    hints: tuple[str, ...]

    @property
    def text_chars(self) -> int:
        return len(self.text)


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def modal_tag(tags: list[str]) -> str:
    if not tags:
        return ""
    return Counter(tags).most_common(1)[0][0]


def collect_fragments(args: argparse.Namespace) -> tuple[list[Fragment], list[str], str]:
    session_args = argparse.Namespace(
        project_root=args.project_root,
        codex_root=args.codex_root,
        claude_root=args.claude_root,
        scan_files=args.scan_files,
        max_sessions=args.max_sessions,
    )
    sessions, warnings = parse_sessions(session_args)
    root = Path(args.project_root).resolve()
    fragments: list[Fragment] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, source: str, model: str, text: str, hints: tuple[str, ...], stable_key: str) -> None:
        text = clean_space(text, args.fragment_chars)
        if not text:
            return
        dedupe = (kind, stable_key)
        if dedupe in seen:
            return
        seen.add(dedupe)
        fragments.append(
            Fragment(
                fragment_id=short_hash(f"{kind}:{stable_key}:{text}", 16),
                kind=kind,
                source=source,
                model=model,
                text=text,
                hints=hints,
            )
        )

    for session in sessions:
        prompt_text = " ".join(req.preview for req in session.user_requests[:6])
        session_text = clean_space(
            f"{session.title} {path_group(session.cwd, root)} {prompt_text}",
            args.fragment_chars,
        )
        add(
            "session",
            session.source,
            session.model,
            session_text,
            (session.source, session.model),
            session.session_id,
        )
        for req in session.user_requests:
            add("prompt", session.source, session.model, req.preview, (), req.text_hash)
        for call in session.llm_calls:
            add(
                "llm",
                session.source,
                call.model or session.model,
                call.preview,
                (session.source, call.model or session.model),
                call.text_hash,
            )

    fingerprint = short_hash(
        "\n".join(f"{s.source}:{s.session_id}:{len(s.user_requests)}:{len(s.llm_calls)}" for s in sessions),
        16,
    )
    return select_fragments(fragments, args.fragments), warnings, fingerprint


def select_fragments(fragments: list[Fragment], limit: int) -> list[Fragment]:
    if limit <= 0 or len(fragments) <= limit:
        return fragments
    groups: dict[str, list[Fragment]] = {
        "prompt": [],
        "session": [],
        "llm": [],
    }
    for fragment in fragments:
        groups.setdefault(fragment.kind, []).append(fragment)

    selected: list[Fragment] = []
    idx = 0
    order = ["prompt", "session", "llm"]
    while len(selected) < limit:
        made_progress = False
        for kind in order:
            group = groups.get(kind, [])
            if idx < len(group):
                selected.append(group[idx])
                made_progress = True
                if len(selected) >= limit:
                    break
        if not made_progress:
            break
        idx += 1
    return selected


def run_annotator(
    name: str,
    fragments: list[Fragment],
    args: argparse.Namespace,
    tmp_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    llama_enabled = name == "llama"
    fragment_subset = fragments
    if llama_enabled and args.llama_limit > 0:
        fragment_cap = max(args.llama_limit // max(args.repeats, 1), 0)
        fragment_subset = fragments[:fragment_cap]

    totals = Counter()
    failures: list[str] = []
    for run_idx in range(args.repeats):
        tagger = OneWordTagger(
            cache_path=tmp_dir / f"{name}-run-{run_idx}.json",
            llama_cli=Path(args.llama_cli) if llama_enabled and args.llama_cli else None,
            model=Path(args.model) if llama_enabled and args.model else None,
            llama_limit=-1 if llama_enabled else 0,
            timeout_s=args.llama_timeout,
        )
        for fragment in fragment_subset:
            tag = tagger.tag(fragment.kind, fragment.text, hints=fragment.hints)
            valid = bool(TAG_RE.fullmatch(tag))
            rows.append(
                {
                    "annotator": name,
                    "run": run_idx,
                    "fragment_id": fragment.fragment_id,
                    "kind": fragment.kind,
                    "source": fragment.source,
                    "model": fragment.model,
                    "text_chars": fragment.text_chars,
                    "tag": tag,
                    "valid": valid,
                    "generic": tag in GENERIC_TAGS,
                }
            )
        totals.update(
            {
                "requests": tagger.requests,
                "llama_calls": tagger.llama_calls,
                "llama_successes": tagger.llama_successes,
                "fallback_uses": tagger.fallback_uses,
                "cache_hits": tagger.cache_hits,
            }
        )
        failures.extend(tagger.llama_failures)

    return rows, {
        "annotator": name,
        "fragment_count": len(fragment_subset),
        "repeats": args.repeats,
        "requests": totals["requests"],
        "llama_calls": totals["llama_calls"],
        "llama_successes": totals["llama_successes"],
        "fallback_uses": totals["fallback_uses"],
        "cache_hits": totals["cache_hits"],
        "llama_failures": failures[:8],
    }


def annotator_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_annotator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_annotator[str(row["annotator"])].append(row)

    result: dict[str, Any] = {}
    for name, annotator_rows in sorted(by_annotator.items()):
        by_fragment: dict[str, list[str]] = defaultdict(list)
        tag_counts = Counter()
        invalid = 0
        generic = 0
        for row in annotator_rows:
            tag = str(row["tag"])
            by_fragment[str(row["fragment_id"])].append(tag)
            tag_counts[tag] += 1
            invalid += 0 if row["valid"] else 1
            generic += 1 if row["generic"] else 0
        stable = sum(1 for tags in by_fragment.values() if len(set(tags)) == 1)
        modal_shares = [
            Counter(tags).most_common(1)[0][1] / len(tags)
            for tags in by_fragment.values()
            if tags
        ]
        result[name] = {
            "outputs": len(annotator_rows),
            "fragment_count": len(by_fragment),
            "invalid_count": invalid,
            "invalid_output_share_pct": pct(invalid, len(annotator_rows)),
            "generic_output_share_pct": pct(generic, len(annotator_rows)),
            "unique_tags": len(tag_counts),
            "exact_stable_fragment_count": stable,
            "exact_stable_fragment_share_pct": pct(stable, len(by_fragment)),
            "mean_modal_share_pct": round(100.0 * sum(modal_shares) / len(modal_shares), 3)
            if modal_shares
            else 0.0,
            "top_tags": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(12)],
            "unstable_examples": [
                {"fragment_id": fragment_id, "tags": dict(Counter(tags))}
                for fragment_id, tags in sorted(by_fragment.items())
                if len(set(tags)) > 1
            ][:10],
        }
    return result


def cross_annotator_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_annotator_fragment: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_annotator_fragment[str(row["annotator"])][str(row["fragment_id"])].append(str(row["tag"]))
    annotators = sorted(by_annotator_fragment)
    if len(annotators) < 2:
        return {"pairs": []}

    pairs = []
    for i, left in enumerate(annotators):
        for right in annotators[i + 1 :]:
            common = sorted(set(by_annotator_fragment[left]) & set(by_annotator_fragment[right]))
            matches = 0
            examples = []
            for fragment_id in common:
                left_tag = modal_tag(by_annotator_fragment[left][fragment_id])
                right_tag = modal_tag(by_annotator_fragment[right][fragment_id])
                if left_tag == right_tag:
                    matches += 1
                elif len(examples) < 10:
                    examples.append(
                        {
                            "fragment_id": fragment_id,
                            left: left_tag,
                            right: right_tag,
                        }
                    )
            pairs.append(
                {
                    "left": left,
                    "right": right,
                    "common_fragments": len(common),
                    "modal_exact_matches": matches,
                    "modal_exact_match_pct": pct(matches, len(common)),
                    "mismatch_examples": examples,
                }
            )
    return {"pairs": pairs}


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "annotator",
        "run",
        "fragment_id",
        "kind",
        "source",
        "model",
        "text_chars",
        "tag",
        "valid",
        "generic",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def write_summary(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Tag Stability Smoke",
        "",
        "This smoke test uses raw session fragments locally but commits only hashes, tags, and counts.",
        "It is evidence for C7 syntax/repeated-run stability, not human semantic adequacy.",
        "",
        "## Metrics",
        "",
    ]
    for name, metrics in result["annotator_metrics"].items():
        lines.append(
            f"- {name}: {metrics['fragment_count']} fragments, "
            f"{metrics['exact_stable_fragment_share_pct']}% exact-stable, "
            f"{metrics['generic_output_share_pct']}% generic outputs, "
            f"{metrics['invalid_count']} invalid outputs."
        )
    for pair in result["cross_annotator_metrics"]["pairs"]:
        lines.append(
            f"- {pair['left']} vs {pair['right']}: "
            f"{pair['modal_exact_match_pct']}% modal exact match over "
            f"{pair['common_fragments']} common fragments."
        )
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            f"- Smoke verdict: {result['smoke_verdict']}.",
            "- C7 remains partial until manual adequacy labels and larger repeated-model runs exist.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def smoke_verdict(metrics: dict[str, Any]) -> str:
    annotators = metrics["annotator_metrics"].values()
    if not annotators:
        return "unsupported"
    invalid = sum(item["invalid_count"] for item in annotators)
    min_stability = min(item["exact_stable_fragment_share_pct"] for item in annotators)
    return "smoke_supported" if invalid == 0 and min_stability >= 95.0 else "partial"


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fragments, warnings, session_fingerprint = collect_fragments(args)
    if not fragments:
        raise SystemExit("no fragments found")

    annotator_names = ["fallback"]
    llama_available = (
        args.model
        and args.llama_cli
        and Path(args.model).exists()
        and Path(args.llama_cli).exists()
        and args.llama_limit != 0
    )
    if llama_available:
        annotator_names.append("llama")

    all_rows: list[dict[str, Any]] = []
    annotator_provenance: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="agentsight-tag-stability-") as tmp:
        tmp_dir = Path(tmp)
        for name in annotator_names:
            rows, provenance = run_annotator(name, fragments, args, tmp_dir)
            all_rows.extend(rows)
            annotator_provenance.append(provenance)

    metrics = {
        "annotator_metrics": annotator_metrics(all_rows),
        "cross_annotator_metrics": cross_annotator_metrics(all_rows),
    }
    result = {
        "schema_version": 1,
        "generated_from": "local raw session fragments; committed output is sanitized",
        "config": {
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
            "fragments_requested": args.fragments,
            "fragments_selected": len(fragments),
            "repeats": args.repeats,
            "fragment_chars": args.fragment_chars,
            "llama_limit": args.llama_limit,
        },
        "provenance": {
            "repo_commit": command_text(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "repo_dirty": bool(command_text(["git", "status", "--short"], REPO_ROOT)),
            "script_sha256": file_sha256(Path(__file__).resolve()),
            "session_fingerprint": session_fingerprint,
            "model": Path(args.model).name if args.model else None,
            "model_sha256": file_sha256(Path(args.model)) if args.model and Path(args.model).exists() else None,
            "llama_cli": Path(args.llama_cli).name if args.llama_cli else None,
            "llama_cli_sha256": file_sha256(Path(args.llama_cli))
            if args.llama_cli and Path(args.llama_cli).exists()
            else None,
        },
        "fragment_counts": dict(Counter(fragment.kind for fragment in fragments)),
        "annotator_provenance": annotator_provenance,
        "warnings": warnings[:20],
        **metrics,
    }
    result["smoke_verdict"] = smoke_verdict(result)

    json_path = out_dir / "tag-stability-smoke.json"
    csv_path = out_dir / "tag-stability-smoke.csv"
    summary_path = out_dir / "tag-stability-summary.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_rows(csv_path, all_rows)
    write_summary(summary_path, result)
    print(json.dumps(result, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(REPO_ROOT))
    parser.add_argument("--codex-root", default=str(DEFAULT_CODEX_ROOT))
    parser.add_argument("--claude-root", default=str(DEFAULT_CLAUDE_ROOT))
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "visexp" / "out"))
    parser.add_argument("--scan-files", type=int, default=180)
    parser.add_argument("--max-sessions", type=int, default=36)
    parser.add_argument("--fragments", type=int, default=30)
    parser.add_argument("--fragment-chars", type=int, default=700)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--llama-cli", default=str(DEFAULT_LLAMA_CLI) if DEFAULT_LLAMA_CLI.exists() else "")
    parser.add_argument("--model", default="")
    parser.add_argument("--llama-limit", type=int, default=0)
    parser.add_argument("--llama-timeout", type=int, default=20)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
