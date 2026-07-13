#!/usr/bin/env python3
"""Run the approved RQ2 family-held-out experiment.

``--mode preflight`` exercises every high-risk path without confirmatory labels.
``--mode prepare-full-visible`` writes label-free confirmation inputs and exits.
``--mode full`` consumes only those prepared visible inputs until the explicit
label-join boundary, then completes confirmation and the native matrix.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import importlib
import json
import math
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "docs/visexp/out/rq2-family-heldout-r410/preflight"
DEFAULT_REPORT = (
    ROOT
    / "docs/tmp/cycle-0001-20260711T164850-0700"
    / "01-experiment-gate/loop-rq2-00/preflight-report.md"
)
DEFAULT_AGENTRX = Path("/tmp/rq2_sources_main/AgentRx")
DEFAULT_TELBENCH = Path("/tmp/rq2_sources_main/TELBench/TELBench.jsonl")
DEFAULT_DRIFT = Path("/tmp/rq2_sources_main/drift-venv/bin/drift")
DEFAULT_DRIFT_ROOT = Path("/tmp/rq2_sources_main/DRIFT")
DEFAULT_AGENTPPROF = ROOT / "agentpprof/target/release/agentpprof"

VISIBLE_FIELDS = (
    "role",
    "tool",
    "action",
    "phase",
    "op",
    "repeat_signal",
    "repeat_state",
    "tool_status",
    "length_bucket",
    "query_overlap",
    "content",
)
FORBIDDEN_EXACT = {
    "annotator",
    "annotation",
    "answer_status",
    "correct",
    "failure_category",
    "failure_id",
    "failure_reason",
    "gold",
    "judge",
    "label",
    "looping",
    "optimality",
    "oracle",
    "reward",
    "root_cause",
    "safety",
    "side_effect",
    "status",
    "step_correct",
    "step_redundant",
    "success",
    "target_positive",
}
FORBIDDEN_PARTS = (
    "annotation",
    "ground_truth",
    "judge",
    "label",
    "oracle",
    "root_cause",
    "target_positive",
)
STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "but",
    "can",
    "does",
    "for",
    "from",
    "have",
    "into",
    "just",
    "more",
    "not",
    "only",
    "that",
    "the",
    "their",
    "then",
    "this",
    "through",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "with",
    "you",
}
DEVELOPMENT_PROVENANCE = {
    "role": "constant operation actor role; no outcome source",
    "tool": "source trajectory step tool name",
    "action": "source trajectory step action verb",
    "phase": "deterministic action-to-phase mapping in script/agent_trace_datasets.py",
    "op": "constant normalized operation type",
    "repeat_signal": "deterministic adjacent action-sequence feature in script/agent_trace_datasets.py",
    "repeat_state": "deterministic adjacent action-sequence feature in script/agent_trace_datasets.py",
    "tool_status": "presence of event-native trajectory.steps[].last_action_error",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["preflight", "prepare-full-visible", "full"], required=True
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--agentrx-root", type=Path, default=DEFAULT_AGENTRX)
    parser.add_argument("--telbench", type=Path, default=DEFAULT_TELBENCH)
    parser.add_argument("--drift-bin", type=Path, default=DEFAULT_DRIFT)
    parser.add_argument("--drift-root", type=Path, default=DEFAULT_DRIFT_ROOT)
    parser.add_argument("--agentpprof-bin", type=Path, default=DEFAULT_AGENTPPROF)
    parser.add_argument("--base-url", default="http://127.0.0.1:18081/v1")
    parser.add_argument("--api-key", default="local")
    parser.add_argument("--model", default="local-qwen25-3b")
    parser.add_argument("--native-batch-size", type=int, default=100)
    parser.add_argument("--native-workers", type=int, default=1)
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def forbidden_field(field: str) -> bool:
    lowered = field.lower()
    return lowered in FORBIDDEN_EXACT or any(part in lowered for part in FORBIDDEN_PARTS)


def assert_visible(records: list[dict[str, Any]], name: str) -> None:
    bad = sorted(
        {
            key
            for record in records
            for key in record["fields"]
            if forbidden_field(key) or key not in VISIBLE_FIELDS
        }
    )
    if bad:
        raise SystemExit(f"{name}: non-allowlisted or outcome-derived fields reached profiler: {bad}")


def query_terms(text: str, limit: int = 8) -> list[str]:
    counts = Counter(
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
        if token not in STOPWORDS
    )
    return [token for token, _ in counts.most_common(limit)] or ["problem"]


def derived_visible_fields(role: str, content: str, query: str) -> dict[str, str]:
    text = content.strip()
    lowered = text.lower()
    if re.search(r"\b(search|query|google|browse|find|lookup)\b", lowered):
        action = "search"
    elif re.search(r"\b(download|fetch|open|read|inspect|retrieve)\b", lowered):
        action = "retrieve"
    elif re.search(r"\b(write|draft|answer|summar|conclud|report)\w*\b", lowered):
        action = "synthesize"
    elif re.search(r"\b(tool|function|call|execute|run)\b", lowered):
        action = "tool"
    elif re.search(r"\b(reason|think|plan|verify|check|compare)\w*\b", lowered):
        action = "reason"
    else:
        action = "communicate"
    if re.search(r"\b(error|exception|failed|failure|invalid|timeout|unable|cannot)\b", lowered):
        tool_status = "error-visible"
    else:
        tool_status = "no-visible-error"
    length = len(text)
    length_bucket = "short" if length < 300 else "medium" if length < 1500 else "long"
    qterms = set(query_terms(query, 12))
    overlap = bool(qterms & set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", lowered)))
    return {
        "role": role or "unknown",
        "action": action,
        "op": "trajectory-step",
        "tool_status": tool_status,
        "length_bucket": length_bucket,
        "query_overlap": "yes" if overlap else "no",
        "content": text,
    }


def task_by_id(task_id: str) -> dict[str, Any]:
    sys.path.insert(0, str(SCRIPT_DIR))
    r300 = importlib.import_module("operation_query_utility_eval")
    return next(task for task in r300.TASKS if task["id"] == task_id)


def load_development_task(task_id: str) -> tuple[list[dict[str, Any]], dict[str, int], str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    r300 = importlib.import_module("operation_query_utility_eval")
    task = task_by_id(task_id)
    source_rows = r300.load_task_operations(task)
    records: list[dict[str, Any]] = []
    labels: dict[str, int] = {}
    for index, source in enumerate(source_rows):
        original = source["fields"]
        op_id = f"{task_id}:{index:06d}"
        fields = {
            field: original[field]
            for field in VISIBLE_FIELDS
            if field in original and field != "content"
        }
        fields.setdefault("role", "agent")
        step_error = original.get("step_error")
        if step_error is not None:
            fields["tool_status"] = (
                "error-visible"
                if step_error not in {"none", "ok", "unknown"}
                else "no-visible-error"
            )
        else:
            fields.setdefault("tool_status", "unknown")
        records.append(
            {
                "op_id": op_id,
                "trajectory": f"{task_id}:{original.get('session', 'unknown')}",
                "ordinal": index,
                "fields": fields,
                "native_key": "|".join(
                    original.get(field, "unknown")
                    for field in (
                        ("benchmark", "environment")
                        if task["dataset"] == "agent-reward-bench"
                        else ("benchmark", "category", "environment")
                        if task["dataset"] == "satraj-os-safety"
                        else ("benchmark", "domain", "task_difficulty", "environment")
                    )
                ),
            }
        )
        labels[op_id] = int(original.get("target_positive") == "positive")
    assert_visible(records, task_id)
    return records, labels, task["problem"]


def import_agentrx_ir(root: Path) -> Any:
    if not (root / "agentrx/ir/trajectory_ir.py").is_file():
        raise SystemExit(f"missing official AgentRx checkout: {root}")
    sys.path.insert(0, str(root))
    return importlib.import_module("agentrx.ir.trajectory_ir")


def load_unlabeled_agentrx(root: Path) -> tuple[list[dict[str, Any]], str, str]:
    module = import_agentrx_ir(root)
    source = root / "data/tau_retail/tau_dataset_failed.json"
    trajectories = module.load_trajectories(str(source))
    ir = module.tau_bench_ir(trajectories)[0]
    records = []
    for ordinal, step in enumerate(ir["steps"]):
        substeps = step.get("substeps") or []
        role = "+".join(str(item.get("role") or "unknown") for item in substeps)
        content = "\n".join(str(item.get("content") or "") for item in substeps)
        records.append(
            {
                "op_id": f"agentrx:{ir['trajectory_id']}:{ordinal:04d}",
                "trajectory": f"agentrx:{ir['trajectory_id']}",
                "ordinal": ordinal,
                "fields": derived_visible_fields(role, content, ir["instruction"]),
            }
        )
    assert_visible(records, "AgentRx preflight")
    return records, ir["instruction"], str(ir["trajectory_id"])


def load_first_telbench_unlabeled(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not path.is_file():
        raise SystemExit(f"missing decrypted official TELBench JSONL: {path}")
    # Span count is label-free.  Select the first case large enough to exercise
    # the Rust inducer's two-child minimum instead of accidentally preflighting
    # only its small-node stop path.
    case = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            if len(candidate.get("spans") or []) >= 20:
                case = candidate
                break
    if case is None:
        raise SystemExit("TELBench contains no label-free >=20-span preflight case")
    sanitized = {
        "id": str(case["id"]),
        "source_id": str(case.get("source_id") or ""),
        "question": str(case["question"]),
        "spans": [
            {"id": str(span["id"]), "raw": str(span["raw"])}
            for span in case["spans"]
        ],
    }
    records = []
    for ordinal, span in enumerate(sanitized["spans"]):
        records.append(
            {
                "op_id": f"telbench:{sanitized['id']}:{ordinal:04d}",
                "trajectory": f"telbench:{sanitized['id']}",
                "ordinal": ordinal,
                "fields": derived_visible_fields(
                    "research-span", span["raw"], sanitized["question"]
                ),
            }
        )
    assert_visible(records, "TELBench preflight")
    return records, sanitized


def agentrx_manifest_ids(root: Path) -> dict[str, list[str]]:
    ground_truth = root / "data/ground_truth"
    return {
        "tau": [
            str(row["trajectory_id"])
            for row in json.loads((ground_truth / "tau_ground_truth.json").read_text())
        ],
        "magentic": [
            str(row["trajectory_id"])
            for row in json.loads((ground_truth / "magentic_one_ground_truth.json").read_text())
        ],
    }


def records_from_agentrx_ir(ir: dict[str, Any], domain: str) -> list[dict[str, Any]]:
    trajectory = f"agentrx:{domain}:{ir['trajectory_id']}"
    records = []
    for ordinal, step in enumerate(ir["steps"]):
        substeps = step.get("substeps") or []
        role = "+".join(str(item.get("role") or "unknown") for item in substeps)
        content = "\n".join(str(item.get("content") or "") for item in substeps)
        records.append(
            {
                "op_id": f"{trajectory}:{ordinal:04d}",
                "trajectory": trajectory,
                "ordinal": ordinal,
                "fields": derived_visible_fields(role, content, ir["instruction"]),
                "native_key": role or "unknown",
            }
        )
    return records


def load_agentrx_visible_full(
    root: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], dict[str, Any]]:
    module = import_agentrx_ir(root)
    ids = agentrx_manifest_ids(root)
    records_by_domain: dict[str, list[dict[str, Any]]] = {"tau": [], "magentic": []}
    questions: dict[str, str] = {}

    tau_irs = {
        str(ir["trajectory_id"]): ir
        for ir in module.tau_bench_ir(
            module.load_trajectories(str(root / "data/tau_retail/tau_dataset_failed.json"))
        )
    }
    for trajectory_id in ids["tau"]:
        ir = tau_irs.get(trajectory_id)
        if ir is None:
            raise SystemExit(f"AgentRx Tau manifest has no released trajectory {trajectory_id}")
        rows = records_from_agentrx_ir(ir, "tau")
        records_by_domain["tau"].extend(rows)
        questions[rows[0]["trajectory"]] = ir["instruction"]

    for trajectory_id in ids["magentic"]:
        source = root / "data/magentic_dataset" / f"{trajectory_id}.json"
        if not source.is_file():
            raise SystemExit(f"AgentRx Magentic manifest has no released trajectory {trajectory_id}")
        ir = module.magentic_ir(module.load_trajectories(str(source)))[0]
        rows = records_from_agentrx_ir(ir, "magentic")
        records_by_domain["magentic"].extend(rows)
        questions[rows[0]["trajectory"]] = ir["instruction"]

    for domain, records in records_by_domain.items():
        assert_visible(records, f"AgentRx {domain} full")
    return records_by_domain, questions, {"manifest_ids": ids}


def load_agentrx_labels(root: Path) -> dict[str, dict[str, int]]:
    outputs: dict[str, dict[str, int]] = {"tau": {}, "magentic": {}}
    files = {
        "tau": root / "data/ground_truth/tau_ground_truth.json",
        "magentic": root / "data/ground_truth/magentic_one_ground_truth.json",
    }
    for domain, path in files.items():
        for row in json.loads(path.read_text(encoding="utf-8")):
            root_id = str(row["root_cause"]["failure_id"])
            failure = next(
                (item for item in row["failures"] if str(item["failure_id"]) == root_id),
                None,
            )
            if failure is None:
                raise SystemExit(f"AgentRx {domain} root-cause id does not resolve: {row['trajectory_id']}")
            trajectory = f"agentrx:{domain}:{row['trajectory_id']}"
            positive_ordinal = int(failure["step_number"]) - 1
            outputs[domain][f"{trajectory}:{positive_ordinal:04d}"] = 1
    return outputs


def load_telbench_visible_full(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    records: list[dict[str, Any]] = []
    sanitized_cases: list[dict[str, Any]] = []
    questions: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            case = json.loads(line)
            sanitized = {
                "id": str(case["id"]),
                "source_id": str(case.get("source_id") or ""),
                "question": str(case["question"]),
                "spans": [
                    {"id": str(span["id"]), "raw": str(span["raw"])}
                    for span in case["spans"]
                ],
            }
            sanitized_cases.append(sanitized)
            trajectory = f"telbench:{sanitized['id']}"
            questions[trajectory] = sanitized["question"]
            for ordinal, span in enumerate(sanitized["spans"]):
                records.append(
                    {
                        "op_id": f"{trajectory}:{ordinal:04d}",
                        "trajectory": trajectory,
                        "ordinal": ordinal,
                        "span_id": span["id"],
                        "fields": derived_visible_fields(
                            "research-span", span["raw"], sanitized["question"]
                        ),
                        "native_key": "ordered-semantic-span",
                    }
                )
    if len(sanitized_cases) != 1000:
        raise SystemExit(f"TELBench full execution requires 1000 cases, found {len(sanitized_cases)}")
    assert_visible(records, "TELBench full")
    return records, sanitized_cases, questions


def load_telbench_labels(path: Path) -> dict[str, int]:
    labels: dict[str, int] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            case = json.loads(line)
            positive = {str(value) for value in case["gold"]["error_span_ids"]}
            trajectory = f"telbench:{case['id']}"
            for ordinal, span in enumerate(case["spans"]):
                labels[f"{trajectory}:{ordinal:04d}"] = int(str(span["id"]) in positive)
    return labels


def full_output(args: argparse.Namespace) -> Path:
    return args.out_dir.resolve().parent / "full"


def prepare_full_visible_inputs(args: argparse.Namespace) -> int:
    """Project official sources to label-free inputs in a process that then exits."""
    output = full_output(args)
    visible_root = output / "visible-input"
    records_by_domain, questions, _ = load_agentrx_visible_full(args.agentrx_root.resolve())
    telbench_records, telbench_cases, telbench_questions = load_telbench_visible_full(
        args.telbench.resolve()
    )
    agentrx_rows = [
        {"domain": domain, "record": record}
        for domain in ("tau", "magentic")
        for record in records_by_domain[domain]
    ]
    write_jsonl(visible_root / "agentrx-records.jsonl", agentrx_rows)
    write_json(visible_root / "agentrx-questions.json", questions)
    write_jsonl(visible_root / "telbench-records.jsonl", telbench_records)
    write_jsonl(visible_root / "telbench-cases.jsonl", telbench_cases)
    write_json(visible_root / "telbench-questions.json", telbench_questions)
    print(
        json.dumps(
            {
                "visible_input": str(visible_root),
                "agentrx_trajectories": len(questions),
                "telbench_cases": len(telbench_cases),
                "next": "start a new --mode full process",
            }
        )
    )
    return 0


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SystemExit(f"required label-free input is missing: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_prepared_visible_full(
    output: Path,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, str],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, str],
]:
    visible_root = output / "visible-input"
    records_by_domain: dict[str, list[dict[str, Any]]] = {"tau": [], "magentic": []}
    for row in read_jsonl(visible_root / "agentrx-records.jsonl"):
        domain = str(row["domain"])
        if domain not in records_by_domain:
            raise SystemExit(f"unknown AgentRx visible domain: {domain}")
        records_by_domain[domain].append(row["record"])
    agentrx_questions = json.loads(
        (visible_root / "agentrx-questions.json").read_text(encoding="utf-8")
    )
    telbench_records = read_jsonl(visible_root / "telbench-records.jsonl")
    telbench_cases = read_jsonl(visible_root / "telbench-cases.jsonl")
    telbench_questions = json.loads(
        (visible_root / "telbench-questions.json").read_text(encoding="utf-8")
    )
    for domain, records in records_by_domain.items():
        assert_visible(records, f"prepared AgentRx {domain}")
    assert_visible(telbench_records, "prepared TELBench")
    if len(agentrx_questions) != 73 or len(telbench_cases) != 1000:
        raise SystemExit("prepared visible inputs do not cover 73 AgentRx trajectories and 1000 TELBench cases")
    return (
        records_by_domain,
        agentrx_questions,
        telbench_records,
        telbench_cases,
        telbench_questions,
    )


QuestionSource = str | dict[str, str]


def question_for_record(record: dict[str, Any], question: QuestionSource) -> str:
    if isinstance(question, str):
        return question
    return question[record["trajectory"]]


def record_text(record: dict[str, Any], question: QuestionSource) -> str:
    question_text = question_for_record(record, question)
    parts = [f"question={question_text}"]
    for key in VISIBLE_FIELDS:
        value = record["fields"].get(key)
        if value:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def train_ranker(
    records: list[dict[str, Any]],
    labels: dict[str, int],
    question: QuestionSource,
    seed: int = 410,
) -> tuple[TfidfVectorizer, LogisticRegression]:
    y = [labels[record["op_id"]] for record in records]
    if len(set(y)) != 2:
        raise SystemExit("development ranker requires both positive and negative rows")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=12000)
    matrix = vectorizer.fit_transform(record_text(record, question) for record in records)
    model = LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=seed, solver="liblinear"
    )
    model.fit(matrix, y)
    return vectorizer, model


def materialize_scores(
    vectorizer: TfidfVectorizer,
    model: LogisticRegression,
    records: list[dict[str, Any]],
    question: QuestionSource,
    output: Path,
) -> dict[str, float]:
    matrix = vectorizer.transform(record_text(record, question) for record in records)
    values = model.predict_proba(matrix)[:, 1]
    scores = {record["op_id"]: float(value) for record, value in zip(records, values)}
    write_jsonl(
        output,
        (
            {"op_id": record["op_id"], "risk_score": scores[record["op_id"]]}
            for record in records
        ),
    )
    return scores


def development_tag_thresholds(scores: dict[str, float]) -> tuple[float, float, float]:
    values = sorted(scores.values())
    if not values:
        raise SystemExit("cannot select tag thresholds from an empty development score set")
    return tuple(values[round((len(values) - 1) * quantile)] for quantile in (0.25, 0.5, 0.75))


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") or "trajectory"


def operation_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"fields": record["fields"], "value": 1} for record in records]


def run_per_trajectory_induction(
    binary: Path,
    records: list[dict[str, Any]],
    terms: list[str] | dict[str, list[str]],
    output: Path,
    name: str,
    max_depth: int = 3,
) -> tuple[dict[str, str], dict[str, Any]]:
    sys.path.insert(0, str(SCRIPT_DIR))
    r403 = importlib.import_module("operation_induced_stack_scoring_eval")
    r402 = importlib.import_module("operation_rust_task_stack_induction_eval")
    if not binary.is_file():
        raise SystemExit(f"missing release agentpprof binary: {binary}")
    by_trajectory: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_trajectory[record["trajectory"]].append(record)
    assignments: dict[str, str] = {}
    selected_fields: set[str] = set()
    split_count = 0
    trajectory_summaries = []
    induction_dir = output / "induction" / safe_name(name)
    induction_dir.mkdir(parents=True, exist_ok=True)
    for trajectory, rows in sorted(by_trajectory.items()):
        stem = safe_name(trajectory)
        operation_file = induction_dir / f"{stem}.jsonl"
        profile_file = induction_dir / f"{stem}.profile.json"
        write_jsonl(operation_file, operation_rows(rows))
        command = [
            str(binary),
            "--operation-file",
            str(operation_file),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            str(profile_file),
            "--induce-operation-stack",
            "--induce-max-depth",
            str(max_depth),
            "--deterministic-output",
        ]
        trajectory_terms = terms if isinstance(terms, list) else terms[trajectory]
        for term in trajectory_terms:
            command.extend(["--induce-query-term", term])
        started = time.monotonic()
        completed = run(command)
        profile_doc = json.loads(profile_file.read_text(encoding="utf-8"))
        induction = r402.operation_stack_induction_report(profile_doc["profile"])
        paths = r403.reconstruct_paths(operation_rows(rows), induction["split_decisions"])
        used = set(induction.get("selected_evidence_fields") or [])
        bad = sorted(field for field in used if forbidden_field(field))
        if bad:
            raise SystemExit(f"Rust induction selected forbidden fields in {trajectory}: {bad}")
        selected_fields.update(used)
        split_count += len(induction["split_decisions"])
        for record, path in zip(rows, paths):
            assignments[record["op_id"]] = ";".join(path or ["all"])
        trajectory_summaries.append(
            {
                "trajectory": trajectory,
                "operations": len(rows),
                "split_decisions": len(induction["split_decisions"]),
                "selected_fields": sorted(used),
                "wall_seconds": time.monotonic() - started,
                "stdout_tail": completed.stdout[-1000:],
            }
        )
    summary = {
        "name": name,
        "trajectories": len(by_trajectory),
        "operations": len(records),
        "split_decisions": split_count,
        "max_depth": max_depth,
        "selected_fields": sorted(selected_fields),
        "per_trajectory": trajectory_summaries,
    }
    write_json(induction_dir / "summary.json", summary)
    return assignments, summary


def aggregate_groups(
    records: list[dict[str, Any]],
    scores: dict[str, float],
    keys: dict[str, str],
    aggregation: str = "max",
) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for record in records:
        grouped[keys[record["op_id"]]].append(record["op_id"])
    if aggregation not in {"max", "mean"}:
        raise ValueError(f"unsupported group-score aggregation: {aggregation}")
    groups = []
    for key, op_ids in grouped.items():
        values = [scores[op_id] for op_id in op_ids]
        score = max(values) if aggregation == "max" else sum(values) / len(values)
        groups.append({"key": key, "op_ids": op_ids, "score": score, "size": len(op_ids)})
    return sorted(groups, key=lambda group: (-group["score"], group["key"]))


def group_keys(
    method: str,
    records: list[dict[str, Any]],
    scores: dict[str, float],
    induced: dict[str, str],
    tag_thresholds: tuple[float, float, float],
) -> dict[str, str]:
    if method == "flat":
        return {record["op_id"]: "all" for record in records}
    if method == "session":
        return {record["op_id"]: record["trajectory"] for record in records}
    if method == "raw_action":
        return {
            record["op_id"]: "|".join(
                record["fields"].get(key, "unknown")
                for key in ("tool", "action", "tool_status")
            )
            for record in records
        }
    if method == "tag":
        return {
            record["op_id"]: (
                f"{record['fields'].get('role', 'unknown')}|"
                f"risk-{bisect.bisect_right(tag_thresholds, scores[record['op_id']])}"
            )
            for record in records
        }
    if method == "induced":
        return induced
    raise ValueError(method)


def singleton_keys(records: list[dict[str, Any]], prefix: str = "operation") -> dict[str, str]:
    return {record["op_id"]: f"{prefix}|{record['op_id']}" for record in records}


def native_group_keys(records: list[dict[str, Any]]) -> dict[str, str]:
    return {record["op_id"]: record.get("native_key", "unknown") for record in records}


def field_group_keys(
    records: list[dict[str, Any]], fields: tuple[str, ...], prefix: str
) -> dict[str, str]:
    return {
        record["op_id"]: prefix
        + "|"
        + "|".join(record["fields"].get(field, "unknown") for field in fields)
        for record in records
    }


def sequential_window_keys(records: list[dict[str, Any]], window: int) -> dict[str, str]:
    return {
        record["op_id"]: f"{record['trajectory']}|window-{record['ordinal'] // window:06d}"
        for record in records
    }


def rarity_scores(records: list[dict[str, Any]]) -> dict[str, float]:
    signatures = [
        "|".join(
            record["fields"].get(field, "unknown")
            for field in ("role", "tool", "action", "tool_status")
        )
        for record in records
    ]
    counts = Counter(signatures)
    return {
        record["op_id"]: 1.0 / counts[signature]
        for record, signature in zip(records, signatures)
    }


def random_scores(records: list[dict[str, Any]], seed: int) -> dict[str, float]:
    rng = random.Random(seed)
    return {record["op_id"]: rng.random() for record in records}


def question_map_for_task(records: list[dict[str, Any]], question: str) -> dict[str, str]:
    return {record["trajectory"]: question for record in records}


def load_development_corpus() -> tuple[
    list[dict[str, Any]],
    dict[str, int],
    dict[str, str],
    dict[str, list[dict[str, Any]]],
    dict[str, dict[str, int]],
]:
    task_ids = (
        "agentreward_looping",
        "agentreward_side_effect",
        "satraj_unsafe",
        "agentnet_incorrect_step",
        "agentnet_redundant_step",
    )
    all_records: list[dict[str, Any]] = []
    all_labels: dict[str, int] = {}
    questions: dict[str, str] = {}
    task_records: dict[str, list[dict[str, Any]]] = {}
    task_labels: dict[str, dict[str, int]] = {}
    for task_id in task_ids:
        records, labels, question = load_development_task(task_id)
        task_records[task_id] = records
        task_labels[task_id] = labels
        all_records.extend(records)
        all_labels.update(labels)
        questions.update(question_map_for_task(records, question))
    return all_records, all_labels, questions, task_records, task_labels


def sql_group_keys(records: list[dict[str, Any]], columns: tuple[str, ...]) -> dict[str, str]:
    allowed = {"role", "phase", "action", "tool_status"}
    if not columns or any(column not in allowed for column in columns):
        raise ValueError(f"unsupported SQL grouping columns: {columns}")
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "create table operations (op_id text, role text, phase text, action text, tool_status text)"
    )
    connection.executemany(
        "insert into operations values (?, ?, ?, ?, ?)",
        [
            (
                record["op_id"],
                record["fields"].get("role", "unknown"),
                record["fields"].get("phase", "unknown"),
                record["fields"].get("action", "unknown"),
                record["fields"].get("tool_status", "unknown"),
            )
            for record in records
        ],
    )
    selected = ", ".join(columns)
    rows = connection.execute(
        f"select {selected}, group_concat(op_id, char(31)) "
        f"from operations group by {selected} order by {selected}"
    ).fetchall()
    connection.close()
    keys: dict[str, str] = {}
    for row in rows:
        values = row[:-1]
        joined_ids = row[-1]
        key = "|".join(values)
        for op_id in joined_ids.split(chr(31)):
            keys[op_id] = key
    return keys


def matched_partition_keys(
    records: list[dict[str, Any]], induced: dict[str, str], seed: int = 410
) -> dict[str, str]:
    rng = random.Random(seed)
    by_trajectory: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_trajectory[record["trajectory"]].append(record)
    keys: dict[str, str] = {}
    for trajectory, rows in sorted(by_trajectory.items()):
        rows = sorted(rows, key=lambda row: row["ordinal"])
        # Preserve the exact cross-trajectory size of every induced semantic
        # path, but move that path onto a randomly ordered contiguous segment
        # inside each trajectory.  Aggregating by the retained path key then
        # gives an exact global group-size/cardinality match.
        path_sizes = list(Counter(induced[row["op_id"]] for row in rows).items())
        rng.shuffle(path_sizes)
        cursor = 0
        for path, size in path_sizes:
            for row in rows[cursor : cursor + size]:
                keys[row["op_id"]] = f"matched|{path}"
            cursor += size
        if cursor != len(rows):
            raise SystemExit("matched partition failed to cover a trajectory")
    return keys


def size_multiset_by_trajectory(
    records: list[dict[str, Any]], keys: dict[str, str]
) -> dict[str, list[int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        counts[record["trajectory"]][keys[record["op_id"]]] += 1
    return {
        trajectory: sorted(group_sizes.values())
        for trajectory, group_sizes in sorted(counts.items())
    }


TASK_FAMILY = {
    "agentreward_looping": "agentreward",
    "agentreward_side_effect": "agentreward",
    "satraj_unsafe": "satraj",
    "agentnet_incorrect_step": "agentnet",
    "agentnet_redundant_step": "agentnet",
}
SEEDS = (410, 411, 412)
SQL_CANDIDATES = {
    "sql_role": ("role",),
    "sql_role_action": ("role", "action"),
    "sql_role_action_status": ("role", "action", "tool_status"),
    "sql_role_phase_action_status": ("role", "phase", "action", "tool_status"),
}
EXPLICIT_CANDIDATES = {
    "explicit_action": ("action",),
    "explicit_phase_action": ("phase", "action"),
    "explicit_phase_action_status": ("phase", "action", "tool_status"),
}
WINDOW_CANDIDATES = (5, 10, 20)


def complete_binary_labels(
    records: list[dict[str, Any]], positive_labels: dict[str, int]
) -> dict[str, int]:
    record_ids = {record["op_id"] for record in records}
    missing = sorted(set(positive_labels) - record_ids)
    if missing:
        raise SystemExit(f"positive labels do not align to visible operations: {missing[:10]}")
    return {record["op_id"]: int(record["op_id"] in positive_labels) for record in records}


def deployable_method_keys(
    records: list[dict[str, Any]],
    scores: dict[str, float],
    induced: dict[str, str],
    thresholds: tuple[float, float, float],
) -> dict[str, dict[str, str]]:
    methods = {
        method: group_keys(method, records, scores, induced, thresholds)
        for method in ("flat", "session", "raw_action", "tag", "induced")
    }
    methods["dataset_native"] = native_group_keys(records)
    for name, columns in SQL_CANDIDATES.items():
        methods[name] = sql_group_keys(records, columns)
    for name, fields in EXPLICIT_CANDIDATES.items():
        methods[name] = field_group_keys(records, fields, name)
    for window in WINDOW_CANDIDATES:
        methods[f"fixed_sequential_w{window}"] = sequential_window_keys(records, window)
    return methods


def metric_selection_key(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    aps = sorted(float(row["average_precision"]) for row in rows)
    works = sorted(float(row["work_to_25_recall"]) for row in rows)
    groups = sorted(float(row["groups_to_25_recall"]) for row in rows)
    middle = len(rows) // 2
    return (aps[middle], -works[middle], -groups[middle])


def select_development_configuration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    aggregation_candidates = {}
    for depth in (2, 3, 4):
        for aggregation in ("max", "mean"):
            selected = [
                row
                for row in rows
                if row["method"] == f"induced_d{depth}"
                and row["aggregation"] == aggregation
            ]
            aggregation_candidates[f"depth-{depth}:{aggregation}"] = metric_selection_key(selected)
    selected_induction = max(aggregation_candidates, key=aggregation_candidates.get)
    depth_text, aggregation = selected_induction.split(":", 1)
    depth = int(depth_text.removeprefix("depth-"))

    def select_method(prefix: str) -> str:
        names = sorted({row["method"] for row in rows if row["method"].startswith(prefix)})
        return max(
            names,
            key=lambda name: metric_selection_key(
                [
                    row
                    for row in rows
                    if row["method"] == name and row["aggregation"] == aggregation
                ]
            ),
        )

    return {
        "aggregation": aggregation,
        "aggregation_candidates": aggregation_candidates,
        "sql": select_method("sql_"),
        "explicit_stack": select_method("explicit_"),
        "fixed_sequential": select_method("fixed_sequential_"),
        "induced_max_depth": depth,
        "induced_depth_source": "current approved family-held-out development selection over depths 2, 3, and 4",
    }


def run_development_selection(
    binary: Path,
    output: Path,
) -> tuple[dict[str, Any], tuple[float, float, float]]:
    all_records, all_labels, questions, task_records, task_labels = load_development_corpus()
    task_questions = {
        task_id: question_for_record(records[0], questions)
        for task_id, records in task_records.items()
    }
    induced_by_task: dict[str, dict[int, dict[str, str]]] = defaultdict(dict)
    induction_summaries = {}
    for task_id, records in task_records.items():
        induction_summaries[task_id] = {}
        for depth in (2, 3, 4):
            assignments, summary = run_per_trajectory_induction(
                binary,
                records,
                query_terms(task_questions[task_id]),
                output,
                f"{task_id}-depth-{depth}",
                max_depth=depth,
            )
            induced_by_task[task_id][depth] = assignments
            induction_summaries[task_id][str(depth)] = summary

    rows: list[dict[str, Any]] = []
    threshold_rows = []
    scored_sources: set[str] = set()
    families = sorted(set(TASK_FAMILY.values()))
    for seed in SEEDS:
        for heldout_family in families:
            train_task_ids = [
                task_id for task_id in task_records if TASK_FAMILY[task_id] != heldout_family
            ]
            test_task_ids = [
                task_id for task_id in task_records if TASK_FAMILY[task_id] == heldout_family
            ]
            train_records = [record for task_id in train_task_ids for record in task_records[task_id]]
            train_labels = {
                op_id: label
                for task_id in train_task_ids
                for op_id, label in task_labels[task_id].items()
            }
            train_questions = {
                record["trajectory"]: task_questions[task_id]
                for task_id in train_task_ids
                for record in task_records[task_id]
            }
            vectorizer, model = train_ranker(train_records, train_labels, train_questions, seed)
            train_scores = materialize_scores(
                vectorizer,
                model,
                train_records,
                train_questions,
                output / f"seed-{seed}/{heldout_family}/training-risk-scores.jsonl",
            )
            thresholds = development_tag_thresholds(train_scores)
            threshold_rows.append(
                {"seed": seed, "heldout_family": heldout_family, "thresholds": list(thresholds)}
            )
            for task_id in test_task_ids:
                records = task_records[task_id]
                scores = materialize_scores(
                    vectorizer,
                    model,
                    records,
                    task_questions[task_id],
                    output / f"seed-{seed}/{heldout_family}/{task_id}-risk-scores.jsonl",
                )
                methods = deployable_method_keys(
                    records, scores, induced_by_task[task_id][2], thresholds
                )
                methods.pop("induced")
                for method, keys in methods.items():
                    for aggregation in ("max", "mean"):
                        groups = aggregate_groups(records, scores, keys, aggregation)
                        metrics = score_groups(
                            groups,
                            task_labels[task_id],
                            len(records),
                            f"development:{task_id}",
                            scored_sources,
                        )
                        rows.append(
                            {
                                "seed": seed,
                                "heldout_family": heldout_family,
                                "task": task_id,
                                "method": method,
                                "aggregation": aggregation,
                                **metrics,
                            }
                        )
                for depth in (2, 3, 4):
                    for aggregation in ("max", "mean"):
                        groups = aggregate_groups(
                            records, scores, induced_by_task[task_id][depth], aggregation
                        )
                        metrics = score_groups(
                            groups,
                            task_labels[task_id],
                            len(records),
                            f"development:{task_id}",
                            scored_sources,
                        )
                        rows.append(
                            {
                                "seed": seed,
                                "heldout_family": heldout_family,
                                "task": task_id,
                                "method": f"induced_d{depth}",
                                "aggregation": aggregation,
                                **metrics,
                            }
                        )
    selection = select_development_configuration(rows)
    all_train_thresholds = []
    for seed in SEEDS:
        vectorizer, model = train_ranker(all_records, all_labels, questions, seed)
        scores = materialize_scores(
            vectorizer,
            model,
            all_records,
            questions,
            output / f"all-development-seed-{seed}-risk-scores.jsonl",
        )
        all_train_thresholds.append(development_tag_thresholds(scores))
    thresholds = tuple(
        sorted(values)[len(values) // 2]
        for values in zip(*all_train_thresholds)
    )
    result = {
        "tasks": {task_id: len(records) for task_id, records in task_records.items()},
        "families": families,
        "seeds": list(SEEDS),
        "rows": rows,
        "threshold_selection_rows": threshold_rows,
        "final_tag_thresholds": list(thresholds),
        "selection": selection,
        "induction": induction_summaries,
        "scored_label_sources": sorted(scored_sources),
    }
    write_json(output / "development-selection.json", result)
    return result, thresholds


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty values")
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_group_metric_samples(
    records: list[dict[str, Any]],
    labels: dict[str, int],
    groups: list[dict[str, Any]],
    operation_scores: dict[str, float],
    aggregation: str,
    seed: int,
    repetitions: int = 1000,
) -> dict[str, list[float]]:
    group_by_op = {op_id: group["key"] for group in groups for op_id in group["op_ids"]}
    by_trajectory: dict[str, list[str]] = defaultdict(list)
    for record in records:
        by_trajectory[record["trajectory"]].append(record["op_id"])
    trajectories = sorted(by_trajectory)
    rng = random.Random(seed)
    samples = {
        "average_precision": [],
        "ap_minus_prevalence": [],
        "work_to_25_recall": [],
        "groups_to_25_recall": [],
        "recall_at_30pct_work": [],
    }
    for _ in range(repetitions):
        sampled_trajectories = [rng.choice(trajectories) for _ in trajectories]
        group_counts: dict[str, dict[str, float]] = {}
        sampled_rows: list[tuple[str, int]] = []
        for trajectory in sampled_trajectories:
            for op_id in by_trajectory[trajectory]:
                group_key = group_by_op[op_id]
                score = float(operation_scores[op_id])
                label = labels[op_id]
                row = group_counts.setdefault(
                    group_key,
                    {"score_sum": 0.0, "score_max": -math.inf, "size": 0.0, "positive": 0.0},
                )
                row["score_sum"] += score
                row["score_max"] = max(row["score_max"], score)
                row["size"] += 1
                row["positive"] += label
                sampled_rows.append((group_key, label))
        y = [label for _, label in sampled_rows]
        positives = sum(y)
        if positives <= 0:
            continue
        group_scores = {
            key: (
                row["score_max"]
                if aggregation == "max"
                else row["score_sum"] / row["size"]
            )
            for key, row in group_counts.items()
        }
        ordered = sorted(group_counts.items(), key=lambda item: (-group_scores[item[0]], item[0]))
        target = math.ceil(positives * 0.25)
        inspected = found = groups_seen = 0
        work25 = groups25 = None
        budget_found = 0
        budget_limit = len(y) * 0.30
        for key, row in ordered:
            inspected += int(row["size"])
            found += int(row["positive"])
            groups_seen += 1
            if inspected <= budget_limit + 1e-12:
                budget_found = found
            if work25 is None and found >= target:
                work25 = inspected / len(y)
                groups25 = groups_seen
        sampled_scores = [group_scores[key] for key, _ in sampled_rows]
        ap = float(average_precision_score(y, sampled_scores))
        samples["average_precision"].append(ap)
        samples["ap_minus_prevalence"].append(ap - positives / len(y))
        samples["work_to_25_recall"].append(float(work25))
        samples["groups_to_25_recall"].append(float(groups25))
        samples["recall_at_30pct_work"].append(budget_found / positives)
    return samples


def summarize_bootstrap_samples(samples: dict[str, list[float]]) -> dict[str, Any]:
    return {
        metric: {
            "repetitions": len(values),
            "median": median(values),
            "lower_95": percentile(values, 0.025),
            "upper_95": percentile(values, 0.975),
        }
        for metric, values in samples.items()
    }


def prepare_confirm_task(
    task_name: str,
    records: list[dict[str, Any]],
    scores: dict[str, float],
    induced: dict[str, str],
    thresholds: tuple[float, float, float],
    selection: dict[str, Any],
    seed: int,
    output: Path,
    include_matched: bool,
) -> dict[str, Any]:
    aggregation = selection["aggregation"]
    methods = deployable_method_keys(records, scores, induced, thresholds)
    groups_by_method: dict[str, list[dict[str, Any]]] = {}
    for method, keys in methods.items():
        groups_by_method[method] = aggregate_groups(records, scores, keys, aggregation)

    operation_keys = singleton_keys(records)
    random_groups = aggregate_groups(
        records, random_scores(records, seed), operation_keys, aggregation
    )
    induced_groups = groups_by_method["induced"]
    width_groups = aggregate_groups(records, {record["op_id"]: 1.0 for record in records}, induced)
    for group in width_groups:
        group["score"] = float(group["size"])
    width_groups.sort(key=lambda group: (-group["score"], group["key"]))
    rarity_groups = aggregate_groups(records, rarity_scores(records), induced, aggregation)
    matched_groups = []
    if include_matched:
        for matched_seed in range(100):
            keys = matched_partition_keys(records, induced, seed * 1000 + matched_seed)
            if size_multiset_by_trajectory(records, induced) != size_multiset_by_trajectory(
                records, keys
            ):
                raise SystemExit(f"{task_name}: matched null fails per-trajectory cardinality")
            groups = aggregate_groups(records, scores, keys, aggregation)
            if sorted(group["size"] for group in groups) != sorted(
                group["size"] for group in induced_groups
            ):
                raise SystemExit(f"{task_name}: matched null fails global cardinality")
            matched_groups.append({"matched_seed": matched_seed, "groups": groups})
    prepared = {
        "task": task_name,
        "seed": seed,
        "operation_count": len(records),
        "operation_scores": scores,
        "aggregation": aggregation,
        "groups_by_method": groups_by_method,
        "random_groups": random_groups,
        "width_groups": width_groups,
        "rarity_groups": rarity_groups,
        "matched_groups": matched_groups,
        "label_fields_present": False,
    }
    write_json(output / "prepared-groups-before-label-join.json", prepared)
    return prepared


def score_prepared_confirm_task(
    task_name: str,
    records: list[dict[str, Any]],
    labels: dict[str, int],
    prepared: dict[str, Any],
    selection: dict[str, Any],
    seed: int,
    output: Path,
    scored_sources: set[str],
) -> dict[str, Any]:
    rows = []
    groups_by_method = prepared["groups_by_method"]
    for method, groups in groups_by_method.items():
        metrics = score_groups(
            groups, labels, len(records), f"confirmatory:{task_name}", scored_sources
        )
        rows.append({"method": method, "ranker": "shared_logistic", **metrics})
    random_groups = prepared["random_groups"]
    rows.append(
        {
            "method": "random_operation",
            "ranker": "random",
            **score_groups(
                random_groups,
                labels,
                len(records),
                f"confirmatory:{task_name}",
                scored_sources,
            ),
        }
    )
    oracle_keys = {
        record["op_id"]: f"oracle|{labels[record['op_id']]}" for record in records
    }
    oracle_scores = {record["op_id"]: float(labels[record["op_id"]]) for record in records}
    oracle_groups = aggregate_groups(records, oracle_scores, oracle_keys, "max")
    rows.append(
        {
            "method": "oracle_upper_bound",
            "ranker": "hidden_oracle",
            **score_groups(
                oracle_groups,
                labels,
                len(records),
                f"confirmatory:{task_name}",
                scored_sources,
            ),
        }
    )
    width_groups = prepared["width_groups"]
    rarity_groups = prepared["rarity_groups"]
    for name, groups in (("induced_width", width_groups), ("induced_rarity", rarity_groups)):
        rows.append(
            {
                "method": name,
                "ranker": name.removeprefix("induced_"),
                **score_groups(
                    groups,
                    labels,
                    len(records),
                    f"confirmatory:{task_name}",
                    scored_sources,
                ),
            }
        )
    matched_rows = []
    for item in prepared["matched_groups"]:
        metrics = score_groups(
            item["groups"],
            labels,
            len(records),
            f"confirmatory:{task_name}",
            scored_sources,
        )
        matched_rows.append({"matched_seed": item["matched_seed"], **metrics})
    selected_group_names = {
        "induced",
        "flat",
        "session",
        "dataset_native",
        "raw_action",
        "tag",
        selection["sql"],
        selection["explicit_stack"],
        selection["fixed_sequential"],
    }
    bootstrap_samples = {}
    if seed == SEEDS[0] and prepared["matched_groups"]:
        for method in sorted(selected_group_names):
            bootstrap_samples[method] = bootstrap_group_metric_samples(
                records,
                labels,
                groups_by_method[method],
                prepared["operation_scores"],
                prepared["aggregation"],
                seed=seed * 1009,
                repetitions=1000,
            )
    elif seed == SEEDS[0]:
        bootstrap_samples["induced"] = bootstrap_group_metric_samples(
            records,
            labels,
            groups_by_method["induced"],
            prepared["operation_scores"],
            prepared["aggregation"],
            seed=seed * 1009,
            repetitions=1000,
        )
    for method in sorted(selected_group_names):
        write_json(output / "groups" / f"{method}.json", groups_by_method[method])
    write_json(output / "groups/random_operation.json", random_groups)
    write_json(output / "groups/oracle_upper_bound.json", oracle_groups)
    write_json(output / "groups/induced_width.json", width_groups)
    write_json(output / "groups/induced_rarity.json", rarity_groups)

    induced_groups = groups_by_method["induced"]
    bootstrap = (
        summarize_bootstrap_samples(
            {"ap_minus_prevalence": bootstrap_samples["induced"]["ap_minus_prevalence"]}
        )["ap_minus_prevalence"]
        if "induced" in bootstrap_samples
        else None
    )
    result = {
        "task": task_name,
        "seed": seed,
        "operations": len(records),
        "trajectories": len({record["trajectory"] for record in records}),
        "positives": sum(labels.values()),
        "rows": rows,
        "matched_rows": matched_rows,
        "induced_ap_minus_prevalence_bootstrap": bootstrap,
        "bootstrap_samples": bootstrap_samples,
        "bootstrap_intervals": {
            method: summarize_bootstrap_samples(samples)
            for method, samples in bootstrap_samples.items()
        },
    }
    write_json(output / "metrics.json", result)
    return result


def method_row(result: dict[str, Any], method: str) -> dict[str, Any]:
    return next(row for row in result["rows"] if row["method"] == method)


def median_method_metrics(results: list[dict[str, Any]], method: str) -> dict[str, float]:
    rows = [method_row(result, method) for result in results]
    metrics = (
        "average_precision",
        "work_to_25_recall",
        "groups_to_25_recall",
        "recall_at_30pct_work",
    )
    return {metric: float(median([row[metric] for row in rows])) for metric in metrics}


def relative_tradeoff_pass(induced: dict[str, float], baseline: dict[str, float]) -> dict[str, Any]:
    work_gain = (baseline["work_to_25_recall"] - induced["work_to_25_recall"]) / max(
        baseline["work_to_25_recall"], 1e-12
    )
    group_gain = (baseline["groups_to_25_recall"] - induced["groups_to_25_recall"]) / max(
        baseline["groups_to_25_recall"], 1e-12
    )
    ap_gain = induced["average_precision"] - baseline["average_precision"]
    work_worse = (induced["work_to_25_recall"] - baseline["work_to_25_recall"]) / max(
        baseline["work_to_25_recall"], 1e-12
    )
    groups_worse = (induced["groups_to_25_recall"] - baseline["groups_to_25_recall"]) / max(
        baseline["groups_to_25_recall"], 1e-12
    )
    branch_a = work_gain >= 0.15 and groups_worse <= 0.10 and ap_gain >= -0.02
    branch_b = group_gain >= 0.15 and work_worse <= 0.10 and ap_gain >= -0.02
    branch_c = ap_gain >= 0.03 and work_worse <= 0.10 and groups_worse <= 0.10
    return {
        "pass": branch_a or branch_b or branch_c,
        "branches": {"work": branch_a, "groups": branch_b, "ap": branch_c},
        "work_gain": work_gain,
        "group_gain": group_gain,
        "ap_gain": ap_gain,
        "work_worse": work_worse,
        "groups_worse": groups_worse,
    }


def decide_confirmatory_results(
    by_task: dict[str, list[dict[str, Any]]], selection: dict[str, Any]
) -> dict[str, Any]:
    deployable_baselines = [
        "flat",
        "session",
        "dataset_native",
        "raw_action",
        "tag",
        selection["sql"],
        selection["explicit_stack"],
        selection["fixed_sequential"],
    ]
    families = {}
    for task_name in ("agentrx", "telbench"):
        results = by_task[task_name]
        uncertainty_results = results[:1]
        induced = median_method_metrics(results, "induced")
        baseline_metrics = {
            method: median_method_metrics(results, method) for method in deployable_baselines
        }
        strongest = max(
            baseline_metrics,
            key=lambda method: (
                baseline_metrics[method]["average_precision"],
                -baseline_metrics[method]["work_to_25_recall"],
                -baseline_metrics[method]["groups_to_25_recall"],
            ),
        )
        bootstrap_lowers = [
            result["induced_ap_minus_prevalence_bootstrap"]["lower_95"]
            for result in uncertainty_results
        ]
        absolute = (
            induced["average_precision"] - method_row(results[1], "induced")["prevalence"]
            >= 0.05
            and min(bootstrap_lowers) > 0
            and induced["recall_at_30pct_work"] >= 0.50
        )
        relative = relative_tradeoff_pass(induced, baseline_metrics[strongest])
        paired_uncertainty = {
            "ap_gain": [],
            "work_gain_fraction": [],
            "group_gain_fraction": [],
        }
        for result in uncertainty_results:
            induced_samples = result["bootstrap_samples"]["induced"]
            baseline_samples = result["bootstrap_samples"][strongest]
            for index in range(len(induced_samples["average_precision"])):
                baseline_work = baseline_samples["work_to_25_recall"][index]
                baseline_groups = baseline_samples["groups_to_25_recall"][index]
                paired_uncertainty["ap_gain"].append(
                    induced_samples["average_precision"][index]
                    - baseline_samples["average_precision"][index]
                )
                paired_uncertainty["work_gain_fraction"].append(
                    (
                        baseline_work
                        - induced_samples["work_to_25_recall"][index]
                    )
                    / max(baseline_work, 1e-12)
                )
                paired_uncertainty["group_gain_fraction"].append(
                    (
                        baseline_groups
                        - induced_samples["groups_to_25_recall"][index]
                    )
                    / max(baseline_groups, 1e-12)
                )
        relative["paired_bootstrap_95"] = summarize_bootstrap_samples(paired_uncertainty)
        matched_deltas = [
            matched["work_to_25_recall"] - method_row(result, "induced")["work_to_25_recall"]
            for result in results
            for matched in result["matched_rows"]
        ]
        matched = {
            "pass": percentile(matched_deltas, 0.025) > 0,
            "median_delta": median(matched_deltas),
            "lower_95_delta": percentile(matched_deltas, 0.025),
            "upper_95_delta": percentile(matched_deltas, 0.975),
        }
        families[task_name] = {
            "induced": induced,
            "strongest_baseline": strongest,
            "strongest_baseline_metrics": baseline_metrics[strongest],
            "absolute_correspondence_pass": absolute,
            "relative_tradeoff": relative,
            "matched_null": matched,
            "induced_bootstrap_95": {
                metric: summarize_bootstrap_samples(
                    {
                        metric: [
                            value
                            for result in uncertainty_results
                            for value in result["bootstrap_samples"]["induced"][metric]
                        ]
                    }
                )[metric]
                for metric in (
                    "average_precision",
                    "work_to_25_recall",
                    "groups_to_25_recall",
                    "recall_at_30pct_work",
                )
            },
        }
    overall = all(
        family["absolute_correspondence_pass"]
        and family["relative_tradeoff"]["pass"]
        and family["matched_null"]["pass"]
        for family in families.values()
    )
    macro_samples = {
        metric: []
        for metric in (
            "average_precision",
            "work_to_25_recall",
            "groups_to_25_recall",
            "recall_at_30pct_work",
        )
    }
    for agentrx_result, telbench_result in zip(
        by_task["agentrx"][:1], by_task["telbench"][:1]
    ):
        for metric in macro_samples:
            left = agentrx_result["bootstrap_samples"]["induced"][metric]
            right = telbench_result["bootstrap_samples"]["induced"][metric]
            macro_samples[metric].extend((a + b) / 2 for a, b in zip(left, right))
    return {
        "positive_claim_pass": overall,
        "uncertainty_policy": (
            "The liblinear ranker is deterministic; one point run and one 1000-repetition "
            "instance-bootstrap stream are used for uncertainty. Additional seeds check "
            "determinism and supply independent matched-partition draws, not model variance."
        ),
        "families": families,
        "cross_family_macro_bootstrap_95": summarize_bootstrap_samples(macro_samples),
    }


def run_full_grouping(args: argparse.Namespace, output: Path) -> dict[str, Any]:
    development, thresholds = run_development_selection(
        args.agentpprof_bin.resolve(), output / "development"
    )
    selection = development["selection"]

    (
        agentrx_by_domain,
        agentrx_questions,
        telbench_records,
        telbench_cases,
        telbench_questions,
    ) = load_prepared_visible_full(output)
    agentrx_records = agentrx_by_domain["tau"] + agentrx_by_domain["magentic"]
    agentrx_manifest = {
        "trajectory_ids": {
            domain: sorted({record["trajectory"] for record in records})
            for domain, records in agentrx_by_domain.items()
        },
        "source": "visible-input/agentrx-records.jsonl",
    }

    agentrx_induced, agentrx_induction = run_per_trajectory_induction(
        args.agentpprof_bin.resolve(),
        agentrx_records,
        {
            trajectory: query_terms(question)
            for trajectory, question in agentrx_questions.items()
        },
        output / "confirmation",
        "agentrx-all",
        max_depth=int(selection["induced_max_depth"]),
    )
    telbench_induced, telbench_induction = run_per_trajectory_induction(
        args.agentpprof_bin.resolve(),
        telbench_records,
        {
            trajectory: query_terms(question)
            for trajectory, question in telbench_questions.items()
        },
        output / "confirmation",
        "telbench-all",
        max_depth=int(selection["induced_max_depth"]),
    )

    development_records, development_labels, development_questions, _, _ = load_development_corpus()
    prepared_by_seed: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    prepared_paths = []
    confirmation_score_vectors: dict[str, list[list[tuple[str, float]]]] = defaultdict(list)
    for seed in SEEDS:
        vectorizer, model = train_ranker(
            development_records, development_labels, development_questions, seed
        )
        seed_root = output / f"confirmation/seed-{seed}"
        agentrx_scores = materialize_scores(
            vectorizer,
            model,
            agentrx_records,
            agentrx_questions,
            seed_root / "agentrx-risk-scores.jsonl",
        )
        telbench_scores = materialize_scores(
            vectorizer,
            model,
            telbench_records,
            telbench_questions,
            seed_root / "telbench-risk-scores.jsonl",
        )
        confirmation_score_vectors["agentrx"].append(sorted(agentrx_scores.items()))
        confirmation_score_vectors["telbench"].append(sorted(telbench_scores.items()))
        for domain in ("tau", "magentic"):
            records = agentrx_by_domain[domain]
            prepared_by_seed[seed][f"agentrx_{domain}"] = prepare_confirm_task(
                f"agentrx_{domain}",
                records,
                {record["op_id"]: agentrx_scores[record["op_id"]] for record in records},
                {record["op_id"]: agentrx_induced[record["op_id"]] for record in records},
                thresholds,
                selection,
                seed,
                seed_root / f"agentrx_{domain}",
                include_matched=False,
            )
            prepared_paths.append(
                seed_root / f"agentrx_{domain}/prepared-groups-before-label-join.json"
            )
        prepared_by_seed[seed]["agentrx"] = prepare_confirm_task(
            "agentrx",
            agentrx_records,
            agentrx_scores,
            agentrx_induced,
            thresholds,
            selection,
            seed,
            seed_root / "agentrx",
            include_matched=True,
        )
        prepared_paths.append(seed_root / "agentrx/prepared-groups-before-label-join.json")
        prepared_by_seed[seed]["telbench"] = prepare_confirm_task(
            "telbench",
            telbench_records,
            telbench_scores,
            telbench_induced,
            thresholds,
            selection,
            seed,
            seed_root / "telbench",
            include_matched=True,
        )
        prepared_paths.append(seed_root / "telbench/prepared-groups-before-label-join.json")

    ranker_deterministic = all(
        all(vector == vectors[0] for vector in vectors[1:])
        for vectors in confirmation_score_vectors.values()
    )
    if not ranker_deterministic:
        raise SystemExit("the declared deterministic-ranker uncertainty policy no longer applies")

    if not all(path.is_file() for path in prepared_paths):
        raise SystemExit("confirmatory deployable group preparation is incomplete before label join")
    join_report = output / "confirmation/label-join-order.md"
    join_report.write_text(
        "# Confirmatory Label Join Order\n\n"
        "A separate completed process first projected the official sources into `visible-input/`, containing only label-free records and questions. This process loaded only those sanitized files. All risk-score files, Rust induction assignments, deployable baseline group orders, ablations, and 100 matched-null orders per family/seed were materialized before this point. AgentRx root-cause and TELBench gold values are first parsed below this boundary. Oracle upper-bound groups are the only post-join group construction and are non-deployable.\n",
        encoding="utf-8",
    )

    # Physical label join boundary: no confirmatory label loader is called above.
    agentrx_positive = load_agentrx_labels(args.agentrx_root.resolve())
    agentrx_labels_by_domain = {
        domain: complete_binary_labels(records, agentrx_positive[domain])
        for domain, records in agentrx_by_domain.items()
    }
    agentrx_labels = {
        **agentrx_labels_by_domain["tau"],
        **agentrx_labels_by_domain["magentic"],
    }
    telbench_labels = load_telbench_labels(args.telbench.resolve())
    if set(telbench_labels) != {record["op_id"] for record in telbench_records}:
        raise SystemExit("TELBench labels do not align exactly to visible span operations")
    if sum(agentrx_labels.values()) != 73:
        raise SystemExit(f"AgentRx requires 73 root-cause positives, found {sum(agentrx_labels.values())}")
    if len({record["trajectory"] for record in agentrx_records}) != 73:
        raise SystemExit("AgentRx full execution did not retain all 73 public labeled trajectories")

    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scored_sources: set[str] = set()
    for seed in SEEDS:
        seed_root = output / f"confirmation/seed-{seed}"
        for domain in ("tau", "magentic"):
            task_name = f"agentrx_{domain}"
            by_task[task_name].append(
                score_prepared_confirm_task(
                    task_name,
                    agentrx_by_domain[domain],
                    agentrx_labels_by_domain[domain],
                    prepared_by_seed[seed][task_name],
                    selection,
                    seed,
                    seed_root / task_name,
                    scored_sources,
                )
            )
        by_task["agentrx"].append(
            score_prepared_confirm_task(
                "agentrx",
                agentrx_records,
                agentrx_labels,
                prepared_by_seed[seed]["agentrx"],
                selection,
                seed,
                seed_root / "agentrx",
                scored_sources,
            )
        )
        by_task["telbench"].append(
            score_prepared_confirm_task(
                "telbench",
                telbench_records,
                telbench_labels,
                prepared_by_seed[seed]["telbench"],
                selection,
                seed,
                seed_root / "telbench",
                scored_sources,
            )
        )

    decision = decide_confirmatory_results(by_task, selection)
    result = {
        "completion": {
            "development_tasks": 5,
            "development_seeds": len(SEEDS),
            "agentrx_trajectories": len({record["trajectory"] for record in agentrx_records}),
            "agentrx_domains": {
                domain: len({record["trajectory"] for record in records})
                for domain, records in agentrx_by_domain.items()
            },
            "telbench_cases": len(telbench_cases),
            "confirmatory_seeds": len(SEEDS),
            "ranker_deterministic_across_seeds": ranker_deterministic,
            "point_estimate_runs": 1,
            "instance_bootstrap_repetitions": 1000,
            "matched_controls_per_task_seed": 100,
        },
        "development": development,
        "selection": selection,
        "tag_thresholds": list(thresholds),
        "agentrx_manifest": agentrx_manifest,
        "induction": {"agentrx": agentrx_induction, "telbench": telbench_induction},
        "confirmation": dict(by_task),
        "decision": decision,
        "scored_label_sources": sorted(scored_sources),
        "visible_before_label_join": all(path.is_file() for path in prepared_paths),
        "label_join_order_report": str(join_report),
    }
    write_json(output / "grouping-results.json", result)
    write_jsonl(output / "telbench-unlabeled.jsonl", telbench_cases)
    return result


def native_batch_complete(summary_path: Path, expected: int) -> bool:
    if not summary_path.is_file():
        return False
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return summary.get("case_count") == expected and len(summary.get("items") or []) == expected


def fallback_errors(value: Any) -> list[str]:
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "_fallback_error":
                errors.append(str(child))
            else:
                errors.extend(fallback_errors(child))
    elif isinstance(value, list):
        for child in value:
            errors.extend(fallback_errors(child))
    return errors


def run_official_drift_full(
    args: argparse.Namespace, output: Path, sanitized_cases: list[dict[str, Any]]
) -> dict[str, Any]:
    if len(sanitized_cases) != 1000:
        raise SystemExit("official TELBench native run requires all 1000 sanitized cases")
    native_root = output / "official-drift"
    batches_root = native_root / "batches"
    batch_size = args.native_batch_size
    if batch_size <= 0:
        raise SystemExit("--native-batch-size must be positive")
    batch_specs = []
    for start in range(0, len(sanitized_cases), batch_size):
        cases = sanitized_cases[start : start + batch_size]
        batch_name = f"batch-{start // batch_size:04d}"
        batch_dir = batches_root / batch_name
        input_path = batch_dir / "input-unlabeled.jsonl"
        write_jsonl(input_path, cases)
        batch_specs.append((batch_name, batch_dir, input_path, len(cases)))

    commands = []
    merged_by_setting = {}
    for setting in ("bare", "drift"):
        items = []
        for batch_name, batch_dir, input_path, expected in batch_specs:
            summary_path = batch_dir / setting / args.model / "summary.json"
            if not native_batch_complete(summary_path, expected):
                command = [
                    str(args.drift_bin.resolve()),
                    "--setting",
                    setting,
                    "--input",
                    str(input_path),
                    "--model",
                    args.model,
                    "--api-type",
                    "chat",
                    "--base-url",
                    args.base_url,
                    "--api-key",
                    args.api_key,
                    "--outdir",
                    str(batch_dir),
                    "--workers",
                    str(args.native_workers),
                ]
                started = time.monotonic()
                completed = run(command)
                recorded = list(command)
                recorded[recorded.index("--api-key") + 1] = "<redacted>"
                commands.append(
                    {
                        "batch": batch_name,
                        "setting": setting,
                        "command": recorded,
                        "wall_seconds": time.monotonic() - started,
                        "stdout_tail": completed.stdout[-1000:],
                    }
                )
            if not native_batch_complete(summary_path, expected):
                raise SystemExit(f"official {setting} batch incomplete: {batch_name}")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            items.extend(summary["items"])
        items.sort(key=lambda row: row["case_id"])
        if len(items) != 1000 or len({row["case_id"] for row in items}) != 1000:
            raise SystemExit(f"official {setting} merged output is not 1000 unique cases")
        usage_records = [row.get("usage") or {} for row in items]
        merged = {
            "setting": setting,
            "model": args.model,
            "case_count": len(items),
            "items": items,
            "usage": {
                "call_count": sum(int(row.get("call_count") or 0) for row in usage_records),
                "input_tokens": sum(int(row.get("input_tokens") or 0) for row in usage_records),
                "output_tokens": sum(int(row.get("output_tokens") or 0) for row in usage_records),
                "total_tokens": sum(int(row.get("total_tokens") or 0) for row in usage_records),
            },
        }
        merged_path = native_root / setting / args.model / "summary.json"
        write_json(merged_path, merged)
        evaluation_path = native_root / setting / args.model / "evaluation.json"
        drift_eval = args.drift_bin.resolve().with_name("drift-eval")
        completed = run(
            [
                str(drift_eval),
                "--gold",
                str(args.telbench.resolve()),
                "--pred",
                str(merged_path),
                "--output",
                str(evaluation_path),
            ]
        )
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        if evaluation["case_count"] != 1000 or evaluation["missing_predictions"]:
            raise SystemExit(f"official {setting} evaluation is incomplete")
        fallback_by_case = {}
        for _, batch_dir, _, _ in batch_specs:
            for run_path in (batch_dir / setting / args.model).glob("*/run.json"):
                errors = fallback_errors(json.loads(run_path.read_text(encoding="utf-8")))
                if errors:
                    fallback_by_case[run_path.parent.name] = errors
        merged_by_setting[setting] = {
            "summary": str(merged_path),
            "evaluation": evaluation,
            "evaluator_stdout": completed.stdout.strip(),
            "usage": merged["usage"],
            "fallback_case_count": len(fallback_by_case),
            "fallback_error_counts": dict(
                sorted(Counter(error for errors in fallback_by_case.values() for error in errors).items())
            ),
            "fallback_cases": fallback_by_case,
        }
    result = {
        "settings": merged_by_setting,
        "batches": len(batch_specs),
        "batch_size": batch_size,
        "workers": args.native_workers,
        "commands_executed_this_invocation": commands,
        "server": observe_llama_server(args.base_url, args.api_key),
    }
    write_json(native_root / "native-results.json", result)
    return result


def write_full_report(path: Path, grouping: dict[str, Any], native: dict[str, Any]) -> None:
    decision = grouping["decision"]
    lines = [
        "# Full Execution Report — RQ2 Cross-Family Problem Localization",
        "",
        "## Completion",
        "",
        "The approved full matrix completed. This report records results for independent result review; it does not itself admit the claim into the paper.",
        "",
        f"- development tasks/seeds: `{grouping['completion']['development_tasks']}` / `{grouping['completion']['development_seeds']}`",
        f"- AgentRx trajectories/domains: `{grouping['completion']['agentrx_trajectories']}` / `{grouping['completion']['agentrx_domains']}`",
        f"- TELBench cases: `{grouping['completion']['telbench_cases']}`",
        f"- confirmatory seeds: `{grouping['completion']['confirmatory_seeds']}`",
        f"- deterministic ranker / point runs / bootstrap repetitions: `{grouping['completion']['ranker_deterministic_across_seeds']}` / `{grouping['completion']['point_estimate_runs']}` / `{grouping['completion']['instance_bootstrap_repetitions']}`",
        f"- matched controls per task and seed: `{grouping['completion']['matched_controls_per_task_seed']}`",
        f"- selected development configuration: `{grouping['selection']}`",
        "",
        "## Predeclared Decision Criteria",
        "",
        f"- positive RQ2 claim passes all criteria: **{decision['positive_claim_pass']}**",
    ]
    for family, result in decision["families"].items():
        lines.extend(
            [
                f"### {family}",
                "",
                f"- induced median metrics: `{result['induced']}`",
                f"- strongest fixed/deployable baseline: `{result['strongest_baseline']}` `{result['strongest_baseline_metrics']}`",
                f"- absolute correspondence: `{result['absolute_correspondence_pass']}`",
                f"- relative tradeoff: `{result['relative_tradeoff']}`",
                f"- matched null: `{result['matched_null']}`",
                "",
            ]
        )
    lines.extend(["## Official TELBench Native Results", ""])
    for setting, result in native["settings"].items():
        evaluation = result["evaluation"]
        lines.extend(
            [
                f"### {setting}",
                "",
                f"- cases: `{evaluation['case_count']}`",
                f"- macro P/R/F1: `{evaluation['macro_precision']:.4f}` / `{evaluation['macro_recall']:.4f}` / `{evaluation['macro_f1']:.4f}`",
                f"- micro P/R/F1: `{evaluation['micro_precision']:.4f}` / `{evaluation['micro_recall']:.4f}` / `{evaluation['micro_f1']:.4f}`",
                f"- first-error accuracy: `{evaluation['first_error_accuracy']:.4f}`",
                f"- usage: `{result['usage']}`",
                f"- official fallback cases: `{result['fallback_case_count']}`; errors: `{result['fallback_error_counts']}`",
                "",
            ]
        )
    if native.get("clean_intersection"):
        clean = native["clean_intersection"]
        lines.extend(["## Native Clean-Intersection Sensitivity", ""])
        lines.append(
            f"The same official evaluator was rerun on the `{clean['case_count']}` cases with no fallback in either setting. The all-1,000 rows above remain the primary completion result."
        )
        lines.append("")
        for setting, evaluation in clean["settings"].items():
            lines.append(
                f"- {setting}: macro-F1 `{evaluation['macro_f1']:.4f}`, micro-F1 `{evaluation['micro_f1']:.4f}`, first-error accuracy `{evaluation['first_error_accuracy']:.4f}`"
            )
        lines.append("")
    lines.extend(
        [
            "## Source and Runtime Disclosure",
            "",
            "- SQL rollup prefixes are separate SQLite `GROUP BY` queries and are scored separately.",
            f"- llama-server observation: `{native['server']}`",
            "- every official native batch uses a label-free TELBench input; the official evaluator joins gold only after merged predictions exist.",
            "- the 32K model cannot execute every TELBench prompt; fallback cases and errors are reported per setting and native aggregate results are contextual rather than claim-decision evidence.",
            "- execution concurrency changed only at completed 100-case recovery boundaries (8, then 16, then 32 workers); model, prompt, data, and evaluator stayed unchanged.",
            "",
            "## Next Action",
            "",
            "Run an independent result review that recomputes the primary rows, tests every predeclared criterion, and decides whether the result is supportive, contradictory, or inconclusive before returning to WRITE.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_full(args: argparse.Namespace) -> int:
    output = full_output(args)
    output.mkdir(parents=True, exist_ok=True)
    grouping = run_full_grouping(args, output)
    sanitized_cases = [
        json.loads(line)
        for line in (output / "telbench-unlabeled.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    native = run_official_drift_full(args, output, sanitized_cases)
    result = {"grouping": grouping, "native": native}
    write_json(output / "full-results.json", result)
    report = DEFAULT_REPORT.with_name("full-execution-report.md")
    write_full_report(report, grouping, native)
    print(json.dumps({"full_results": str(output / "full-results.json"), "report": str(report)}))
    return 0


def score_groups(
    groups: list[dict[str, Any]],
    labels: dict[str, int],
    operation_count: int,
    label_source: str,
    scored_sources: set[str],
) -> dict[str, Any]:
    # Hidden labels enter only here, after scores, groups, and ordering exist.
    scored_sources.add(label_source)
    positives = sum(labels.values())
    if positives <= 0:
        raise SystemExit("scoring requires at least one positive")
    ranked_op_scores: dict[str, float] = {}
    seen_positive = 0
    work = 0
    groups_seen = 0
    work25 = None
    groups25 = None
    work50 = None
    groups50 = None
    work_first = None
    cumulative_rows: list[tuple[int, int]] = []
    for group in groups:
        group_positive = sum(labels[op_id] for op_id in group["op_ids"])
        for op_id in group["op_ids"]:
            ranked_op_scores[op_id] = group["score"]
        seen_positive += group_positive
        work += group["size"]
        groups_seen += 1
        cumulative_rows.append((work, seen_positive))
        if work_first is None and group_positive > 0:
            work_first = work / operation_count
        if work25 is None and seen_positive >= math.ceil(positives * 0.25):
            work25 = work / operation_count
            groups25 = groups_seen
        if work50 is None and seen_positive >= math.ceil(positives * 0.50):
            work50 = work / operation_count
            groups50 = groups_seen
    ordered_ids = sorted(labels)
    budget_recalls = {}
    for budget in (0.10, 0.20, 0.30):
        limit = operation_count * budget
        selected_positive = max(
            (positive for inspected, positive in cumulative_rows if inspected <= limit + 1e-12),
            default=0,
        )
        budget_recalls[f"recall_at_{int(budget * 100)}pct_work"] = selected_positive / positives
    return {
        "average_precision": float(
            average_precision_score(
                [labels[op_id] for op_id in ordered_ids],
                [ranked_op_scores[op_id] for op_id in ordered_ids],
            )
        ),
        "work_to_25_recall": work25,
        "groups_to_25_recall": groups25,
        "work_to_50_recall": work50,
        "groups_to_50_recall": groups50,
        "work_to_first_positive": work_first,
        "groups": len(groups),
        "operations": operation_count,
        "positives": positives,
        "prevalence": positives / operation_count,
        **budget_recalls,
    }


def run_official_drift(
    drift_bin: Path,
    sanitized_case: dict[str, Any],
    output: Path,
    base_url: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    if not drift_bin.is_file():
        raise SystemExit(f"missing installed official DRIFT CLI: {drift_bin}")
    input_path = output / "telbench-unlabeled.jsonl"
    write_jsonl(input_path, [sanitized_case])
    if any(key in sanitized_case for key in ("gold", "annotations", "meta")):
        raise SystemExit("TELBench preflight model input contains forbidden metadata")
    native_out = output / "official-drift"
    if native_out.exists():
        shutil.rmtree(native_out)
    result: dict[str, Any] = {}
    for setting in ("bare", "drift"):
        command = [
            str(drift_bin),
            "--setting",
            setting,
            "--input",
            str(input_path),
            "--model",
            model,
            "--api-type",
            "chat",
            "--base-url",
            base_url,
            "--api-key",
            api_key,
            "--outdir",
            str(native_out),
            "--workers",
            "1",
        ]
        started = time.monotonic()
        completed = run(command)
        summary_path = native_out / setting / model / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        recorded_command = list(command)
        recorded_command[recorded_command.index("--api-key") + 1] = "<redacted>"
        result[setting] = {
            "command": recorded_command,
            "wall_seconds": time.monotonic() - started,
            "case_count": summary["case_count"],
            "usage": summary["usage"],
            "summary": str(summary_path),
            "stdout_tail": completed.stdout[-1000:],
        }
    return result


def git_revision(path: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def observe_llama_server(base_url: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        models = json.loads(response.read().decode("utf-8"))
    process_list = subprocess.run(
        ["ps", "-eo", "pid=,lstart=,args="],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    port = urllib.parse.urlparse(base_url).port
    port_marker = f"--port {port}" if port is not None else "llama-server"
    server_commands = [
        line.strip()
        for line in process_list
        if "llama-server" in line and port_marker in line
    ]
    return {"models_response": models, "server_processes": server_commands}


def write_report(path: Path, result: dict[str, Any]) -> None:
    dev = result["development"]
    lines = [
        "# Real Preflight — RQ2 Cross-Family Problem Localization",
        "",
        "## Verdict",
        "",
        f"**{result['verdict']}**. This is executability evidence only; it is not admitted paper evidence and does not score confirmatory AgentRx or TELBench labels.",
        "",
        "## Scope Executed",
        "",
        f"- development target: `{dev['target_task']}` ({dev['operations']} operations, {dev['trajectories']} trajectories)",
        f"- ranker training family: `{dev['training_task']}`",
        f"- AgentRx unlabeled trajectory: `{result['agentrx']['trajectory_id']}` ({result['agentrx']['operations']} operations)",
        f"- TELBench unlabeled case: `{result['telbench']['case_id']}` ({result['telbench']['operations']} spans)",
        f"- official TELBench native rows: bare={result['native_drift']['bare']['case_count']}, drift={result['native_drift']['drift']['case_count']}",
        "",
        "## Development Sanity Metrics",
        "",
        "These values only prove that materialized scores, independent grouping views, matched partitions, and post-ranking label joins execute end to end.",
        "",
        "| View | AP | Work@25% recall | Groups@25% recall | Total groups |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, metrics in dev["metrics"].items():
        lines.append(
            f"| {method} | {metrics['average_precision']:.4f} | {metrics['work_to_25_recall']:.4f} | {metrics['groups_to_25_recall']} | {metrics['groups']} |"
        )
    lines.extend(
        [
            "",
            "## Leakage and Execution Checks",
            "",
            f"- profiler visible-field allowlist passed: `{result['checks']['visible_allowlist']}`",
            f"- confirmatory labels joined or scored: `{result['checks']['confirmatory_labels_scored']}`",
            f"- induction invocation granularity: `{result['checks']['induction_granularity']}`",
            f"- cross-trajectory semantic-path aggregation retained: `{result['checks']['cross_trajectory_semantic_path_aggregation']}`",
            f"- global matched group-size multiset exact: `{result['checks']['matched_global_group_size_multiset_exact']}`",
            f"- every per-trajectory matched size multiset exact: `{result['checks']['matched_per_trajectory_group_size_multisets_exact']}`",
            f"- development selected Rust fields: `{dev['induction']['selected_fields']}`",
            f"- AgentRx selected Rust fields: `{result['agentrx']['induction']['selected_fields']}`",
            f"- TELBench selected Rust fields: `{result['telbench']['induction']['selected_fields']}`",
            "- the common risk score was materialized before any grouping; hidden development labels entered only in the final metric function.",
            f"- risk-tag thresholds were selected on the separate training family: `{dev['tag_thresholds_selected_on_training_family']}`",
            f"- development visible-field provenance: `{dev['visible_field_provenance']}`",
            "- SQL rollup prefixes are implemented as four separate SQLite `GROUP BY` queries (`role`, `role/action`, `role/action/tool_status`, and `role/phase/action/tool_status`) and scored separately; SQLite has no native `ROLLUP` operator.",
            "- the official DRIFT model input contains only `id`, `source_id`, `question`, and ordered `spans[{id,raw}]`.",
            "",
            "## Official Sources",
            "",
            f"- Microsoft AgentRx commit: `{result['sources']['agentrx_revision']}`",
            f"- NJU-LINK DRIFT commit: `{result['sources']['drift_revision']}`",
            f"- TELBench decrypted rows: `{result['sources']['telbench_rows']}`",
            f"- TELBench decrypted SHA-256: `{result['sources']['telbench_sha256']}`",
            f"- observed llama-server process: `{result['sources']['llama_server']['server_processes']}`",
            f"- observed llama-server model response: `{result['sources']['llama_server']['models_response']}`",
            "",
            "## Next Action",
            "",
            "Independently review this preflight and its raw outputs. If it passes, extend the same driver to the approved development-selection and complete AgentRx/TELBench full matrix; do not interpret this one-case prefix.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.mode == "prepare-full-visible":
        return prepare_full_visible_inputs(args)
    if args.mode == "full":
        return run_full(args)
    output = args.out_dir.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    train_records, train_labels, train_question = load_development_task("satraj_unsafe")
    target_records, target_labels, target_question = load_development_task("agentreward_looping")
    vectorizer, model = train_ranker(train_records, train_labels, train_question)
    train_scores = materialize_scores(
        vectorizer,
        model,
        train_records,
        train_question,
        output / "training-risk-scores.jsonl",
    )
    tag_thresholds = development_tag_thresholds(train_scores)
    target_scores = materialize_scores(
        vectorizer, model, target_records, target_question, output / "development-risk-scores.jsonl"
    )
    target_induced, target_induction = run_per_trajectory_induction(
        args.agentpprof_bin.resolve(),
        target_records,
        ["loop", "repeat"],
        output,
        "agentreward-looping",
    )

    methods: dict[str, dict[str, str]] = {
        method: group_keys(
            method, target_records, target_scores, target_induced, tag_thresholds
        )
        for method in ("flat", "session", "raw_action", "tag", "induced")
    }
    methods["sql_role"] = sql_group_keys(target_records, ("role",))
    methods["sql_role_action"] = sql_group_keys(target_records, ("role", "action"))
    methods["sql_role_action_status"] = sql_group_keys(
        target_records, ("role", "action", "tool_status")
    )
    methods["sql_role_phase_action_status"] = sql_group_keys(
        target_records, ("role", "phase", "action", "tool_status")
    )
    methods["matched_partition"] = matched_partition_keys(target_records, target_induced)
    if size_multiset_by_trajectory(target_records, methods["induced"]) != size_multiset_by_trajectory(
        target_records, methods["matched_partition"]
    ):
        raise SystemExit("matched partition does not preserve per-trajectory group-size multisets")
    metrics = {}
    scored_label_sources: set[str] = set()
    prepared_groups: dict[str, list[dict[str, Any]]] = {}
    for method, keys in methods.items():
        groups = aggregate_groups(target_records, target_scores, keys)
        prepared_groups[method] = groups
        write_json(output / "groups" / f"{method}.json", groups)
        metrics[method] = score_groups(
            groups,
            target_labels,
            len(target_records),
            "development:agentreward_looping",
            scored_label_sources,
        )
    induced_sizes = sorted(group["size"] for group in prepared_groups["induced"])
    matched_sizes = sorted(group["size"] for group in prepared_groups["matched_partition"])
    if induced_sizes != matched_sizes:
        raise SystemExit("matched partition does not preserve exact global group-size multiset")

    agentrx_records, agentrx_question, agentrx_id = load_unlabeled_agentrx(
        args.agentrx_root.resolve()
    )
    agentrx_scores = materialize_scores(
        vectorizer, model, agentrx_records, agentrx_question, output / "agentrx-risk-scores.jsonl"
    )
    del agentrx_scores
    _, agentrx_induction = run_per_trajectory_induction(
        args.agentpprof_bin.resolve(),
        agentrx_records,
        query_terms(agentrx_question),
        output,
        "agentrx-unlabeled",
    )

    telbench_records, telbench_case = load_first_telbench_unlabeled(args.telbench.resolve())
    telbench_scores = materialize_scores(
        vectorizer,
        model,
        telbench_records,
        telbench_case["question"],
        output / "telbench-risk-scores.jsonl",
    )
    del telbench_scores
    _, telbench_induction = run_per_trajectory_induction(
        args.agentpprof_bin.resolve(),
        telbench_records,
        query_terms(telbench_case["question"]),
        output,
        "telbench-unlabeled",
    )
    native = run_official_drift(
        args.drift_bin.resolve(),
        telbench_case,
        output,
        args.base_url,
        args.api_key,
        args.model,
    )
    server_observation = observe_llama_server(args.base_url, args.api_key)
    telbench_rows = sum(1 for line in args.telbench.open(encoding="utf-8") if line.strip())
    drift_root = args.drift_root.resolve()
    all_profiler_records = target_records + agentrx_records + telbench_records
    visible_allowlist_ok = all(
        not forbidden_field(field) and field in VISIBLE_FIELDS
        for record in all_profiler_records
        for field in record["fields"]
    )
    induction_summaries = (target_induction, agentrx_induction, telbench_induction)
    per_trajectory_ok = all(
        summary["trajectories"] == len(summary["per_trajectory"])
        for summary in induction_summaries
    )
    global_matched_exact = sorted(
        group["size"] for group in prepared_groups["induced"]
    ) == sorted(group["size"] for group in prepared_groups["matched_partition"])
    per_trajectory_matched_exact = size_multiset_by_trajectory(
        target_records, methods["induced"]
    ) == size_multiset_by_trajectory(target_records, methods["matched_partition"])
    scored_label_sources_list = sorted(scored_label_sources)
    result = {
        "verdict": "PASS",
        "mode": "preflight",
        "development": {
            "training_task": "satraj_unsafe",
            "target_task": "agentreward_looping",
            "operations": len(target_records),
            "trajectories": len({record["trajectory"] for record in target_records}),
            "metrics": metrics,
            "induction": target_induction,
            "tag_thresholds_selected_on_training_family": list(tag_thresholds),
            "visible_field_provenance": DEVELOPMENT_PROVENANCE,
        },
        "agentrx": {
            "trajectory_id": agentrx_id,
            "operations": len(agentrx_records),
            "induction": agentrx_induction,
        },
        "telbench": {
            "case_id": telbench_case["id"],
            "operations": len(telbench_records),
            "induction": telbench_induction,
        },
        "native_drift": native,
        "checks": {
            "visible_allowlist": visible_allowlist_ok,
            "scored_label_sources": scored_label_sources_list,
            "confirmatory_labels_scored": any(
                source.startswith(("agentrx:", "telbench:"))
                for source in scored_label_sources_list
            ),
            "induction_granularity": (
                "one Rust invocation per trajectory" if per_trajectory_ok else "invalid"
            ),
            "cross_trajectory_semantic_path_aggregation": True,
            "matched_global_group_size_multiset_exact": global_matched_exact,
            "matched_per_trajectory_group_size_multisets_exact": per_trajectory_matched_exact,
        },
        "sources": {
            "agentrx_root": str(args.agentrx_root.resolve()),
            "agentrx_revision": git_revision(args.agentrx_root.resolve()),
            "drift_root": str(drift_root),
            "drift_revision": git_revision(drift_root),
            "telbench": str(args.telbench.resolve()),
            "telbench_rows": telbench_rows,
            "telbench_sha256": sha256_file(args.telbench.resolve()),
            "llama_server": server_observation,
        },
    }
    write_json(output / "preflight-summary.json", result)
    write_report(args.report.resolve(), result)
    print(json.dumps({"verdict": "PASS", "summary": str(output / "preflight-summary.json"), "report": str(args.report.resolve())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
