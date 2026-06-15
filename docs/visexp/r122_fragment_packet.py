#!/usr/bin/env python3
"""Build a redacted real-fragment packet for tag adequacy and stability runs."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_tag_flamegraph import (  # noqa: E402
    DEFAULT_CLAUDE_ROOT,
    DEFAULT_CODEX_ROOT,
    REPO_ROOT,
    clean_space,
    command_text,
    file_sha256,
    parse_sessions,
    path_group,
    short_hash,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LOCAL_FRAGMENT_FILE = REPO_ROOT / ".agentsight" / "agentflame" / "r122-real-fragments.txt"
DEFAULT_OUT_CSV = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.csv"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "tag-adequacy-label-packet-r122.md"


SECRET_RE = re.compile(
    r"\b(?:sk|ghp|gho|hf)_[A-Za-z0-9_]{12,}|\bsk-[A-Za-z0-9_-]{16,}",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"https?://([^/\s)\"']+)[^\s)\"']*")
LONG_HEX_RE = re.compile(r"\b[0-9a-f]{24,}\b", re.IGNORECASE)
TOOL_USE_RE = re.compile(r"\btoolu_[A-Za-z0-9_-]{8,}\b")
XML_ID_RE = re.compile(r"<(task-id|tool-use-id)>[^<]*</\1>")
SHELL_PROMPT_RE = re.compile(r"\b[A-Za-z0-9._-]+@[A-Za-z0-9._-]+:[^\s$]*\$")


def leak_patterns(include_long_ids: bool = False) -> list[tuple[str, re.Pattern[str]]]:
    patterns = [
        ("home_path", re.compile(r"/home/yunwei37|home/yunwei37|-home-yunwei37")),
        ("shell_prompt", re.compile(r"\b[A-Za-z0-9._-]+@[A-Za-z0-9._-]+:[^\s$]*\$")),
        ("secret", SECRET_RE),
        ("email", EMAIL_RE),
        ("tool_use_id", TOOL_USE_RE),
        ("raw_url_path", re.compile(r"https?://[^/\s)\"']+/(?!\.\.\.)[^\s)\"',]+")),
    ]
    if include_long_ids:
        patterns.append(("long_hex", LONG_HEX_RE))
    return patterns


@dataclasses.dataclass(frozen=True)
class Fragment:
    fragment_index: int
    fragment_hash: str
    kind: str
    source: str
    model: str
    text: str
    preview: str
    text_chars: int


def scrub_text(text: str, limit: int) -> str:
    text = clean_space(text, limit)
    home = str(Path.home())
    user = Path.home().name
    text = text.replace(home, "$HOME").replace(f"home/{Path.home().name}", "$HOME")
    text = text.replace(f"-home-{user}-", "$HOME-")
    text = text.replace(f"/home/{user}/", "$HOME/")
    text = XML_ID_RE.sub(lambda m: f"<{m.group(1)}><id></{m.group(1)}>", text)
    text = SHELL_PROMPT_RE.sub("<shell-prompt>", text)
    text = SECRET_RE.sub("<secret>", text)
    text = TOOL_USE_RE.sub("<tool-use-id>", text)
    text = EMAIL_RE.sub("<email>", text)
    text = URL_RE.sub(lambda m: f"https://{m.group(1)}/...", text)
    text = LONG_HEX_RE.sub("<hex>", text)
    return clean_space(text, limit)


def redaction_scan(paths: list[Path]) -> dict[str, Any]:
    findings = []
    for path in paths:
        if not path.exists():
            continue
        include_long_ids = path.suffix in {".csv", ".md"}
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            for name, pattern in leak_patterns(include_long_ids):
                if pattern.search(line):
                    findings.append({"file": rel(path), "line": line_no, "pattern": name})
                    break
    return {
        "status": "ok" if not findings else "fail",
        "files_scanned": len([path for path in paths if path.exists()]),
        "findings": findings[:20],
    }


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def pick_evenly(items: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    if limit <= 0 or len(items) <= limit:
        return items
    if limit == 1:
        return [items[0]]
    indexes = [round(i * (len(items) - 1) / (limit - 1)) for i in range(limit)]
    selected = []
    seen: set[int] = set()
    for idx in indexes:
        if idx not in seen:
            selected.append(items[idx])
            seen.add(idx)
    cursor = 0
    while len(selected) < limit and cursor < len(items):
        if cursor not in seen:
            selected.append(items[cursor])
            seen.add(cursor)
        cursor += 1
    return selected[:limit]


def collect_candidates(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[str], str, dict[str, Any]]:
    session_args = argparse.Namespace(
        project_root=args.project_root,
        codex_root=args.codex_root,
        claude_root=args.claude_root,
        scan_files=args.scan_files,
        max_sessions=args.max_sessions,
    )
    sessions, warnings = parse_sessions(session_args)
    root = Path(args.project_root).resolve()
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, source: str, model: str, text: str, stable_key: str) -> None:
        redacted = scrub_text(text, args.fragment_chars)
        if not redacted:
            return
        dedupe = (kind, sha16(f"{stable_key}\n{redacted}"))
        if dedupe in seen:
            return
        seen.add(dedupe)
        candidates.append(
            {
                "kind": kind,
                "source": source,
                "model": model,
                "text": redacted,
                "stable_key": stable_key,
            }
        )

    for session in sessions:
        prompt_text = " ".join(req.preview for req in session.user_requests[:6])
        add(
            "session",
            session.source,
            session.model,
            f"{session.title} {path_group(session.cwd, root)} {prompt_text}",
            session.session_id,
        )
        for req in session.user_requests:
            add("prompt", session.source, session.model, req.preview, req.text_hash)
        for call in session.llm_calls:
            add("llm", session.source, call.model or session.model, call.preview, call.text_hash)

    fingerprint = short_hash(
        "\n".join(f"{s.source}:{s.session_id}:{len(s.user_requests)}:{len(s.llm_calls)}" for s in sessions),
        16,
    )
    source_counts = Counter(session.source for session in sessions)
    parse_summary = {
        "sessions": len(sessions),
        "source_counts": dict(source_counts),
        "candidate_counts": dict(Counter(item["kind"] for item in candidates)),
    }
    return candidates, warnings, fingerprint, parse_summary


def build_fragments(candidates: list[dict[str, str]], per_kind: int, preview_chars: int) -> list[Fragment]:
    groups: dict[str, list[dict[str, str]]] = {"session": [], "prompt": [], "llm": []}
    for candidate in candidates:
        groups.setdefault(candidate["kind"], []).append(candidate)
    selected: list[dict[str, str]] = []
    for kind in ("session", "prompt", "llm"):
        selected.extend(pick_evenly(groups.get(kind, []), per_kind))

    fragments: list[Fragment] = []
    for idx, item in enumerate(selected):
        text = item["text"]
        fragments.append(
            Fragment(
                fragment_index=idx,
                fragment_hash=sha16(text),
                kind=item["kind"],
                source=item["source"],
                model=item["model"],
                text=text,
                preview=clean_space(text, preview_chars),
                text_chars=len(text),
            )
        )
    return fragments


def write_local_fragment_file(path: Path, fragments: list[Fragment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fragment.text for fragment in fragments) + "\n", encoding="utf-8")


def write_csv(path: Path, fragments: list[Fragment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "fragment_index",
        "fragment_hash",
        "kind",
        "source",
        "model",
        "text_chars",
        "preview",
        "labeler_1",
        "labeler_2",
        "adjudicated_label",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for fragment in fragments:
            writer.writerow(
                {
                    "fragment_index": fragment.fragment_index,
                    "fragment_hash": fragment.fragment_hash,
                    "kind": fragment.kind,
                    "source": fragment.source,
                    "model": fragment.model,
                    "text_chars": fragment.text_chars,
                    "preview": fragment.preview,
                    "labeler_1": "",
                    "labeler_2": "",
                    "adjudicated_label": "",
                    "notes": "",
                }
            )


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def write_json(
    path: Path,
    args: argparse.Namespace,
    fragments: list[Fragment],
    warnings: list[str],
    fingerprint: str,
    parse_summary: dict[str, Any],
) -> dict[str, Any]:
    result = {
        "schema_version": 1,
        "run_id": "R122-packet",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": "local Codex/Claude session histories parsed read-only; committed output uses redacted text",
        "config": {
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
            "per_kind": args.per_kind,
            "fragment_chars": args.fragment_chars,
            "preview_chars": args.preview_chars,
        },
        "provenance": {
            "repo_commit": command_text(["git", "rev-parse", "HEAD"], REPO_ROOT),
            "repo_dirty": bool(command_text(["git", "status", "--short"], REPO_ROOT)),
            "script_sha256": file_sha256(Path(__file__).resolve()),
            "session_fingerprint": fingerprint,
            "local_fragment_file": rel(args.local_fragment_file),
        },
        "parse_summary": parse_summary,
        "fragment_counts": dict(Counter(fragment.kind for fragment in fragments)),
        "fragment_count": len(fragments),
        "warnings": warnings[:20],
        "outputs": {
            "label_packet_csv": rel(args.out_csv),
            "summary_json": rel(args.out_json),
            "summary_md": rel(args.out_md),
        },
        "privacy": {
            "redactions": ["home path", "secret token patterns", "email addresses", "URL paths", "long hex strings"],
            "raw_trace_files_modified": False,
            "local_fragment_file_committed": False,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    counts = result["fragment_counts"]
    text = f"""# R122 Tag Adequacy Label Packet

