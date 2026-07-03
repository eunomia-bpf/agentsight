#!/usr/bin/env python3
"""Sample labeled agent-trajectory datasets into operation JSONL.

The durable profiler abstraction is an operation plus an operation stack. This
script keeps third-party datasets outside the repository, then emits a small
normalized operation JSONL file that `agentpprof --operation-file` can fold with
the same `--stack` and `--stack-rule` machinery used for local traces.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


HF_DATASET_VIEWER = "https://datasets-server.huggingface.co"
DEFAULT_OUT = Path(".agentsight/datasets/agent-traces")


DATASETS: dict[str, dict[str, Any]] = {
    "weblinx-chat": {
        "title": "WebLINX chat split",
        "hf_repo": "McGill-NLP/WebLINX",
        "config": "chat",
        "split": "validation",
        "access": "hf-viewer",
        "adapter": "weblinx-chat",
        "source": "https://mcgill-nlp.github.io/weblinx/",
        "paper": "https://arxiv.org/abs/2402.05930",
        "why": "Expert web-navigation demonstrations with action, history, turn, and demo ids.",
    },
    "mind2web": {
        "title": "Mind2Web",
        "hf_repo": "osunlp/Mind2Web",
        "config": "default",
        "split": "train",
        "access": "large-repo-json",
        "source": "https://osu-nlp-group.github.io/Mind2Web/",
        "paper": "https://arxiv.org/abs/2306.06070",
        "why": "Crowdsourced web task action sequences; best as an oracle dataset after full-file download.",
        "note": "Dataset Viewer row groups are too large; use HF repo files or the official raw dump for full runs.",
    },
    "android-control": {
        "title": "AndroidControl",
        "hf_repo": "smolagents/android-control",
        "config": "default",
        "split": "train",
        "access": "large-parquet",
        "source": "https://github.com/google-research/google-research/blob/master/android_control/README.md",
        "paper": "https://arxiv.org/abs/2406.03679",
        "why": "Human Android demonstrations with high-level goals, step instructions, screenshots, trees, and actions.",
        "note": "Dataset Viewer row groups are too large; use full parquet/TFRecord workflows for full runs.",
    },
    "aitw": {
        "title": "Android in the Wild",
        "access": "official-gcs",
        "source": "https://research.google/pubs/android-in-the-wild-a-large-scale-dataset-for-android-device-control/",
        "paper": "https://arxiv.org/abs/2307.10088",
        "why": "Large device-control demonstrations with screens, actions, and natural language instructions.",
        "note": "Use the official google-research/android_in_the_wild release for full data.",
    },
    "toolbench": {
        "title": "ToolBench / ToolLLM",
        "access": "official-drive",
        "source": "https://github.com/OpenBMB/ToolBench",
        "paper": "https://arxiv.org/abs/2307.16789",
        "why": "Tool-use instructions, solution paths, real API calls, and reasoning traces.",
        "note": "Official release is hosted outside Dataset Viewer; convert answer/toolenv JSON after download.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_parser = sub.add_parser("list", help="List known labeled trajectory sources")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    sample = sub.add_parser("sample", help="Download a small supported sample")
    sample.add_argument("dataset", choices=sorted(DATASETS))
    sample.add_argument("--limit", type=int, default=50)
    sample.add_argument("--offset", type=int, default=0)
    sample.add_argument("--out", type=Path, default=DEFAULT_OUT)
    sample.add_argument(
        "--include-text",
        action="store_true",
        help="Include instruction/action-history text in normalized operations",
    )

    args = parser.parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "sample":
        return cmd_sample(args)
    parser.error(f"unknown command {args.cmd}")
    return 2


def cmd_list(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(DATASETS, indent=2, sort_keys=True))
        return 0
    for key, item in DATASETS.items():
        hf = item.get("hf_repo", "no-hf-repo")
        print(f"{key:16} {item['access']:15} {hf:28} {item['title']}")
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    dataset = DATASETS[args.dataset]
    if dataset["access"] != "hf-viewer":
        note = dataset.get("note", "No lightweight sampler is configured for this dataset.")
        raise SystemExit(f"{args.dataset} is not viewer-sampleable: {note}")
    if args.limit <= 0:
        raise SystemExit("--limit must be positive")

    rows = hf_viewer_rows(dataset, args.offset, args.limit)
    out_dir = args.out / args.dataset / f"{dataset['config']}-{dataset['split']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / f"rows-{args.offset}-{args.offset + len(rows)}.jsonl"
    op_path = out_dir / f"operations-{args.offset}-{args.offset + len(rows)}.jsonl"
    manifest_path = out_dir / "manifest.json"

    operations = [normalize_row(args.dataset, dataset, row, args.include_text) for row in rows]
    write_jsonl(raw_path, rows)
    write_jsonl(op_path, operations)
    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset": args.dataset,
        "source": dataset,
        "offset": args.offset,
        "limit": args.limit,
        "rows": len(rows),
        "raw_rows": str(raw_path),
        "operation_jsonl": str(op_path),
        "privacy": "raw rows may contain task text; operation JSONL omits text unless --include-text is set",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def hf_viewer_rows(dataset: dict[str, Any], offset: int, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    while len(rows) < limit:
        length = min(100, limit - len(rows))
        params = urllib.parse.urlencode(
            {
                "dataset": dataset["hf_repo"],
                "config": dataset["config"],
                "split": dataset["split"],
                "offset": offset + len(rows),
                "length": length,
            }
        )
        payload = get_json(f"{HF_DATASET_VIEWER}/rows?{params}")
        if "error" in payload:
            raise SystemExit(payload["error"])
        batch = [entry["row"] for entry in payload.get("rows", [])]
        if not batch:
            break
        rows.extend(batch)
    return rows


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_row(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> dict[str, Any]:
    adapter = dataset.get("adapter")
    if adapter == "weblinx-chat":
        return normalize_weblinx_chat(dataset_id, dataset, row, include_text)
    raise SystemExit(f"no adapter for dataset {dataset_id}")


def normalize_weblinx_chat(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> dict[str, Any]:
    action = str(row.get("action") or "unknown")
    action_name = first_match(r"^([A-Za-z_][A-Za-z0-9_]*)", action, "unknown").lower()
    target = first_match(r'uid=(?:"([^"]+)"|([^,)]+))', action, "none")
    if target == "None":
        target = "none"

    fields: dict[str, Any] = {
        "project": "external-agent-traces",
        "agent": "human-demo",
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": str(row.get("demo") or "unknown"),
        "turn": str(row.get("turn") or "unknown"),
        "task": "web-navigation",
        "phase": action_name,
        "op": "action",
        "tool": "browser",
        "action": action_name,
        "target": sanitize_label(target),
        "status": "gold",
    }
    if include_text:
        instruction = latest_instructor_utterance(str(row.get("action_history") or ""))
        if instruction:
            fields["task_preview"] = truncate_clean(instruction, 180)
        fields["action_raw"] = truncate_clean(action, 180)
    return {"value": 1, "fields": fields}


def first_match(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return default
    for group in match.groups():
        if group:
            return group
    return match.group(0)


def latest_instructor_utterance(text: str) -> str:
    utterances = re.findall(r'say\(speaker="instructor", utterance="(.*?)"\)', text, re.DOTALL)
    return utterances[-1] if utterances else ""


def sanitize_label(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_.:-]+", "-", value)
    return value.strip("-") or "none"


def truncate_clean(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "..."


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
