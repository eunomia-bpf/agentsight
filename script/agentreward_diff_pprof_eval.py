#!/usr/bin/env python3
"""Build and evaluate task-semantic bad-minus-good pprof profiles.

The converter uses AgentRewardBench outcome annotations only to select and pair
same-task traces and to score results. Stack derivation never receives an
outcome field.
"""

from __future__ import annotations

import argparse
import ast
import csv
import gzip
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


STACK = "task,subtask,strategy,action,object,result"
ACTION_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*\(")
TARGET_RE = re.compile(r"\[([^\]]+)\]\s+([^\n]+)")
PURPOSE_PATTERNS = (
    re.compile(r"\bneed to\s+([^.!?]+)", re.I),
    re.compile(r"\bshould\s+([^.!?]+)", re.I),
    re.compile(r"\b(?:next|now|then)[, ]+I(?:'ll| will)?\s+([^.!?]+)", re.I),
    re.compile(r"\bI will\s+([^.!?]+)", re.I),
)
STOPWORDS = {
    "a", "an", "and", "at", "be", "for", "from", "i", "in", "is", "it",
    "of", "on", "or", "the", "this", "to", "with", "will",
}


@dataclass(frozen=True)
class Label:
    benchmark: str
    task_id: str
    canonical_task: str
    model: str
    experiment: str
    success: bool
    looping: bool | None
    source: Path

    @property
    def key(self) -> str:
        return "__".join(
            sanitize_slug(part)
            for part in (self.benchmark, self.task_id, self.model)
        )


@dataclass
class TraceSummary:
    label: Label
    goal: str
    operation_records: list[dict[str, Any]]
    token_records: list[dict[str, Any]]
    steps: int
    tokens: int
    errors: int
    repeats: int
    nonprogress: int
    finished: bool
    evidence: list[dict[str, Any]]

    def score(self, name: str) -> float:
        if name == "steps":
            return float(self.steps)
        if name == "tokens":
            return float(self.tokens)
        denominator = max(self.steps, 1)
        if name == "error_rate":
            return self.errors / denominator
        if name == "repeat_rate":
            return self.repeats / denominator
        if name == "nonprogress_rate":
            return self.nonprogress / denominator
        raise KeyError(name)


def canonical_task_id(task_id: str) -> str:
    return task_id.replace(".resized.", ".")


def sanitize_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value[:120] or "unknown"


def pair_slug(benchmark: str, task: str, bad: Label, good: Label) -> str:
    identity = "\0".join(
        (benchmark, task, bad.task_id, bad.model, bad.experiment, good.task_id, good.model, good.experiment)
    )
    digest = hashlib.sha256(identity.encode()).hexdigest()[:12]
    readable = sanitize_slug(f"{benchmark}__{task}__{bad.model}__minus__{good.model}")[:96]
    return f"{readable}__{digest}"


def clean_frame(value: Any, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.replace(";", ",").replace("=", ":")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def consensus(values: Iterable[str], yes: str) -> bool | None:
    observed = set(values)
    if len(observed) != 1:
        return None
    return next(iter(observed)) == yes


def load_labels(dataset_root: Path) -> tuple[list[Label], dict[str, int]]:
    annotations = dataset_root / "data" / "annotations.csv"
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    with annotations.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[
                (
                    row["benchmark"],
                    row["task_id"],
                    row["model_name"],
                    row["exp_name"],
                )
            ].append(row)

    labels: list[Label] = []
    conflicts = 0
    missing = 0
    for (benchmark, task_id, model, experiment), rows in grouped.items():
        success = consensus((row["trajectory_success"] for row in rows), "Successful")
        looping = consensus((row["trajectory_looping"] for row in rows), "Yes")
        if success is None:
            conflicts += 1
            continue
        source = dataset_root / "cleaned" / benchmark / model / experiment / f"{task_id}.json"
        if not source.is_file():
            missing += 1
            continue
        labels.append(
            Label(
                benchmark=benchmark,
                task_id=task_id,
                canonical_task=canonical_task_id(task_id),
                model=model,
                experiment=experiment,
                success=success,
                looping=looping,
                source=source,
            )
        )
    return labels, {
        "annotation_rows": sum(len(rows) for rows in grouped.values()),
        "annotated_trajectories": len(grouped),
        "consensus_success_trajectories": len(labels),
        "success_conflicts_excluded": conflicts,
        "missing_sources": missing,
    }


def eligible_groups(labels: list[Label]) -> dict[tuple[str, str], list[Label]]:
    grouped: dict[tuple[str, str], list[Label]] = defaultdict(list)
    for label in labels:
        grouped[(label.benchmark, label.canonical_task)].append(label)
    return {
        key: values
        for key, values in grouped.items()
        if {label.success for label in values} == {False, True}
    }


def parse_action(action: str) -> tuple[str, list[Any]]:
    match = ACTION_RE.match(action or "")
    name = match.group(1).split(".")[-1].lower() if match else "unknown"
    try:
        node = ast.parse(action.strip(), mode="eval").body
        if isinstance(node, ast.Call):
            args = []
            for argument in node.args:
                try:
                    args.append(ast.literal_eval(argument))
                except (ValueError, TypeError):
                    args.append("")
            return name, args
    except (SyntaxError, ValueError):
        pass
    return name, []


def target_from_axtree(axtree: str, target: str) -> str:
    if not target:
        return ""
    for line in (axtree or "").splitlines():
        match = TARGET_RE.search(line)
        if match and match.group(1) == target:
            rendered = match.group(2).strip()
            quoted = re.search(r"'([^']+)'", rendered)
            if quoted and quoted.group(1).strip():
                return clean_frame(quoted.group(1), 72)
            return clean_frame(rendered.split(",", 1)[0], 72)
    return ""


def action_object(action_name: str, args: list[Any], step: dict[str, Any]) -> str:
    target = clean_frame(args[0], 40) if args else ""
    accessible = target_from_axtree(str(step.get("axtree") or ""), target)
    if action_name in {"fill", "type"} and len(args) > 1:
        value = clean_frame(args[1], 72)
        if "search" in accessible.lower() or "search" in str(step.get("url", "")).lower():
            return f"search: {value}"
    if accessible:
        return accessible
    if action_name in {"goto", "open_url"} and args:
        domain = urlparse(str(args[0])).netloc
        return clean_frame(domain or args[0], 72)
    if target and not target.isdigit():
        return target
    domain = urlparse(str(step.get("url") or "")).netloc
    return clean_frame(domain, 72)


def strategy_for(action_name: str, reasoning: str, object_name: str) -> str:
    text = f"{reasoning} {object_name}".lower()
    if action_name in {"send_msg_to_user", "answer", "report_infeasible", "finish"}:
        return "finish"
    if action_name in {"fill", "type"}:
        return "search" if "search" in text else "input"
    if action_name in {"goto", "open_url", "go_back", "new_tab", "click"}:
        if any(word in text for word in ("review", "inspect", "read", "check", "verify")):
            return "inspect"
        return "navigate"
    if action_name in {"scroll", "select_option", "hover"}:
        return "inspect"
    if action_name in {"press", "keyboard", "upload_file"}:
        return "input"
    if action_name in {"noop", "wait"}:
        return "wait"
    if any(word in text for word in ("error", "retry", "failed", "recover")):
        return "recover"
    return "act"


def phrase_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in STOPWORDS and len(token) > 1
    }


def similar_phrase(left: str, right: str) -> bool:
    a, b = phrase_tokens(left), phrase_tokens(right)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= 0.4


def purpose_phrase(reasoning: str, strategy: str, object_name: str, previous: str) -> str:
    plain = re.sub(r"<[^>]+>", " ", reasoning or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    candidate = ""
    for pattern in PURPOSE_PATTERNS:
        match = pattern.search(plain)
        if match:
            candidate = match.group(1)
            break
    candidate = re.split(r"\b(?:so that|because|by clicking|using the)\b", candidate, 1)[0]
    candidate = clean_frame(candidate, 88)
    if not candidate or candidate.lower().startswith(("click", "fill", "type", "scroll", "press")):
        candidate = clean_frame(f"{strategy} {object_name}".strip(), 88)
    if previous and (candidate == previous or similar_phrase(candidate, previous)):
        return previous
    return candidate or previous


def exact_action_state_signature(action: str, url: str, axtree: str) -> str:
    native_action = re.sub(r"\s+", " ", action or "").strip()
    visible_state = hashlib.sha256((axtree or "").encode()).hexdigest()
    return "\0".join((native_action, url or "", visible_state))


def trace_to_summary(label: Label) -> TraceSummary:
    with label.source.open(encoding="utf-8") as handle:
        trace = json.load(handle)
    goal = clean_frame(trace.get("goal") or label.canonical_task, 160)
    raw_steps = trace.get("steps") or []
    steps = [step for step in raw_steps if str(step.get("action") or "").strip()]
    summary = trace.get("summary_info") or {}
    operations: list[dict[str, Any]] = []
    token_operations: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    previous_signature = ""
    previous_subtask = ""
    errors = repeats = nonprogress = total_tokens = 0
    finished = False

    for index, step in enumerate(steps):
        action = str(step.get("action") or "")
        reasoning = str(step.get("reasoning") or "")
        action_name, args = parse_action(action)
        object_name = action_object(action_name, args, step)
        strategy = strategy_for(action_name, reasoning, object_name)
        subtask = purpose_phrase(reasoning, strategy, object_name, previous_subtask)
        if subtask:
            previous_subtask = subtask
        signature = exact_action_state_signature(
            action,
            str(step.get("url") or ""),
            str(step.get("axtree") or ""),
        )
        repeated = bool(previous_signature and signature == previous_signature)
        previous_signature = signature
        error_text = clean_frame(step.get("last_action_error"), 72)
        is_last = index + 1 == len(steps)
        is_finish = strategy == "finish"
        if error_text:
            result = f"error: {error_text}"
        elif repeated:
            result = "repeated"
        elif is_finish:
            result = "conclusion"
            finished = True
        elif is_last:
            result = "stopped" if summary.get("truncated") or summary.get("err_msg") else "terminal"
        else:
            result = "progress"

        stats = step.get("stats") or {}
        tokens = int(stats.get("input_tokens") or 0) + int(stats.get("output_tokens") or 0)
        total_tokens += tokens
        errors += int(bool(error_text))
        repeats += int(repeated)
        nonprogress += int(bool(error_text) or repeated)
        fields = {
            "task": goal,
            "subtask": subtask,
            "strategy": strategy,
            "action": action_name,
            "object": object_name,
            "result": result,
            "agent": label.model,
            "source_session": label.key,
            "evidence_id": f"{label.key}:step-{index:04d}",
        }
        fields = {key: value for key, value in fields.items() if value}
        operations.append({"value": 1, "fields": fields})
        if tokens > 0:
            token_operations.append({"value": tokens, "fields": fields})
        evidence.append(
            {
                "step": index,
                "reasoning": clean_frame(reasoning, 240),
                "action": clean_frame(action, 240),
                "url": clean_frame(step.get("url"), 160),
                "stack": [f"{key}:{value}" for key, value in fields.items()],
                "tokens": tokens,
                "visible_error": error_text,
                "repeated": repeated,
            }
        )

    return TraceSummary(
        label=label,
        goal=goal,
        operation_records=operations,
        token_records=token_operations,
        steps=len(steps),
        tokens=total_tokens,
        errors=errors,
        repeats=repeats,
        nonprogress=nonprogress,
        finished=finished,
        evidence=evidence,
    )


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def auc(labels: list[bool], scores: list[float]) -> float | None:
    positives = [score for label, score in zip(labels, scores) if label]
    negatives = [score for label, score in zip(labels, scores) if not label]
    if not positives or not negatives:
        return None
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            wins += float(positive > negative) + 0.5 * float(positive == negative)
    return wins / (len(positives) * len(negatives))


def paired_accuracy(pairs: list[tuple[TraceSummary, TraceSummary]], score: str) -> dict[str, Any]:
    wins = ties = losses = 0
    for bad, good in pairs:
        bad_score, good_score = bad.score(score), good.score(score)
        wins += int(bad_score > good_score)
        ties += int(bad_score == good_score)
        losses += int(bad_score < good_score)
    total = len(pairs)
    return {
        "pairs": total,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "accuracy_ties_half": (wins + 0.5 * ties) / total if total else None,
    }


def invoke_agentpprof(
    binary: Path,
    candidate: Path,
    base: Path,
    view: str,
    output: Path,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = agentpprof_command(binary, candidate, base, view, output)
    run = subprocess.run(command, check=False, capture_output=True, text=True)
    if run.returncode != 0:
        raise RuntimeError(f"AgentPProf failed: {' '.join(command)}\n{run.stderr}")
    status = json.loads(run.stdout)
    with gzip.open(output, "rb") as handle:
        if not handle.read(1):
            raise RuntimeError(f"empty pprof: {output}")
    readback = subprocess.run(
        ["go", "tool", "pprof", "-top", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    if readback.returncode != 0:
        raise RuntimeError(f"go tool pprof rejected {output}: {readback.stderr}")
    return status


def agentpprof_command(
    binary: Path,
    candidate: Path,
    base: Path,
    view: str,
    output: Path,
) -> list[str]:
    return [
        str(binary),
        "--operation-file", str(candidate),
        "--diff-base-operation-file", str(base),
        "--view", view,
        "--stack", STACK,
        "--deterministic-output",
        "--output", str(output),
    ]


def top_evidence(summary: TraceSummary, result_names: set[str], limit: int = 8) -> list[dict[str, Any]]:
    selected = []
    for row in summary.evidence:
        result = next((frame.split(":", 1)[1] for frame in row["stack"] if frame.startswith("result:")), "")
        if any(result.startswith(name) for name in result_names):
            selected.append(row)
    return sorted(selected, key=lambda row: (-row["tokens"], row["step"]))[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--agentpprof", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--case-only",
        action="store_true",
        help="Run only the fixed VisualWebArena 512 Qwen-bad/Claude-good preflight pair.",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Build the complete pair-occurrence aggregate without regenerating per-pair profiles.",
    )
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    binary = args.agentpprof.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    labels, coverage = load_labels(dataset_root)
    groups = eligible_groups(labels)
    if args.case_only:
        case_key = ("visualwebarena", "visualwebarena.512")
        values = groups.get(case_key, [])
        bad = next((label for label in values if not label.success and "Qwen" in label.model), None)
        good = next(
            (label for label in values if label.success and "claude" in label.model.lower()),
            None,
        )
        if bad is None or good is None:
            raise RuntimeError("fixed VisualWebArena 512 preflight pair is unavailable")
        groups = {case_key: [bad, good]}
    eligible = [label for values in groups.values() for label in values]
    summaries: dict[str, TraceSummary] = {}
    for number, label in enumerate(eligible, 1):
        summary = trace_to_summary(label)
        summaries[label.key] = summary
        trace_dir = out_dir / "traces" / label.key
        write_jsonl(trace_dir / "operations.jsonl", summary.operation_records)
        write_jsonl(trace_dir / "tokens.jsonl", summary.token_records)
        if number % 25 == 0 or number == len(eligible):
            print(f"materialized {number}/{len(eligible)} trajectories", flush=True)

    pairs: list[tuple[TraceSummary, TraceSummary]] = []
    pair_rows: list[dict[str, Any]] = []
    per_benchmark: dict[str, list[tuple[TraceSummary, TraceSummary]]] = defaultdict(list)
    profile_failures: list[dict[str, str]] = []
    profile_count = 0
    for (benchmark, task), values in sorted(groups.items()):
        bads = [summaries[label.key] for label in values if not label.success]
        goods = [summaries[label.key] for label in values if label.success]
        for bad in bads:
            for good in goods:
                pairs.append((bad, good))
                per_benchmark[benchmark].append((bad, good))
                pair_name = pair_slug(benchmark, task, bad.label, good.label)
                pair_dir = out_dir / "pairs" / pair_name
                statuses: dict[str, Any] = {}
                if not args.aggregate_only:
                    try:
                        for view in ("operations", "tokens"):
                            statuses[view] = invoke_agentpprof(
                                binary,
                                out_dir / "traces" / bad.label.key / f"{view}.jsonl",
                                out_dir / "traces" / good.label.key / f"{view}.jsonl",
                                view,
                                pair_dir / f"bad-minus-good-{view}.pb.gz",
                            )
                            profile_count += 1
                    except Exception as error:  # recorded and reported; never silently drop a pair
                        profile_failures.append({"pair": pair_name, "error": str(error)})
                pair_rows.append(
                    {
                        "benchmark": benchmark,
                        "canonical_task": task,
                        "bad": bad.label.key,
                        "good": good.label.key,
                        "scores": {
                            name: {"bad": bad.score(name), "good": good.score(name)}
                            for name in ("steps", "tokens", "error_rate", "repeat_rate", "nonprogress_rate")
                        },
                        "profiles": {
                            view: {
                                "path": str(pair_dir / f"bad-minus-good-{view}.pb.gz"),
                                "status": statuses.get(view),
                            }
                            for view in ("operations", "tokens")
                        },
                    }
                )
                if len(pair_rows) % 25 == 0:
                    print(f"profiled {len(pair_rows)} pairs", flush=True)

    aggregate_dir = out_dir / "aggregate"
    aggregate_candidate = aggregate_dir / "bad.operations.jsonl"
    aggregate_base = aggregate_dir / "good.operations.jsonl"
    aggregate_output = aggregate_dir / "bad-minus-good.operations.pb.gz"
    write_jsonl(
        aggregate_candidate,
        (record for bad, _ in pairs for record in bad.operation_records),
    )
    write_jsonl(
        aggregate_base,
        (record for _, good in pairs for record in good.operation_records),
    )
    aggregate_status = invoke_agentpprof(
        binary,
        aggregate_candidate,
        aggregate_base,
        "operations",
        aggregate_output,
    )
    profile_count += 1
    aggregate_command = agentpprof_command(
        binary,
        aggregate_candidate,
        aggregate_base,
        "operations",
        aggregate_output,
    )

    score_names = ("steps", "tokens", "error_rate", "repeat_rate", "nonprogress_rate")
    trajectory_rows = list(summaries.values())
    metrics = {
        name: {
            "pairwise": paired_accuracy(pairs, name),
            "unsuccessful_auc": auc(
                [not row.label.success for row in trajectory_rows],
                [row.score(name) for row in trajectory_rows],
            ),
        }
        for name in score_names
    }
    looping_rows = [row for row in trajectory_rows if row.label.looping is not None]
    looping_auc = auc(
        [bool(row.label.looping) for row in looping_rows],
        [row.score("repeat_rate") for row in looping_rows],
    )
    benchmark_metrics = {
        benchmark: {
            name: paired_accuracy(benchmark_pairs, name)
            for name in score_names
        }
        for benchmark, benchmark_pairs in sorted(per_benchmark.items())
    }

    case_key = ("visualwebarena", "visualwebarena.512")
    case_values = groups.get(case_key, [])
    case_bad = next(
        (summaries[label.key] for label in case_values if not label.success and "Qwen" in label.model),
        next((summaries[label.key] for label in case_values if not label.success), None),
    )
    case_good = next(
        (summaries[label.key] for label in case_values if label.success and "claude" in label.model.lower()),
        next((summaries[label.key] for label in case_values if label.success), None),
    )
    case = None
    if case_bad and case_good:
        case_pair_name = pair_slug(
            "visualwebarena", "visualwebarena.512", case_bad.label, case_good.label
        )
        case = {
            "benchmark": "visualwebarena",
            "canonical_task": "visualwebarena.512",
            "goal": case_bad.goal,
            "bad": {
                "source": str(case_bad.label.source),
                "model": case_bad.label.model,
                "steps": case_bad.steps,
                "tokens": case_bad.tokens,
                "errors": case_bad.errors,
                "repeats": case_bad.repeats,
                "nonprogress_rate": case_bad.score("nonprogress_rate"),
                "problem_evidence": top_evidence(case_bad, {"error", "repeated", "stopped"}),
            },
            "good": {
                "source": str(case_good.label.source),
                "model": case_good.label.model,
                "steps": case_good.steps,
                "tokens": case_good.tokens,
                "errors": case_good.errors,
                "repeats": case_good.repeats,
                "nonprogress_rate": case_good.score("nonprogress_rate"),
                "conclusion_evidence": top_evidence(case_good, {"conclusion"}),
            },
            "operation_pprof": str(out_dir / "pairs" / case_pair_name / "bad-minus-good-operations.pb.gz"),
            "token_pprof": str(out_dir / "pairs" / case_pair_name / "bad-minus-good-tokens.pb.gz"),
        }
        if args.aggregate_only:
            case["operation_pprof"] = None
            case["token_pprof"] = None

    result = {
        "schema_version": 1,
        "dataset": {
            "name": "McGill-NLP/agent-reward-bench",
            "revision": "b6d17e646009d6cb63d5dd7be78807b680693f61",
            **coverage,
        },
        "stack": STACK,
        "oracle_policy": "success and looping annotations are scorer-only",
        "eligible": {
            "canonical_mixed_tasks": len(groups),
            "trajectories": len(eligible),
            "bad_good_pairs": len(pairs),
            "by_benchmark": dict(Counter(key[0] for key in groups)),
        },
        "profiles": {
            "attempted": 1 if args.aggregate_only else len(pairs) * 2 + 1,
            "decoded_by_go_tool_pprof": profile_count,
            "failures": profile_failures,
        },
        "aggregate_profile": {
            "pair_occurrence_weighting": True,
            "bad_operation_occurrences": sum(bad.steps for bad, _ in pairs),
            "good_operation_occurrences": sum(good.steps for _, good in pairs),
            "candidate_input": str(aggregate_candidate),
            "base_input": str(aggregate_base),
            "output": str(aggregate_output),
            "command": aggregate_command,
            "status": aggregate_status,
        },
        "metrics": metrics,
        "looping_repeat_rate_auc": looping_auc,
        "looping_consensus_trajectories": len(looping_rows),
        "benchmark_pairwise": benchmark_metrics,
        "case_study": case,
    }
    (out_dir / "evaluation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "pairs.json").write_text(
        json.dumps(pair_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if profile_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