Date: {result['generated_at']}

This artifact samples real local Codex/Claude session, prompt, and LLM-call
fragments for human tag adequacy labeling. Raw traces are parsed read-only. The
committed CSV contains redacted previews and blank label columns; the local
fragment file used by automated stability runs is not committed.

| Kind | Count |
|------|------:|
| session | {counts.get('session', 0)} |
| prompt | {counts.get('prompt', 0)} |
| llm | {counts.get('llm', 0)} |

Outputs:

- Label packet: `{result['outputs']['label_packet_csv']}`
- Local fragment file: `{result['provenance']['local_fragment_file']}`

Claim impact: this prepares R122 but does not by itself support human adequacy.
The CSV still needs independent labels and agreement/adjudication.
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidates, warnings, fingerprint, parse_summary = collect_candidates(args)
    fragments = build_fragments(candidates, args.per_kind, args.preview_chars)
    write_local_fragment_file(args.local_fragment_file, fragments)
    write_csv(args.out_csv, fragments)
    result = write_json(args.out_json, args, fragments, warnings, fingerprint, parse_summary)
    write_markdown(args.out_md, result)
    scan = redaction_scan([args.out_csv, args.out_md, args.out_json])
    result["privacy"]["redaction_scan"] = scan
    args.out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.out_md, result)
    if scan["status"] != "ok":
        raise SystemExit(f"redaction scan failed: {json.dumps(scan, ensure_ascii=False)}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--codex-root", type=Path, default=DEFAULT_CODEX_ROOT)
    parser.add_argument("--claude-root", type=Path, default=DEFAULT_CLAUDE_ROOT)
    parser.add_argument("--scan-files", type=int, default=10000)
    parser.add_argument("--max-sessions", type=int, default=10000)
    parser.add_argument("--per-kind", type=int, default=100)
    parser.add_argument("--fragment-chars", type=int, default=700)
    parser.add_argument("--preview-chars", type=int, default=220)
    parser.add_argument("--local-fragment-file", type=Path, default=DEFAULT_LOCAL_FRAGMENT_FILE)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
