#!/usr/bin/env python3
"""Sample labeled agent-trajectory datasets into operation JSONL.

The durable profiler abstraction is an operation plus an operation stack. This
script keeps third-party datasets outside the repository, then emits a small
normalized operation JSONL file that `agentpprof --operation-file` can fold with
the same `--stack`, `--op-map`, and `--stack-rule` machinery used for local traces.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
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
        "repo_file": "data/train/train_10.json",
        "access": "large-repo-json",
        "adapter": "mind2web",
        "source": "https://osu-nlp-group.github.io/Mind2Web/",
        "paper": "https://arxiv.org/abs/2306.06070",
        "why": "Crowdsourced web task action sequences; best as an oracle dataset after full-file download.",
        "note": "Dataset Viewer row groups are too large; use HF repo files or the official raw dump for full runs.",
    },
    "webshop-expert": {
        "title": "WebShop expert trajectories",
        "hf_repo": "lclan/webshop_expert_trajectories",
        "config": "default",
        "split": "test",
        "access": "hf-viewer",
        "adapter": "webshop-expert",
        "source": "https://webshop-pnlp.github.io/",
        "paper": "https://papers.neurips.cc/paper_files/paper/2022/hash/82ad13ec01f9fe44c01cb91814fd7b8c-Abstract-Datasets_and_Benchmarks.html",
        "why": "Human/expert shopping task trajectories with task metadata, rewards, and action conversations.",
    },
    "api-bank": {
        "title": "API-Bank",
        "hf_repo": "liminghao1630/API-Bank",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "api-bank",
        "source": "https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank",
        "paper": "https://arxiv.org/abs/2304.08244",
        "why": "Tool/API-use dialogue instances with gold API request outputs.",
    },
    "agenttrek": {
        "title": "AgentTrek",
        "hf_repo": "xlangai/AgentTrek",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "agenttrek",
        "source": "https://agenttrek.github.io/",
        "paper": "https://arxiv.org/abs/2412.09605",
        "why": "Synthetic-but-verified GUI/web trajectories with action tags from tutorial-guided replay.",
    },
    "swe-agent-trajectories": {
        "title": "SWE-agent trajectories",
        "hf_repo": "nebius/SWE-agent-trajectories",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "swe-agent",
        "source": "https://huggingface.co/datasets/nebius/SWE-agent-trajectories",
        "paper": "https://arxiv.org/abs/2405.15793",
        "why": "Large software-engineering agent trajectories with actions, observations, model name, and success target.",
    },
    "trail": {
        "title": "TRAIL",
        "hf_repo": "PatronusAI/TRAIL",
        "access": "hf-gated-files",
        "source": "https://github.com/patronus-ai/trail-benchmark",
        "paper": "https://arxiv.org/abs/2505.08638",
        "why": "148 human-annotated execution traces with 841 reasoning/planning/execution errors.",
        "note": "HF repo is auto-gated; use after authentication or manual accepted access.",
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
    sample.add_argument("--config", help="Override the HF Dataset Viewer config")
    sample.add_argument("--split", help="Override the HF Dataset Viewer split")
    sample.add_argument("--repo-file", help="Override the HF repo file for large JSON datasets")
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
    dataset = dict(DATASETS[args.dataset])
    if args.config:
        dataset["config"] = args.config
    if args.split:
        dataset["split"] = args.split
    if args.repo_file:
        dataset["repo_file"] = args.repo_file
    if args.limit <= 0:
        raise SystemExit("--limit must be positive")

    out_dir = args.out / args.dataset / f"{dataset['config']}-{dataset['split']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if dataset["access"] == "hf-viewer":
        rows = hf_viewer_rows(dataset, args.offset, args.limit)
    elif dataset["access"] == "large-repo-json":
        rows = hf_repo_json_rows(dataset, out_dir, args.offset, args.limit)
    else:
        note = dataset.get("note", "No lightweight sampler is configured for this dataset.")
        raise SystemExit(f"{args.dataset} is not sampleable by this command: {note}")
    raw_path = out_dir / f"rows-{args.offset}-{args.offset + len(rows)}.jsonl"
    op_path = out_dir / f"operations-{args.offset}-{args.offset + len(rows)}.jsonl"
    manifest_path = out_dir / "manifest.json"

    operations: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        operations.extend(
            normalize_row(args.dataset, dataset, row, args.offset + row_index, args.include_text)
        )
    write_jsonl(raw_path, rows)
    write_jsonl(op_path, operations)
    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset": args.dataset,
        "source": dataset,
        "offset": args.offset,
        "limit": args.limit,
        "rows": len(rows),
        "operations": len(operations),
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
        fallback_first_rows = False
        try:
            payload = get_json(f"{HF_DATASET_VIEWER}/rows?{params}")
        except urllib.error.HTTPError as error:
            if rows:
                break
            if offset != 0:
                raise SystemExit(f"Dataset Viewer rows request failed: HTTP {error.code}") from error
            payload = hf_first_rows(dataset)
            fallback_first_rows = True
        if "error" in payload:
            raise SystemExit(payload["error"])
        batch = [entry["row"] for entry in payload.get("rows", [])]
        if not batch:
            break
        rows.extend(batch[: limit - len(rows)])
        if fallback_first_rows:
            break
    return rows


def hf_first_rows(dataset: dict[str, Any]) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "dataset": dataset["hf_repo"],
            "config": dataset["config"],
            "split": dataset["split"],
        }
    )
    return get_json(f"{HF_DATASET_VIEWER}/first-rows?{params}")


def hf_repo_json_rows(
    dataset: dict[str, Any], out_dir: Path, offset: int, limit: int
) -> list[dict[str, Any]]:
    repo_file = dataset["repo_file"]
    source_path = out_dir / Path(repo_file).name
    if not source_path.exists():
        encoded = urllib.parse.quote(repo_file)
        url = f"https://huggingface.co/datasets/{dataset['hf_repo']}/resolve/main/{encoded}"
        with urllib.request.urlopen(url, timeout=120) as response:
            source_path.write_bytes(response.read())
    with source_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise SystemExit(f"{repo_file} did not contain a JSON list")
    return payload[offset : offset + limit]


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_row(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    adapter = dataset.get("adapter")
    if adapter == "weblinx-chat":
        return [normalize_weblinx_chat(dataset_id, dataset, row, include_text)]
    if adapter == "mind2web":
        return normalize_mind2web(dataset_id, dataset, row, include_text)
    if adapter == "webshop-expert":
        return normalize_webshop_expert(dataset_id, dataset, row, include_text)
    if adapter == "api-bank":
        return [normalize_api_bank(dataset_id, dataset, row, row_index, include_text)]
    if adapter == "agenttrek":
        return normalize_agenttrek(dataset_id, dataset, row, row_index, include_text)
    if adapter == "swe-agent":
        return normalize_swe_agent(dataset_id, dataset, row, row_index, include_text)
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


def normalize_mind2web(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> list[dict[str, Any]]:
    session = str(row.get("annotation_id") or stable_id(row))
    task = sanitize_label(str(row.get("domain") or "web-task"))
    operations = []
    action_reprs = row.get("action_reprs") or []
    for turn, action in enumerate(row.get("actions") or []):
        operation = action.get("operation") or {}
        action_name = sanitize_label(str(operation.get("op") or operation.get("original_op") or "unknown"))
        original = sanitize_label(str(operation.get("original_op") or action_name))
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-demo",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": task,
            "phase": action_name,
            "op": "action",
            "tool": "browser",
            "action": action_name,
            "original_action": original,
            "website": sanitize_label(str(row.get("website") or "unknown")),
            "domain": sanitize_label(str(row.get("domain") or "unknown")),
            "subdomain": sanitize_label(str(row.get("subdomain") or "unknown")),
            "status": "gold",
        }
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("confirmed_task") or ""), 180)
            if turn < len(action_reprs):
                fields["action_raw"] = truncate_clean(str(action_reprs[turn]), 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_webshop_expert(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> list[dict[str, Any]]:
    info = row.get("info") or {}
    session = str(row.get("id") or stable_id(row))
    reward = int(info.get("reward") or 0)
    task = sanitize_label(str(info.get("task_name") or "webshop-task"))
    operations = []
    for turn, message in enumerate(row.get("conversations") or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content") or "")
        action = extract_action_block(content)
        if not action:
            continue
        action_name = action_verb(action)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": str(info.get("agent_arch") or "expert"),
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": task,
            "phase": action_name,
            "op": "action",
            "tool": "webshop",
            "action": action_name,
            "status": "success" if reward > 0 else "unknown",
            "score": str(message.get("score") or reward),
        }
        if include_text:
            fields["action_raw"] = truncate_clean(action, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_api_bank(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> dict[str, Any]:
    output = str(row.get("output") or "")
    api_name = first_match(r"\[([A-Za-z_][A-Za-z0-9_]*)\(", output, "unknown_api")
    domain = first_match(r'"apiCode":\s*"([A-Za-z_][A-Za-z0-9_]*)"', str(row.get("input") or ""), api_name)
    fields: dict[str, Any] = {
        "project": "external-agent-traces",
        "agent": "gold-api",
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": f"api-bank-{row_index}",
        "task": "api-call",
        "phase": "api",
        "op": "tool",
        "tool": "api",
        "action": sanitize_label(api_name),
        "domain": sanitize_label(domain),
        "status": "gold",
    }
    if include_text:
        fields["action_raw"] = truncate_clean(output, 180)
    return {"value": 1, "fields": fields}


def normalize_agenttrek(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    operations = []
    session = f"agenttrek-{row_index}"
    for turn, message in enumerate(row.get("messages") or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content") or "")
        action = first_match(r"<action>\s*(.*?)\s*</action>", content, "")
        if not action:
            continue
        action_name = action_verb(action)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "vlm-agent",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "web-gui",
            "phase": action_name,
            "op": "action",
            "tool": "browser",
            "action": action_name,
            "status": "verified",
        }
        if include_text:
            fields["action_raw"] = truncate_clean(action, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_swe_agent(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    operations = []
    session = str(row.get("instance_id") or f"swe-{row_index}")
    status = str(row.get("exit_status") or "unknown")
    success = "success" if row.get("target") is True else "failure"
    for turn, event in enumerate(row.get("trajectory") or []):
        role = str(event.get("role") or "")
        if role not in {"ai", "assistant"}:
            continue
        text = str(event.get("text") or "")
        command = extract_code_command(text)
        if not command:
            continue
        command_name = action_verb(command)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": sanitize_label(str(row.get("model_name") or "swe-agent")),
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "software-issue",
            "phase": command_name,
            "op": "tool",
            "tool": "swe-agent",
            "action": command_name,
            "cmd": command_name,
            "status": success,
            "exit": sanitize_label(status),
        }
        if include_text:
            fields["command"] = truncate_clean(command, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def first_match(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return default
    for group in match.groups():
        if group:
            return group
    return match.group(0)


def extract_action_block(text: str) -> str:
    match = re.search(r"Action:\s*(.*)", text, re.DOTALL)
    if not match:
        return ""
    action = match.group(1).strip()
    return action.splitlines()[0].strip()


def extract_code_command(text: str) -> str:
    match = re.search(r"```(?:[A-Za-z0-9_-]+)?\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        return ""
    command = match.group(1).strip()
    return command.splitlines()[0].strip()


def action_verb(action: str) -> str:
    action = action.strip()
    if not action:
        return "unknown"
    verb = first_match(r"^([A-Za-z_][A-Za-z0-9_-]*)", action, "unknown")
    return sanitize_label(verb)


def stable_id(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


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
